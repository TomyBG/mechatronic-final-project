from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QListWidget, QPushButton, QMessageBox
)

class SaveProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Project")
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Enter Project Name:")
        lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Garden_Front_Yard")
        layout.addWidget(self.name_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_project_name(self):
        return self.name_input.text().strip()


class LoadProjectDialog(QDialog):
    def __init__(self, projects_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Existing Project")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Select a Project to Load:")
        lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)
        
        self.list_widget = QListWidget()
        self.list_widget.addItems(projects_list)
        layout.addWidget(self.list_widget)
        
        load_btn = QPushButton("Load Selected Project")
        load_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        load_btn.clicked.connect(self.validate_selection)
        layout.addWidget(load_btn)

    def validate_selection(self):
        if not self.list_widget.currentItem():
            QMessageBox.warning(self, "No Selection", "Please select a project from the list.")
            return
        self.accept()

    def get_selected_project(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.text()
        return None