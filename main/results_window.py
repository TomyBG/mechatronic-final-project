import sys
import os
import csv
from datetime import datetime

# --- NEW IMPORT FOR PDF ---
from fpdf import FPDF

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

# --- PDF Class Helper ---
class PDFReport(FPDF):
    def header(self):
        # Set font
        self.set_font('Helvetica', 'B', 15)
        # Title
        self.set_text_color(44, 95, 45) # Dark Green #2c5f2d
        self.cell(0, 10, 'Irrigation System Design Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(240, 248, 240) # Light Green background
        self.set_text_color(44, 95, 45)
        self.cell(0, 8, f"  {label}", 0, 1, 'L', fill=True)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0)
        self.multi_cell(0, 6, body)
        self.ln()

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

        # --- EXPORT BUTTONS ---
        
        # CSV Button
        self.export_csv_btn = QPushButton("📂 Export Data to Excel (CSV)")
        self.export_csv_btn.setFixedHeight(45)
        self.export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                font-size: 14px;
                border-radius: 6px;
                margin-top: 15px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.layout.addWidget(self.export_csv_btn)
        
        # PDF Button
        self.export_pdf_btn = QPushButton("📄 Export Professional Report (PDF)")
        self.export_pdf_btn.setFixedHeight(45)
        self.export_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F; 
                color: white; 
                font-weight: bold; 
                font-size: 14px;
                border-radius: 6px;
                margin-top: 5px;
                margin-bottom: 20px;
            }
            QPushButton:hover { background-color: #B71C1C; }
        """)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.layout.addWidget(self.export_pdf_btn)

    def perform_calculation(self, input_data):
        if not self.calculator:
            self.results_label.setText("Error: Engine missing")
            return

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
        """Original CSV export function"""
        if not self.last_results or not self.last_inputs:
            QMessageBox.warning(self, "No Data", "Please run a calculation first.")
            return

        default_name = f"Irrigation_Plan_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Calculation Results", default_name, "CSV Files (*.csv)")

        if not file_path:
            return

        try:
            res = self.last_results
            inp = self.last_inputs
            connectors = inp.get('connectors', {})
            mode = inp.get('mode', 'continuous')
            
            pipe_size = res.get('recommended_pipe_mm') if mode == 'continuous' else res.get('recommended_main_pipe_mm')

            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["IRRIGATION SYSTEM CALCULATION REPORT"])
                writer.writerow(["Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow([])
                writer.writerow(["BILL OF MATERIALS (BOM)"])
                writer.writerow(["Item", "Quantity/Value", "Unit"])
                writer.writerow(["Main Pipe Diameter", pipe_size, "mm"])
                writer.writerow(["Total Length", inp.get('length'), "m"])
                
                if mode == 'planters':
                    writer.writerow(["Spaghetti Pipe", "As needed (per planter)", ""])
                    writer.writerow(["Number of Planters", inp.get('num_outlets'), "units"])
                
                writer.writerow(["Total System Flow", res.get('total_flow_lh'), "L/h"])
                writer.writerow(["Required Inlet Pressure", res.get('required_inlet_pressure_bar'), "Bar"])
                
                writer.writerow([])
                writer.writerow(["CONNECTORS LIST"])
                writer.writerow(["Elbows (90 deg)", connectors.get('elbows', 0), "units"])
                writer.writerow(["T-Connectors", connectors.get('tees', 0), "units"])
                writer.writerow(["Straight Connectors", connectors.get('straights', 0), "units"])
                
                writer.writerow([])
                writer.writerow(["HYDRAULIC DATA - PRESSURE DISTRIBUTION"])
                writer.writerow(["Distance from Source (m)", "Pressure (Bar)"])
                
                distances = res.get('graph_data', {}).get('x', [])
                pressures = res.get('graph_data', {}).get('y', [])
                
                for d, p in zip(distances, pressures):
                    writer.writerow([f"{d:.2f}", f"{p:.3f}"])
            
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save CSV:\n{str(e)}")

    def export_pdf(self):
        """Generates a styled PDF report"""
        if not self.last_results or not self.last_inputs:
            QMessageBox.warning(self, "No Data", "Please run a calculation first.")
            return

        # 1. Ask for file location
        default_name = f"Irrigation_Report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", default_name, "PDF Files (*.pdf)")

        if not file_path:
            return

        try:
            # 2. Generate temp graph image
            temp_img = os.path.join(root_dir, "temp_graph.png")
            self.canvas.figure.savefig(temp_img, dpi=150, bbox_inches='tight')

            # 3. Create PDF
            pdf = PDFReport()
            pdf.add_page()
            
            res = self.last_results
            inp = self.last_inputs
            connectors = inp.get('connectors', {})
            mode = inp.get('mode', 'continuous')
            
            # --- Project Info ---
            pdf.chapter_title("Project Overview")
            date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            info_text = (f"Date: {date_str}\n"
                         f"Garden Length: {inp.get('length')} m\n"
                         f"Irrigation Mode: {mode.replace('_', ' ').title()}\n"
                         f"Total Flow: {res.get('total_flow_lh')} L/h")
            pdf.chapter_body(info_text)

            # --- Recommendations ---
            pdf.chapter_title("System Recommendations")
            
            pipe_size = res.get('recommended_pipe_mm') if mode == 'continuous' else res.get('recommended_main_pipe_mm')
            
            rec_text = (f"Main Pipe Diameter: {pipe_size} mm\n"
                        f"Required Inlet Pressure: {res.get('required_inlet_pressure_bar')} Bar\n")
            
            if mode == 'planters':
                 rec_text += f"Secondary Pipe (Spaghetti): {res.get('recommended_planter_pipe')}\n"
                 
            pdf.chapter_body(rec_text)

            # --- Bill of Materials (Table) ---
            pdf.chapter_title("Bill of Materials (BOM)")
            
            # Table Header
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(100, 7, "Item", 1, 0, 'L', fill=True)
            pdf.cell(40, 7, "Quantity", 1, 1, 'C', fill=True)
            
            # Table Rows
            pdf.set_font('Helvetica', '', 10)
            
            items = [
                (f"Main Pipe ({pipe_size}mm)", f"{inp.get('length')} m"),
                ("Elbow Connectors (90)", str(connectors.get('elbows', 0))),
                ("T-Connectors", str(connectors.get('tees', 0))),
                ("Straight Connectors", str(connectors.get('straights', 0))),
            ]
            
            if mode == 'planters':
                 items.append(("Drippers / Outlets", str(inp.get('num_outlets'))))
            
            for name, qty in items:
                pdf.cell(100, 7, name, 1, 0, 'L')
                pdf.cell(40, 7, qty, 1, 1, 'C')
            
            pdf.ln(5)

            # --- Graph Image ---
            pdf.chapter_title("Hydraulic Analysis Graph")
            # Calculate width to center it
            pdf.image(temp_img, x=15, w=180)

            # 4. Save
            pdf.output(file_path)
            
            # 5. Cleanup and Open
            if os.path.exists(temp_img):
                os.remove(temp_img)
                
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

        except Exception as e:
            QMessageBox.critical(self, "PDF Export Error", f"Failed to generate PDF:\n{str(e)}")
            # Cleanup if failed
            if os.path.exists("temp_graph.png"):
                try: os.remove("temp_graph.png")
                except: pass