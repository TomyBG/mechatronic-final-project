import sys
import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QDoubleSpinBox, QSpinBox, 
    QPushButton, QRadioButton, QButtonGroup, QGroupBox, QScrollArea,
    QMessageBox, QDialog
)
from PySide6.QtCore import Qt
from main.results_window import ResultsWindow

from projects.dialogs import SaveProjectDialog
from projects.file_manager import ProjectFileManager

GROUPBOX_STYLE = """
    QGroupBox {
        font-weight: bold;
        color: white;
        border: 2px solid #2c5f2d;
        border-radius: 5px;
        padding-top: 10px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
        background-color: #2c5f2d;
        color: white;
        font-weight: bold;
    }
"""

class NewProjectWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setFixedSize(800, 700) 
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        self.file_manager = ProjectFileManager(root_dir)

        self.results_window = None
        self.water_inputs = [] 
        self.water_inputs_widgets = [] 
        self.realtime_enabled = False 

        self.scroll = QScrollArea(self)
        self.scroll.setGeometry(0, 0, 800, 700)
        self.scroll.setWidgetResizable(False) 
        self.setCentralWidget(self.scroll)
        
        self.container = QWidget()
        self.scroll.setWidget(self.container)
        
        self.title = QLabel("Create New Project", self.container)
        self.title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c5f2d;")
        
        self.length_group = QGroupBox("1. Garden Length", self.container)
        self.length_group.setStyleSheet(GROUPBOX_STYLE)
        
        self.length_label = QLabel("Total garden length:", self.length_group)
        self.length_label.setStyleSheet("font-weight: bold;")
        self.length_spinbox = QDoubleSpinBox(self.length_group)
        self.length_spinbox.setRange(0.01, 150.0)
        self.length_spinbox.setValue(10.0)
        self.length_spinbox.setDecimals(2)
        self.length_spinbox.setSingleStep(0.5)
        self.length_spinbox.setSuffix(" m")
        self.length_spinbox.valueChanged.connect(self.update_summary)
        self.length_spinbox.valueChanged.connect(self.auto_refresh_calculation) 
        
        self.outlets_group = QGroupBox("2. Choose Irrigation Type", self.container)
        self.outlets_group.setStyleSheet(GROUPBOX_STYLE)
        
        self.outlets_button_group = QButtonGroup(self)
        
        self.no_outlets_radio = QRadioButton("Direct Soil / No Planters", self.outlets_group)
        self.no_outlets_radio.setChecked(False)
        self.no_outlets_radio.toggled.connect(self.on_outlet_type_changed)
        self.no_outlets_radio.toggled.connect(self.auto_refresh_calculation) 
        self.outlets_button_group.addButton(self.no_outlets_radio)
        
        self.with_outlets_radio = QRadioButton("With Outlets (Planters):", self.outlets_group)
        self.with_outlets_radio.setChecked(True)
        self.with_outlets_radio.toggled.connect(self.on_outlet_type_changed)
        self.with_outlets_radio.toggled.connect(self.auto_refresh_calculation)
        self.outlets_button_group.addButton(self.with_outlets_radio)
        
        self.outlets_spinbox = QSpinBox(self.outlets_group)
        self.outlets_spinbox.setRange(1, 50)
        self.outlets_spinbox.setValue(5)
        self.outlets_spinbox.valueChanged.connect(self.on_num_outlets_changed)
        self.outlets_spinbox.valueChanged.connect(self.auto_refresh_calculation)
        
        self.set_all_label = QLabel("Set all outlets to (L/hour):", self.outlets_group)
        self.set_all_label.setStyleSheet("font-weight: bold;")
        self.set_all_flow_spinbox = QDoubleSpinBox(self.outlets_group)
        self.set_all_flow_spinbox.setRange(0.0, 10.0)
        self.set_all_flow_spinbox.setValue(2.0)
        self.set_all_flow_spinbox.setDecimals(2)
        self.set_all_flow_spinbox.setSingleStep(0.5)
        
        self.set_all_btn = QPushButton("Set All", self.outlets_group)
        self.set_all_btn.setStyleSheet("QPushButton { font-size: 11px; background-color: #2196F3; color: white; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #0b7dda; }")
        self.set_all_btn.clicked.connect(self.set_all_outlets_flow)
        
        self.direct_soil_group = QGroupBox("3. Dripper Selection (Direct Soil)", self.container)
        self.direct_soil_group.setStyleSheet(GROUPBOX_STYLE)
        
        self.ds_label_1 = QLabel("Dripper Type", self.direct_soil_group)
        self.ds_label_2 = QLabel("Quantity", self.direct_soil_group)
        
        self.dripper_qty_inputs = {} 
        self.dripper_labels = {}
        standard_drippers = [1.0, 2.0, 4.0, 8.0]
        
        for flow in standard_drippers:
            lbl = QLabel(f"{flow} L/h", self.direct_soil_group)
            lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
            spin = QSpinBox(self.direct_soil_group)
            spin.setRange(0, 500)
            spin.setValue(0)
            spin.valueChanged.connect(self.update_summary)
            spin.valueChanged.connect(self.auto_refresh_calculation)
            
            self.dripper_labels[str(flow)] = lbl
            self.dripper_qty_inputs[str(flow)] = spin
            
        self.direct_soil_group.hide()
        
        self.outlets_water_group = QGroupBox("3. Water Requirements (Per Outlet)", self.container)
        self.outlets_water_group.setStyleSheet(GROUPBOX_STYLE)
        
        self.connectors_group = QGroupBox("4. System Connectors for Main Line", self.container)
        self.connectors_group.setStyleSheet(GROUPBOX_STYLE)
        
        self.t_label = QLabel("T-Connectors:", self.connectors_group)
        self.t_label.setStyleSheet("font-weight: bold;")
        self.t_spinbox = QSpinBox(self.connectors_group)
        self.t_spinbox.setRange(0, 100)
        self.t_spinbox.valueChanged.connect(self.update_summary)
        self.t_spinbox.valueChanged.connect(self.auto_refresh_calculation)
        
        self.elbow_label = QLabel("Elbow Connectors (90°):", self.connectors_group)
        self.elbow_label.setStyleSheet("font-weight: bold;")
        self.elbow_spinbox = QSpinBox(self.connectors_group)
        self.elbow_spinbox.setRange(0, 100)
        self.elbow_spinbox.valueChanged.connect(self.update_summary)
        self.elbow_spinbox.valueChanged.connect(self.auto_refresh_calculation)
        
        self.straight_label = QLabel("Straight Connectors:", self.connectors_group)
        self.straight_label.setStyleSheet("font-weight: bold;")
        self.straight_spinbox = QSpinBox(self.connectors_group)
        self.straight_spinbox.setRange(0, 100)
        self.straight_spinbox.valueChanged.connect(self.update_summary)
        self.straight_spinbox.valueChanged.connect(self.auto_refresh_calculation)
        
        self.summary_title = QLabel("📊 Project Summary:", self.container)
        self.summary_title.setStyleSheet("font-weight: bold; font-size: 13px; color: white; background-color: #2c5f2d; padding: 8px; border-radius: 3px;")
        
        self.summary_label = QLabel(self.container)
        self.summary_label.setStyleSheet("background-color: #f0f8f0; color: #2c5f2d; padding: 15px; border-radius: 5px; border: 2px solid #2c5f2d; font-weight: bold;")
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.start_btn = QPushButton("🚀 START CALCULATION", self.container)
        self.start_btn.setStyleSheet("""
            QPushButton { font-size: 16px; background-color: #FF9800; color: white; border: none; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.start_btn.clicked.connect(self.on_start_clicked)
        
        self.save_btn = QPushButton("Save Project", self.container)
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; border-radius: 5px;")
        self.save_btn.clicked.connect(self.save_project)
        
        self.cancel_btn = QPushButton("Cancel", self.container)
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; border-radius: 5px;")
        self.cancel_btn.clicked.connect(self.close)
        
        self.on_outlet_type_changed()

    def _recalculate_positions(self):
        y = 30
        margin_x = 30
        group_w = 720 
        
        self.title.setGeometry(margin_x, y, group_w, 30)
        y += 50
        
        self.length_group.setGeometry(margin_x, y, group_w, 80)
        self.length_label.setGeometry(15, 30, 200, 30)
        self.length_spinbox.setGeometry(220, 30, 150, 30)
        y += 100
        
        self.outlets_group.setGeometry(margin_x, y, group_w, 160)
        self.no_outlets_radio.setGeometry(15, 30, 250, 30)
        self.with_outlets_radio.setGeometry(15, 70, 200, 30)
        self.outlets_spinbox.setGeometry(220, 70, 100, 30)
        
        if self.with_outlets_radio.isChecked():
            self.set_all_label.show()
            self.set_all_flow_spinbox.show()
            self.set_all_btn.show()
            self.set_all_label.setGeometry(15, 110, 200, 30)
            self.set_all_flow_spinbox.setGeometry(220, 110, 100, 30)
            self.set_all_btn.setGeometry(330, 110, 100, 30)
        else:
            self.set_all_label.hide()
            self.set_all_flow_spinbox.hide()
            self.set_all_btn.hide()
            
        y += 180
        
        if self.no_outlets_radio.isChecked():
            group3a_h = 50 + len(self.dripper_qty_inputs) * 40
            self.direct_soil_group.setGeometry(margin_x, y, group_w, group3a_h)
            self.ds_label_1.setGeometry(15, 25, 150, 30)
            self.ds_label_2.setGeometry(180, 25, 100, 30)
            
            dy = 60
            for flow, spin in self.dripper_qty_inputs.items():
                lbl = self.dripper_labels[flow]
                lbl.setGeometry(15, dy, 150, 30)
                spin.setGeometry(180, dy, 100, 30)
                dy += 40
            y += group3a_h + 20
        else:
            group3b_h = 40 + len(self.water_inputs_widgets) * 40
            if group3b_h < 80: group3b_h = 80
            self.outlets_water_group.setGeometry(margin_x, y, group_w, group3b_h)
            
            dy = 30
            for lbl, spin in self.water_inputs_widgets:
                lbl.setGeometry(15, dy, 150, 30)
                spin.setGeometry(180, dy, 100, 30)
                dy += 40
            y += group3b_h + 20
            
        self.connectors_group.setGeometry(margin_x, y, group_w, 160)
        self.t_label.setGeometry(15, 30, 200, 30)
        self.t_spinbox.setGeometry(220, 30, 100, 30)
        self.elbow_label.setGeometry(15, 70, 200, 30)
        self.elbow_spinbox.setGeometry(220, 70, 100, 30)
        self.straight_label.setGeometry(15, 110, 200, 30)
        self.straight_spinbox.setGeometry(220, 110, 100, 30)
        y += 180
        
        self.summary_title.setGeometry(margin_x, y, group_w, 30)
        y += 40
        
        # --- תיקון מקדם ביטחון: הגובה קפץ מ-180 ל-250 ---
        self.summary_label.setGeometry(margin_x, y, group_w, 250)
        y += 270 
        
        self.start_btn.setGeometry(margin_x, y, group_w, 50)
        y += 80
        
        btn_width = (group_w // 2) - 10
        self.save_btn.setGeometry(margin_x, y, btn_width, 40)
        self.cancel_btn.setGeometry(margin_x + btn_width + 20, y, btn_width, 40)
        y += 70 
        
        self.container.setFixedSize(780, y)

    def on_start_clicked(self):
        self.realtime_enabled = True
        if self.results_window is None:
            self.results_window = ResultsWindow(self)
        self.results_window.show()
        self.results_window.raise_()
        self.perform_calculation_logic()

    def auto_refresh_calculation(self):
        if self.realtime_enabled:
            if self.results_window and self.results_window.isVisible():
                self.perform_calculation_logic()

    def on_outlet_type_changed(self):
        if self.no_outlets_radio.isChecked():
            self.direct_soil_group.show()
            self.outlets_water_group.hide()
            self.water_inputs = [] 
        else:
            self.direct_soil_group.hide()
            self.outlets_water_group.show()
            self._rebuild_planters_ui()
            
        self.update_summary()
        self._recalculate_positions() 

    def _rebuild_planters_ui(self):
        for lbl, spin in self.water_inputs_widgets:
            lbl.setParent(None)
            lbl.deleteLater()
            spin.setParent(None)
            spin.deleteLater()
            
        self.water_inputs_widgets = []
        self.water_inputs = [] 
            
        num_outlets = self.outlets_spinbox.value()
        for i in range(num_outlets):
            lbl = QLabel(f"Outlet {i+1} (L/h):", self.outlets_water_group)
            spinbox = QDoubleSpinBox(self.outlets_water_group)
            spinbox.setRange(0.0, 10.0)
            spinbox.setValue(2.0)
            spinbox.setFixedWidth(100)
            spinbox.valueChanged.connect(self.update_summary)
            spinbox.valueChanged.connect(self.auto_refresh_calculation)
            
            lbl.show()
            spinbox.show()
            
            self.water_inputs_widgets.append((lbl, spinbox))
            self.water_inputs.append((f"outlet_{i+1}", spinbox))

        self._recalculate_positions() 

    def on_num_outlets_changed(self):
        if self.with_outlets_radio.isChecked():
            self._rebuild_planters_ui()
            self.update_summary()

    def set_all_outlets_flow(self):
        val = self.set_all_flow_spinbox.value()
        for _, spinbox in self.water_inputs:
            spinbox.setValue(val)
        self.update_summary()

    def update_summary(self):
        length = self.length_spinbox.value()
        text = f"📋 Summary:\nLength: {length:.2f}m\n"
        total_flow = 0.0
        
        if self.no_outlets_radio.isChecked():
            text += "Mode: Direct Soil (No Planters)\n"
            text += "Selected Drippers:\n"
            for flow, spinbox in self.dripper_qty_inputs.items():
                qty = spinbox.value()
                if qty > 0:
                    subtotal = qty * float(flow)
                    total_flow += subtotal
                    text += f"  - {qty} x {flow} L/h = {subtotal} L/h\n"
        else:
            if self.water_inputs: 
                total_flow = sum([s.value() for _, s in self.water_inputs])
            
        text += f"\nTotal Flow: {total_flow:.2f} L/h"
        if length > 0:
             text += f" ({total_flow/length:.2f} L/m avg)"
        self.summary_label.setText(text)

    def save_project(self):
        data = {
            "length": self.length_spinbox.value(),
            "connectors": {
                "t": self.t_spinbox.value(),
                "elbow": self.elbow_spinbox.value(),
                "straight": self.straight_spinbox.value()
            }
        }
        
        if self.no_outlets_radio.isChecked():
            data["mode"] = "direct_soil"
            drippers = {}
            for flow_key, spin in self.dripper_qty_inputs.items():
                drippers[flow_key] = spin.value()
            data["direct_soil_drippers"] = drippers
            data["planter_flows"] = []
        else:
            data["mode"] = "planters"
            data["num_outlets"] = self.outlets_spinbox.value()
            flows = []
            for _, spin in self.water_inputs:
                try:
                    flows.append(spin.value())
                except RuntimeError:
                    pass
            data["planter_flows"] = flows
            data["direct_soil_drippers"] = {}

        dialog = SaveProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_project_name()
            if not name:
                QMessageBox.warning(self, "Warning", "Project name cannot be empty.")
                return
            
            success, msg = self.file_manager.save_project(name, data)
            if success:
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.critical(self, "Error", f"Failed to save: {msg}")

    def populate_from_data(self, data):
        self.length_spinbox.blockSignals(True)
        self.outlets_spinbox.blockSignals(True)
        
        try:
            self.length_spinbox.setValue(data.get("length", 10.0))
            conns = data.get("connectors", {})
            self.t_spinbox.setValue(conns.get("t", 0))
            self.elbow_spinbox.setValue(conns.get("elbow", 0))
            self.straight_spinbox.setValue(conns.get("straight", 0))
            
            mode = data.get("mode", "planters")
            
            if mode == "direct_soil":
                self.no_outlets_radio.setChecked(True) 
                saved_drippers = data.get("direct_soil_drippers", {})
                for flow_key, qty in saved_drippers.items():
                    if flow_key in self.dripper_qty_inputs:
                        self.dripper_qty_inputs[flow_key].setValue(qty)
            else:
                self.with_outlets_radio.setChecked(True)
                num_outlets = data.get("num_outlets", 5)
                self.outlets_spinbox.setValue(num_outlets)
                self._rebuild_planters_ui() 
                saved_flows = data.get("planter_flows", [])
                for i, (_, spinbox) in enumerate(self.water_inputs):
                    if i < len(saved_flows):
                        spinbox.setValue(saved_flows[i])

        finally:
            self.length_spinbox.blockSignals(False)
            self.outlets_spinbox.blockSignals(False)
            self.update_summary()
            self._recalculate_positions()

    def perform_calculation_logic(self):
        connectors_data = {
            'elbows': self.elbow_spinbox.value(),
            'tees': self.t_spinbox.value(),
            'straights': self.straight_spinbox.value()
        }

        input_data = {
            'length': self.length_spinbox.value(),
            'connectors': connectors_data
        }
        
        if self.no_outlets_radio.isChecked():
            input_data['mode'] = 'continuous'
            total_flow = 0.0
            for flow, spinbox in self.dripper_qty_inputs.items():
                total_flow += (float(flow) * spinbox.value())
            input_data['total_flow_lh'] = total_flow
        else:
            input_data['mode'] = 'planters'
            input_data['num_outlets'] = self.outlets_spinbox.value()
            specific_flows = []
            for _, spinbox in self.water_inputs:
                try:
                    specific_flows.append(spinbox.value())
                except: pass
            input_data['specific_flows'] = specific_flows

        if self.results_window:
            self.results_window.perform_calculation(input_data)