import sys
import os
import csv
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QGroupBox, 
    QScrollArea, QTextEdit, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

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
            
        # משתנים לשמירת תוצאות החישוב האחרון עבור הייצוא
        self.last_results = None
        self.last_inputs = None

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

        # Graph Section
        group_g = QGroupBox("Pressure Distribution")
        group_g.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #2c5f2d; margin-top: 10px; }")
        vbox_g = QVBoxLayout()
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        vbox_g.addWidget(self.canvas)
        group_g.setLayout(vbox_g)
        self.layout.addWidget(group_g)

        # Recommendations Section
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

        # --- EXPORT BUTTON ---
        self.export_btn = QPushButton("📂 Export Results to Excel (CSV)")
        self.export_btn.setFixedHeight(50)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                font-size: 16px;
                border-radius: 8px;
                margin-top: 20px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.export_btn.clicked.connect(self.export_csv)
        self.layout.addWidget(self.export_btn)

    def perform_calculation(self, input_data):
        if not self.calculator:
            self.results_label.setText("Error: Engine missing")
            return

        # שמירת הקלט לשימוש בייצוא
        self.last_inputs = input_data
        
        length = input_data.get('length', 10)
        mode = input_data.get('mode', 'continuous')
        connectors = input_data.get('connectors', {})
        
        try:
            if mode == 'continuous':
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
            
            # שמירת התוצאות לשימוש בייצוא
            self.last_results = res
            
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
        
        # דיבאג
        debug = res.get('debug_info', {})
        if debug:
            html += f"""
            <div style='background-color:#eee; padding:5px; margin-top:10px; font-size:11px; color:#555;'>
            <b>🔧 Engineering Data (First Segment):</b><br>
            • Velocity: {debug.get('velocity', 0):.3f} m/s<br>
            • Reynolds No: {int(debug.get('reynolds', 0))}<br>
            • Friction Factor (f): {debug.get('friction_f', 0):.4f}<br>
            </div>
            """
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

    def export_csv(self):
        """Generates a CSV file with BOM and Pressure Data and opens it."""
        if not self.last_results or not self.last_inputs:
            QMessageBox.warning(self, "No Data", "Please run a calculation first.")
            return

        # 1. Ask user for file location
        default_name = f"Irrigation_Plan_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Calculation Results", default_name, "CSV Files (*.csv)")

        if not file_path:
            return

        try:
            res = self.last_results
            inp = self.last_inputs
            connectors = inp.get('connectors', {})
            mode = inp.get('mode', 'continuous')
            
            # Determine main pipe size string
            pipe_size = res.get('recommended_pipe_mm') if mode == 'continuous' else res.get('recommended_main_pipe_mm')

            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                
                # --- Header ---
                writer.writerow(["IRRIGATION SYSTEM CALCULATION REPORT"])
                writer.writerow(["Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow([])
                
                # --- BOM (Bill of Materials) ---
                writer.writerow(["BILL OF MATERIALS (BOM)"])
                writer.writerow(["Item", "Quantity/Value", "Unit"])
                
                writer.writerow(["Main Pipe Diameter", pipe_size, "mm"])
                writer.writerow(["Total Length", inp.get('length'), "m"])
                
                if mode == 'planters':
                    writer.writerow(["Spaghetti Pipe", "As needed (per planter)", ""])
                    writer.writerow(["Number of Planters", inp.get('num_outlets'), "units"])
                
                writer.writerow(["Total System Flow", res.get('total_flow_lh'), "L/h"])
                writer.writerow(["Required Inlet Pressure", res.get('required_inlet_pressure_bar'), "Bar"])
                
                # Connectors BOM
                writer.writerow([])
                writer.writerow(["CONNECTORS LIST"])
                writer.writerow(["Elbows (90 deg)", connectors.get('elbows', 0), "units"])
                writer.writerow(["T-Connectors", connectors.get('tees', 0), "units"])
                writer.writerow(["Straight Connectors", connectors.get('straights', 0), "units"])
                
                # --- Pressure Data Table ---
                writer.writerow([])
                writer.writerow(["HYDRAULIC DATA - PRESSURE DISTRIBUTION"])
                writer.writerow(["Distance from Source (m)", "Pressure (Bar)"])
                
                # Extract graph data for the table
                distances = res.get('graph_data', {}).get('x', [])
                pressures = res.get('graph_data', {}).get('y', [])
                
                for d, p in zip(distances, pressures):
                    writer.writerow([f"{d:.2f}", f"{p:.3f}"])
            
            # 2. Open the file automatically
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save file:\n{str(e)}")