"""
Main Window - Home Screen
Displays three main options: About, New Project, Saved Projects
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel
)
from PySide6.QtCore import Qt
from about.about_window import AboutWindow
from main.new_project_window import NewProjectWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Garden Irrigation System Planning")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Garden Irrigation System Planning")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c5f2d;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Design your garden irrigation system")
        subtitle.setStyleSheet("font-size: 12px; color: #666666;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Spacing
        layout.addSpacing(30)
        
        # Button layout
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)
        
        # New Project button
        self.new_project_btn = QPushButton("📋 New Project")
        self.new_project_btn.setFixedHeight(60)
        self.new_project_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.new_project_btn.clicked.connect(self.open_new_project)
        buttons_layout.addWidget(self.new_project_btn)
        
        # Saved Projects button
        self.saved_projects_btn = QPushButton("💾 Saved Projects")
        self.saved_projects_btn.setFixedHeight(60)
        self.saved_projects_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.saved_projects_btn.clicked.connect(self.open_saved_projects)
        buttons_layout.addWidget(self.saved_projects_btn)
        
        # About button
        self.about_btn = QPushButton("ℹ️ About")
        self.about_btn.setFixedHeight(60)
        self.about_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        self.about_btn.clicked.connect(self.open_about)
        buttons_layout.addWidget(self.about_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        self.about_window = None
        self.new_project_window = None

    def open_new_project(self):
        """Open New Project window"""
        if self.new_project_window is None:
            self.new_project_window = NewProjectWindow(self)
        self.new_project_window.show()
        self.new_project_window.raise_()
        self.new_project_window.activateWindow()

    def open_saved_projects(self):
        """Open Saved Projects window"""
        print("Opening Saved Projects window...")
        # TODO: Implement Saved Projects window
        pass

    def open_about(self):
        """Open About window"""
        if self.about_window is None:
            self.about_window = AboutWindow(self)
        self.about_window.show()
        self.about_window.raise_()
        self.about_window.activateWindow()
