import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QLabel, QMessageBox, QDialog
)
from PySide6.QtCore import Qt

# Adjust imports based on your folder structure
from about.about_window import AboutWindow
from main.new_project_window import NewProjectWindow

# --- UPDATED IMPORTS ---
from projects.dialogs import LoadProjectDialog
from projects.file_manager import ProjectFileManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Garden Irrigation System Planning")
        
        # נעילת גודל החלון כדי שהמיקומים האבסולוטיים לא יישברו
        self.setFixedSize(600, 400)
        
        # Initialize File Manager
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        self.file_manager = ProjectFileManager(root_dir)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Title (X: 50, Y: 30, Width: 500, Height: 40)
        title = QLabel("Garden Irrigation System Planning", central_widget)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c5f2d;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setGeometry(50, 30, 500, 40)
        
        # Subtitle (X: 50, Y: 75, Width: 500, Height: 20)
        subtitle = QLabel("Design your garden irrigation system", central_widget)
        subtitle.setStyleSheet("font-size: 12px; color: #666666;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setGeometry(50, 75, 500, 20)
        
        # New Project button (X: 100, Y: 140, Width: 400, Height: 60)
        self.new_project_btn = QPushButton("📋 New Project", central_widget)
        self.new_project_btn.setStyleSheet("QPushButton { font-size: 14px; background-color: #4CAF50; color: white; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #45a049; }")
        self.new_project_btn.setGeometry(100, 140, 400, 60)
        self.new_project_btn.clicked.connect(self.open_new_project)
        
        # Saved Projects button (X: 100, Y: 220, Width: 400, Height: 60)
        self.saved_projects_btn = QPushButton("💾 Saved Projects", central_widget)
        self.saved_projects_btn.setStyleSheet("QPushButton { font-size: 14px; background-color: #2196F3; color: white; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #0b7dda; }")
        self.saved_projects_btn.setGeometry(100, 220, 400, 60)
        self.saved_projects_btn.clicked.connect(self.open_saved_projects)
        
        # About button (X: 100, Y: 300, Width: 400, Height: 60)
        self.about_btn = QPushButton("ℹ️ About", central_widget)
        self.about_btn.setStyleSheet("QPushButton { font-size: 14px; background-color: #FF9800; color: white; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #e68900; }")
        self.about_btn.setGeometry(100, 300, 400, 60)
        self.about_btn.clicked.connect(self.open_about)
        
        self.about_window = None
        self.new_project_window = None

    def open_new_project(self):
        """Open New Project window (Empty)"""
        self.new_project_window = NewProjectWindow(self)
        self.new_project_window.show()

    def open_saved_projects(self):
        projects = self.file_manager.get_existing_projects()
        
        if not projects:
            QMessageBox.information(self, "No Projects", "No saved projects found.")
            return

        dialog = LoadProjectDialog(projects, self)
        if dialog.exec() == QDialog.Accepted:
            selected_name = dialog.get_selected_project()
            if selected_name:
                data = self.file_manager.load_project(selected_name)
                if data:
                    self.new_project_window = NewProjectWindow(self)
                    self.new_project_window.populate_from_data(data)
                    self.new_project_window.setWindowTitle(f"Project: {selected_name}")
                    self.new_project_window.show()
                else:
                    QMessageBox.critical(self, "Error", "Failed to load project data.")

    def open_about(self):
        if self.about_window is None:
            self.about_window = AboutWindow(self)
        self.about_window.show()