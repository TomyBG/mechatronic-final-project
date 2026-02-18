import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QGroupBox, QScrollArea, QTextEdit
)
from PySide6.QtCore import Qt

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

try:
    from calculations.calculation_engine import IrrigationCalculator
except ImportError:
    IrrigationCalculator = None

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class ResultsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calculation Results")
        self.setGeometry(150, 150, 700, 950)
        
        if IrrigationCalculator:
            self.calculator = IrrigationCalculator()
        else:
            self.calculator = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        container = QWidget()
        scroll.setWidget(container)
        self.layout = QVBoxLayout(container)
        
        title = QLabel("📊 Hydraulic Calculation Results")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c5f2d;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # Graph
        group_g = QGroupBox("Pressure Distribution")
        group_g.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #2c5f2d; margin-top: 10px; }")
        vbox_g = QVBoxLayout()
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        vbox_g.addWidget(self.canvas)
        group_g.setLayout(vbox_g)
        self.layout.addWidget(group_g)

        # Data
        group_d = QGroupBox("Recommendations")
        group_d.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #2c5f2d; margin-top: 10px; }")
        self.results_label = QLabel("Waiting for data...")
        self.results_label.setWordWrap(True)
        self.planters_detail_text = QTextEdit()
        self.planters_detail_text.setReadOnly(True)
        self.planters_detail_text.setMaximumHeight(200)
        
        vbox_d = QVBoxLayout()
        vbox_d.addWidget(self.results_label)
        vbox_d.addWidget(QLabel("Planter Details:"))
        vbox_d.addWidget(self.planters_detail_text)
        group_d.setLayout(vbox_d)
        self.layout.addWidget(group_d)

    def perform_calculation(self, input_data):
        if not self.calculator:
            self.results_label.setText("Error: Engine missing")
            return

        length = input_data.get('length', 10)
        mode = input_data.get('mode', 'continuous')
        connectors = input_data.get('connectors', {})
        
        try:
            if mode == 'continuous':
                # Direct Soil mode now passes total_flow_lh directly
                res = self.calculator.calculate_continuous_soil(
                    length_m=length,
                    total_flow_lh=input_data.get('total_flow_lh', 0.0),
                    connectors=connectors
                )
            else:
                specific_flows = input_data.get('specific_flows', [])
                res = self.calculator.calculate_planters_scenario(
                    length_m=length,
                    num_planters=input_data.get('num_outlets', 5),
                    specific_flows_list=specific_flows,
                    connectors=connectors
                )
            
            self.update_report(res, mode)
            self.update_graph(res['graph_data'])
        except Exception as e:
            self.results_label.setText(f"Error: {e}")
            import traceback
            traceback.print_exc()

    def update_report(self, res, mode):
        html = f"""<h3>✅ Results</h3>
        <p><b>Range:</b> {res.get('range_classification')}</p>
        <p><b>Total Flow:</b> {res.get('total_flow_lh')} L/h</p>
        <hr>"""
        
        if mode == 'continuous':
            self.planters_detail_text.hide()
            html += f"<p><b>Main Pipe:</b> {res.get('recommended_pipe_mm')} mm (Direct Soil Mode)</p>"
        else:
            html += f"<p><b>Main Pipe:</b> {res.get('recommended_main_pipe_mm')} mm</p>"
            html += f"<p><b>Spaghetti:</b> {res.get('recommended_planter_pipe')}</p>"
            self.planters_detail_text.show()
            self.planters_detail_text.setText("\n".join(res.get('detailed_planters_list', [])))
            
        html += f"<hr><p style='color:red; font-size:14px'><b>REQUIRED INLET: {res.get('required_inlet_pressure_bar')} Bar</b></p>"
        
        # --- תוספת דיבאג הנדסי ---
        debug = res.get('debug_info', {})
        if debug:
            html += f"""
            <div style='background-color:#eee; padding:5px; margin-top:10px; font-size:11px; color:#555;'>
            <b>🔧 Engineering Data (First Segment):</b><br>
            • Velocity: {debug.get('velocity', 0):.3f} m/s<br>
            • Reynolds No: {int(debug.get('reynolds', 0))}<br>
            • Friction Factor (f): {debug.get('friction_f', 0):.4f}<br>
            • Segment Loss: {debug.get('segment_loss', 0):.4f} Bar<br>
            • Pipe ID used: {debug.get('internal_dia', 0)} mm
            </div>
            """
        # ------------------------
        
        self.results_label.setText(html)

    def update_graph(self, graph_data):
        x = graph_data['x']
        y = graph_data['y']
        self.canvas.axes.cla()
        self.canvas.axes.plot(x, y, 'o-', color='#2196F3')
        self.canvas.axes.axhline(y=1.0, color='red', linestyle='--')
        
        if y:
            min_y, max_y = min(y), max(y)
            margin = (max_y - min_y) * 0.1 if max_y != min_y else 0.5
            self.canvas.axes.set_ylim(min_y - margin, max_y + margin)
            
        self.canvas.axes.set_xlabel("Distance (m)")
        self.canvas.axes.set_ylabel("Pressure (Bar)")
        self.canvas.axes.grid(True, alpha=0.5)
        self.canvas.draw()