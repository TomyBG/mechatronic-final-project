import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
from main.results_window import ResultsWindow


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
        self.setGeometry(100, 100, 800, 950)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self.results_window = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        
        container = QWidget()
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Create New Project")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c5f2d;")
        main_layout.addWidget(title)
        
        # SECTION 1: Length
        length_group = QGroupBox("1. Garden Length")
        length_group.setStyleSheet(GROUPBOX_STYLE)
        length_layout = QHBoxLayout()
        length_layout.setSpacing(15)
        length_layout.setContentsMargins(15, 15, 15, 15)
        
        length_label = QLabel("Total garden length:")
        length_label.setStyleSheet("font-weight: bold;")
        self.length_spinbox = QDoubleSpinBox()
        self.length_spinbox.setRange(0.01, 150.0)
        self.length_spinbox.setValue(10.0)
        self.length_spinbox.setDecimals(2)
        self.length_spinbox.setSingleStep(0.5)
        self.length_spinbox.setSuffix(" m")
        self.length_spinbox.setFixedWidth(150)
        self.length_spinbox.valueChanged.connect(self.update_summary)
        
        length_layout.addWidget(length_label)
        length_layout.addWidget(self.length_spinbox)
        length_layout.addStretch()
        length_group.setLayout(length_layout)
        main_layout.addWidget(length_group)
        
        # SECTION 2: Outlets / Irrigation Type
        outlets_group = QGroupBox("2. Choose Irrigation Type")
        outlets_group.setStyleSheet(GROUPBOX_STYLE)
        outlets_layout = QVBoxLayout()
        outlets_layout.setSpacing(10)
        outlets_layout.setContentsMargins(15, 15, 15, 15)
        
        self.outlets_button_group = QButtonGroup()
        
        self.no_outlets_radio = QRadioButton("Direct Soil / No Planters")
        self.no_outlets_radio.setChecked(False)
        self.no_outlets_radio.toggled.connect(self.on_outlet_type_changed)
        self.outlets_button_group.addButton(self.no_outlets_radio)
        outlets_layout.addWidget(self.no_outlets_radio)
        
        outlets_with_num_layout = QHBoxLayout()
        self.with_outlets_radio = QRadioButton("With Outlets (Planters):")
        self.with_outlets_radio.setChecked(True)
        self.with_outlets_radio.toggled.connect(self.on_outlet_type_changed)
        self.outlets_button_group.addButton(self.with_outlets_radio)
        
        self.outlets_spinbox = QSpinBox()
        self.outlets_spinbox.setRange(1, 50)
        self.outlets_spinbox.setValue(5)
        self.outlets_spinbox.setFixedWidth(100)
        self.outlets_spinbox.valueChanged.connect(self.on_num_outlets_changed)
        
        outlets_with_num_layout.addWidget(self.with_outlets_radio)
        outlets_with_num_layout.addWidget(self.outlets_spinbox)
        outlets_with_num_layout.addStretch()
        outlets_layout.addLayout(outlets_with_num_layout)
        
        # Set all helper (Only visible for Planters mode)
        self.set_all_widget = QWidget()
        set_all_layout = QHBoxLayout(self.set_all_widget)
        set_all_layout.setContentsMargins(0, 0, 0, 0)
        
        set_all_label = QLabel("Set all outlets to (L/hour):")
        set_all_label.setStyleSheet("font-weight: bold;")
        self.set_all_flow_spinbox = QDoubleSpinBox()
        self.set_all_flow_spinbox.setRange(0.0, 10.0)
        self.set_all_flow_spinbox.setValue(2.0)
        self.set_all_flow_spinbox.setDecimals(2)
        self.set_all_flow_spinbox.setSingleStep(0.5)
        self.set_all_flow_spinbox.setFixedWidth(100)
        
        set_all_btn = QPushButton("Set All")
        set_all_btn.setFixedWidth(100)
        set_all_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        set_all_btn.clicked.connect(self.set_all_outlets_flow)
        
        set_all_layout.addWidget(set_all_label)
        set_all_layout.addWidget(self.set_all_flow_spinbox)
        set_all_layout.addWidget(set_all_btn)
        set_all_layout.addStretch()
        
        outlets_layout.addWidget(self.set_all_widget)
        
        outlets_group.setLayout(outlets_layout)
        main_layout.addWidget(outlets_group)
        
        # SECTION 3A: Direct Soil - Dripper Selection
        self.direct_soil_group = QGroupBox("3. Dripper Selection (Direct Soil)")
        self.direct_soil_group.setStyleSheet(GROUPBOX_STYLE)
        
        # Using Grid Layout for the drippers table
        self.direct_soil_layout = QGridLayout()
        self.direct_soil_layout.setSpacing(10)
        self.direct_soil_layout.setContentsMargins(15, 15, 15, 15)
        
        # Headers
        self.direct_soil_layout.addWidget(QLabel("Dripper Type"), 0, 0)
        self.direct_soil_layout.addWidget(QLabel("Quantity"), 0, 1)
        
        # Store references to spinboxes
        self.dripper_qty_inputs = {} 
        standard_drippers = [1.0, 2.0, 4.0, 8.0]
        
        for i, flow in enumerate(standard_drippers):
            label = QLabel(f"{flow} L/h")
            label.setStyleSheet("font-weight: bold; font-size: 14px;")
            
            spinbox = QSpinBox()
            spinbox.setRange(0, 500) # Allow up to 500 drippers
            spinbox.setValue(0)
            spinbox.setFixedWidth(100)
            spinbox.valueChanged.connect(self.update_summary)
            
            self.dripper_qty_inputs[flow] = spinbox
            
            self.direct_soil_layout.addWidget(label, i+1, 0)
            self.direct_soil_layout.addWidget(spinbox, i+1, 1)

        # Add a stretch to keep it tight
        self.direct_soil_layout.setRowStretch(len(standard_drippers)+1, 1)
        
        self.direct_soil_group.setLayout(self.direct_soil_layout)
        self.direct_soil_group.hide()
        main_layout.addWidget(self.direct_soil_group)
        
        # SECTION 3B: Planters - Outlets Water
        self.outlets_water_group = QGroupBox("3. Water Requirements (Per Outlet)")
        self.outlets_water_group.setStyleSheet(GROUPBOX_STYLE)
        self.outlets_water_layout = QVBoxLayout()
        self.outlets_water_layout.setSpacing(12)
        self.outlets_water_layout.setContentsMargins(15, 15, 15, 15)
        self.outlets_water_group.setLayout(self.outlets_water_layout)
        main_layout.addWidget(self.outlets_water_group)
        
        # SECTION 4: Connectors
        connectors_group = QGroupBox("4. System Connectors for Main Line")
        connectors_group.setStyleSheet(GROUPBOX_STYLE)
        connectors_layout = QVBoxLayout()
        connectors_layout.setSpacing(12)
        connectors_layout.setContentsMargins(15, 15, 15, 15)
        
        t_layout = QHBoxLayout()
        t_label = QLabel("T-Connectors:")
        t_label.setStyleSheet("font-weight: bold;")
        self.t_spinbox = QSpinBox()
        self.t_spinbox.setRange(0, 100)
        self.t_spinbox.setFixedWidth(100)
        self.t_spinbox.valueChanged.connect(self.update_summary)
        t_layout.addWidget(t_label)
        t_layout.addWidget(self.t_spinbox)
        t_layout.addStretch()
        connectors_layout.addLayout(t_layout)
        
        elbow_layout = QHBoxLayout()
        elbow_label = QLabel("Elbow Connectors (90°):")
        elbow_label.setStyleSheet("font-weight: bold;")
        self.elbow_spinbox = QSpinBox()
        self.elbow_spinbox.setRange(0, 100)
        self.elbow_spinbox.setFixedWidth(100)
        self.elbow_spinbox.valueChanged.connect(self.update_summary)
        elbow_layout.addWidget(elbow_label)
        elbow_layout.addWidget(self.elbow_spinbox)
        elbow_layout.addStretch()
        connectors_layout.addLayout(elbow_layout)
        
        straight_layout = QHBoxLayout()
        straight_label = QLabel("Straight Connectors:")
        straight_label.setStyleSheet("font-weight: bold;")
        self.straight_spinbox = QSpinBox()
        self.straight_spinbox.setRange(0, 100)
        self.straight_spinbox.setFixedWidth(100)
        self.straight_spinbox.valueChanged.connect(self.update_summary)
        straight_layout.addWidget(straight_label)
        straight_layout.addWidget(self.straight_spinbox)
        straight_layout.addStretch()
        connectors_layout.addLayout(straight_layout)
        
        connectors_group.setLayout(connectors_layout)
        main_layout.addWidget(connectors_group)
        
        # SUMMARY
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("background-color: #f0f8f0; color: #2c5f2d; padding: 15px; border-radius: 5px; border: 2px solid #2c5f2d; font-weight: bold;")
        self.summary_label.setWordWrap(True)
        self.summary_label.setMinimumHeight(150)
        
        summary_title = QLabel("📊 Project Summary:")
        summary_title.setStyleSheet("font-weight: bold; font-size: 13px; color: white; background-color: #2c5f2d; padding: 8px; border-radius: 3px;")
        main_layout.addWidget(summary_title)
        main_layout.addWidget(self.summary_label)
        
        # START BUTTON
        self.start_btn = QPushButton("🚀 START CALCULATION")
        self.start_btn.setFixedHeight(50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.start_btn.clicked.connect(self.open_results_window)
        main_layout.addWidget(self.start_btn)
        
        # FOOTER
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save Project")
        save_btn.setFixedHeight(40)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; border-radius: 5px;")
        save_btn.clicked.connect(self.save_project)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; border-radius: 5px;")
        cancel_btn.clicked.connect(self.close)
        buttons_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(buttons_layout)
        
        self.water_inputs = []
        self.on_outlet_type_changed()

    def on_outlet_type_changed(self):
        # Clear existing dynamic inputs list
        self.water_inputs = []
        
        if self.no_outlets_radio.isChecked():
            # Mode: Direct Soil
            self.direct_soil_group.show()
            self.outlets_water_group.hide()
            self.set_all_widget.hide()
        else:
            # Mode: Planters
            self.direct_soil_group.hide()
            self.outlets_water_group.show()
            self.set_all_widget.show()
            
            # Rebuild planters input
            self._rebuild_planters_ui()
            
        self.update_summary()

    def _rebuild_planters_ui(self):
        # Clear layout
        while self.outlets_water_layout.count() > 0:
            item = self.outlets_water_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    child_item = item.layout().takeAt(0)
                    if child_item.widget(): child_item.widget().deleteLater()
            elif item.widget(): item.widget().deleteLater()
            
        num_outlets = self.outlets_spinbox.value()
        for i in range(num_outlets):
            layout = QHBoxLayout()
            label = QLabel(f"Outlet {i+1} (L/h):")
            spinbox = QDoubleSpinBox()
            spinbox.setRange(0.0, 10.0)
            spinbox.setValue(2.0)
            spinbox.setFixedWidth(100)
            spinbox.valueChanged.connect(self.update_summary)
            
            layout.addWidget(label)
            layout.addWidget(spinbox)
            layout.addStretch()
            self.outlets_water_layout.addLayout(layout)
            self.water_inputs.append((f"outlet_{i+1}", spinbox))

    def on_num_outlets_changed(self):
        if self.with_outlets_radio.isChecked():
            self._rebuild_planters_ui()
            self.update_summary()

    def set_all_outlets_flow(self):
        val = self.set_all_flow_spinbox.value()
        for label, spinbox in self.water_inputs:
            spinbox.setValue(val)
        self.update_summary()

    def update_summary(self):
        length = self.length_spinbox.value()
        text = f"📋 Summary:\nLength: {length:.2f}m\n"
        
        total_flow = 0.0
        
        if self.no_outlets_radio.isChecked():
            # Calculate from Dripper Quantities
            text += "Mode: Direct Soil (No Planters)\n"
            text += "Selected Drippers:\n"
            for flow, spinbox in self.dripper_qty_inputs.items():
                qty = spinbox.value()
                if qty > 0:
                    subtotal = qty * flow
                    total_flow += subtotal
                    text += f"  - {qty} x {flow} L/h = {subtotal} L/h\n"
        else:
            # Calculate from Planters inputs
            total_flow = sum([s.value() for _, s in self.water_inputs])
            
        text += f"\nTotal Flow: {total_flow:.2f} L/h"
        if length > 0:
             text += f" ({total_flow/length:.2f} L/m avg)"
             
        self.summary_label.setText(text)

    def save_project(self):
        self.close()

    def open_results_window(self):
        if self.results_window is None:
            self.results_window = ResultsWindow(self)
        self.results_window.show()
        self.results_window.raise_()
        
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
            # Mode: Direct Soil (Continuous)
            input_data['mode'] = 'continuous'
            
            # Calculate total flow from drippers
            total_flow = 0.0
            for flow, spinbox in self.dripper_qty_inputs.items():
                total_flow += (flow * spinbox.value())
            
            input_data['total_flow_lh'] = total_flow
            
        else:
            # Mode: Planters
            input_data['mode'] = 'planters'
            input_data['num_outlets'] = self.outlets_spinbox.value()
            
            specific_flows = []
            for label, spinbox in self.water_inputs:
                specific_flows.append(spinbox.value())
            
            input_data['specific_flows'] = specific_flows

        self.results_window.perform_calculation(input_data)