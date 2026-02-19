from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QDialogButtonBox, 
    QListWidget, QPushButton, QMessageBox
)

class SaveProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Project")
        # גודל חלון קבוע
        self.setFixedSize(400, 150)
        
        # כותרת
        lbl = QLabel("Enter Project Name:", self)
        lbl.setStyleSheet("font-weight: bold;")
        lbl.setGeometry(20, 20, 360, 20)
        
        # שורת קלט
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("e.g., Garden_Front_Yard")
        self.name_input.setGeometry(20, 50, 360, 30)
        
        # כפתורי שמירה/ביטול מובנים של Qt
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setGeometry(20, 100, 360, 30)

    def get_project_name(self):
        return self.name_input.text().strip()


class LoadProjectDialog(QDialog):
    def __init__(self, projects_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Existing Project")
        # גודל חלון קבוע
        self.setFixedSize(400, 500)
        
        # כותרת
        lbl = QLabel("Select a Project to Load:", self)
        lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        lbl.setGeometry(20, 20, 360, 20)
        
        # רשימת הפרויקטים לבחירה
        self.list_widget = QListWidget(self)
        self.list_widget.addItems(projects_list)
        # גובה 380, כדי שיישאר בדיוק מקום לכפתור למטה
        self.list_widget.setGeometry(20, 50, 360, 380) 
        
        # כפתור טעינה
        load_btn = QPushButton("Load Selected Project", self)
        load_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
        load_btn.clicked.connect(self.validate_selection)
        load_btn.setGeometry(20, 440, 360, 40)

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