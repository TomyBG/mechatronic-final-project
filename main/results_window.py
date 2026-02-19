import sys
import os
import csv
from datetime import datetime

from fpdf import FPDF

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QGroupBox, 
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

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(44, 95, 45)
        self.cell(0, 10, 'Irrigation System Design Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(240, 248, 240) 
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
        if parent is not None:
            self.setParent(parent)

class ResultsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calculation Results")
        self.setFixedSize(700, 700) 
        
        if IrrigationCalculator:
            self.calculator = IrrigationCalculator()
        else:
            self.calculator = None
            
        self.last_results = None
        self.last_inputs = None

        self.scroll = QScrollArea(self)
        self.scroll.setGeometry(0, 0, 700, 700)
        self.scroll.setWidgetResizable(False) 
        self.setCentralWidget(self.scroll)
        
        self.container = QWidget()
        self.scroll.setWidget(self.container)
        
        self.title = QLabel("📊 Hydraulic Calculation Results", self.container)
        self.title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c5f2d;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.group_g = QGroupBox("Pressure Distribution", self.container)
        self.group_g.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #2c5f2d; margin-top: 10px; }")
        
        self.canvas = MplCanvas(self.group_g, width=5, height=4, dpi=100)

        self.group_d = QGroupBox("Recommendations", self.container)
        self.group_d.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #2c5f2d; margin-top: 10px; }")
        
        self.results_label = QLabel("Waiting for data...", self.group_d)
        self.results_label.setWordWrap(True)
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.planters_label = QLabel("Planter Details:", self.group_d)
        self.planters_label.setStyleSheet("font-weight: bold;")
        
        self.planters_detail_text = QTextEdit(self.group_d)
        self.planters_detail_text.setReadOnly(True)

        self.export_csv_btn = QPushButton("📂 Export Data to Excel (CSV)", self.container)
        self.export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.export_csv_btn.clicked.connect(self.export_csv)
        
        self.export_pdf_btn = QPushButton("📄 Export Professional Report (PDF)", self.container)
        self.export_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F; color: white; font-weight: bold; font-size: 14px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #B71C1C; }
        """)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        
        self._recalculate_positions(mode='continuous')

    def _recalculate_positions(self, mode):
        margin_x = 20
        group_w = 640
        y = 20
        
        self.title.setGeometry(margin_x, y, group_w, 30)
        y += 50
        
        # --- Graph ---
        group_g_height = 450
        self.group_g.setGeometry(margin_x, y, group_w, group_g_height)
        self.canvas.setGeometry(10, 30, group_w - 20, group_g_height - 40)
        self.canvas.show()
        y += group_g_height + 20
        
        # --- מנגנון גובה דינמי לטקסט ---
        # מכריחים את הטקסט לקבל רוחב קבוע כדי שיידע מתי לשבור שורה
        self.results_label.setFixedWidth(group_w - 30)
        # מכריחים את התיבה להתאים את הגובה שלה לכמות הטקסט (כולל הטקסט האדום!)
        self.results_label.adjustSize()
        results_label_height = self.results_label.height()
        
        # נוודא שתמיד יש מינימום שטח כדי שלא ייראה צפוף מדי
        if results_label_height < 100:
            results_label_height = 100
            
        if mode == 'continuous':
            self.planters_label.hide()
            self.planters_detail_text.hide()
            group_d_height = results_label_height + 50 # מקדם ביטחון של 50 פיקסלים בתוך התיבה
            self.group_d.setGeometry(margin_x, y, group_w, group_d_height)
            self.results_label.setGeometry(15, 30, group_w - 30, results_label_height)
            y += group_d_height + 30
        else:
            self.planters_label.show()
            self.planters_detail_text.show()
            planters_text_height = 150
            group_d_height = results_label_height + planters_text_height + 70
            
            self.group_d.setGeometry(margin_x, y, group_w, group_d_height)
            self.results_label.setGeometry(15, 30, group_w - 30, results_label_height)
            
            current_group_y = 30 + results_label_height + 10
            self.planters_label.setGeometry(15, current_group_y, group_w - 30, 20)
            
            current_group_y += 25
            self.planters_detail_text.setGeometry(15, current_group_y, group_w - 30, planters_text_height)
            
            y += group_d_height + 30
            
        self.export_csv_btn.setGeometry(margin_x, y, group_w, 45)
        y += 60
        self.export_pdf_btn.setGeometry(margin_x, y, group_w, 45)
        y += 65 
        
        self.container.setFixedSize(680, y)

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
            
            # --- מחשבים מחדש את המיקומים אחרי שהטקסט עודכן! ---
            self._recalculate_positions(mode)
            
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
            html += f"<p><b>Main Pipe:</b> {res.get('recommended_pipe_mm')} mm (Direct Soil Mode)</p>"
        else:
            html += f"<p><b>Main Pipe:</b> {res.get('recommended_main_pipe_mm')} mm</p>"
            html += f"<p><b>Spaghetti:</b> {res.get('recommended_planter_pipe')}</p>"
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
        
        # מעדכנים את הטקסט ומכריחים את הקופסה להסתדר עליו
        self.results_label.setText(html)
        self.results_label.adjustSize()

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
        if not self.last_results or not self.last_inputs:
            QMessageBox.warning(self, "No Data", "Please run a calculation first.")
            return

        default_name = f"Irrigation_Report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", default_name, "PDF Files (*.pdf)")

        if not file_path:
            return

        try:
            temp_img = os.path.join(root_dir, "temp_graph.png")
            self.canvas.figure.savefig(temp_img, dpi=150, bbox_inches='tight')

            pdf = PDFReport()
            pdf.add_page()
            
            res = self.last_results
            inp = self.last_inputs
            connectors = inp.get('connectors', {})
            mode = inp.get('mode', 'continuous')
            
            pdf.chapter_title("Project Overview")
            date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            info_text = (f"Date: {date_str}\n"
                         f"Garden Length: {inp.get('length')} m\n"
                         f"Irrigation Mode: {mode.replace('_', ' ').title()}\n"
                         f"Total Flow: {res.get('total_flow_lh')} L/h")
            pdf.chapter_body(info_text)

            pdf.chapter_title("System Recommendations")
            
            pipe_size = res.get('recommended_pipe_mm') if mode == 'continuous' else res.get('recommended_main_pipe_mm')
            
            rec_text = (f"Main Pipe Diameter: {pipe_size} mm\n"
                        f"Required Inlet Pressure: {res.get('required_inlet_pressure_bar')} Bar\n")
            
            if mode == 'planters':
                 rec_text += f"Secondary Pipe (Spaghetti): {res.get('recommended_planter_pipe')}\n"
                 
            pdf.chapter_body(rec_text)

            pdf.chapter_title("Bill of Materials (BOM)")
            
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(100, 7, "Item", 1, 0, 'L', fill=True)
            pdf.cell(40, 7, "Quantity", 1, 1, 'C', fill=True)
            
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

            pdf.chapter_title("Hydraulic Analysis Graph")
            pdf.image(temp_img, x=15, w=180)

            pdf.output(file_path)
            
            if os.path.exists(temp_img):
                os.remove(temp_img)
                
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

        except Exception as e:
            QMessageBox.critical(self, "PDF Export Error", f"Failed to generate PDF:\n{str(e)}")
            if os.path.exists("temp_graph.png"):
                try: os.remove("temp_graph.png")
                except: pass