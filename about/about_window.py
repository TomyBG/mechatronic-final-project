"""
About Window - Information about the application and developer
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QCursor, QDesktopServices
import webbrowser

class ClickableLabel(QLabel):
    """Clickable label that opens URLs smoothly using Qt framework"""
    def __init__(self, text, url, parent=None):
        super().__init__(text, parent)
        self.url = url
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("""
            QLabel {
                color: #0066CC;
                text-decoration: underline;
                font-weight: bold;
                font-size: 14px;
            }
            QLabel:hover {
                color: #0052A3;
            }
        """)
    
    def mousePressEvent(self, event):
        """Open URL on click gracefully"""
        QDesktopServices.openUrl(QUrl(self.url))
        super().mousePressEvent(event)


class AboutWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About - Garden Irrigation System Planning")
        self.setGeometry(200, 150, 600, 550)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setStyleSheet("background-color: #f5f5f5;")
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Title
        title = QLabel("Garden Irrigation System Planning")
        title.setGeometry(30, 20, 540, 50)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c5f2d;")
        title.setParent(central_widget)
        
        # Version
        version = QLabel("Version 1.0")
        version.setGeometry(30, 70, 540, 25)
        version.setStyleSheet("font-size: 14px; color: #555555;")
        version.setParent(central_widget)
        
        # Description Section
        desc_title = QLabel("About This Application:")
        desc_title.setGeometry(30, 105, 540, 25)
        desc_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #333333;")
        desc_title.setParent(central_widget)
        
        description = QLabel(
            "A professional tool for designing garden irrigation systems.\n\n"
            "Features:\n"
            "  • Hydraulic pressure calculations\n"
            "  • Component catalog management\n"
            "  • Project save/load functionality\n"
            "  • CSV and PDF export\n"
            "  • Real-time pressure visualization"
        )
        description.setGeometry(30, 135, 540, 150)
        description.setStyleSheet("font-size: 12px; color: #444444; line-height: 1.6;")
        description.setWordWrap(True)
        description.setParent(central_widget)
        
        # Developer Section
        dev_title = QLabel("Developer Information:")
        dev_title.setGeometry(30, 290, 540, 25)
        dev_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #333333;")
        dev_title.setParent(central_widget)
        
        # Developer name
        developer = QLabel("Tomer Baruch")
        developer.setGeometry(30, 320, 540, 30)
        developer.setStyleSheet("font-size: 14px; color: #2c5f2d; font-weight: bold;")
        developer.setParent(central_widget)
        
        # Email
        email_label = QLabel("Email:")
        email_label.setGeometry(30, 355, 540, 22)
        email_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #333333;")
        email_label.setParent(central_widget)
        
        email = ClickableLabel("tomer1246@gmail.com", "mailto:tomer1246@gmail.com")
        email.setGeometry(30, 377, 540, 25)
        email.setParent(central_widget)
        
        # LinkedIn
        linkedin_label = QLabel("LinkedIn:")
        linkedin_label.setGeometry(30, 410, 540, 22)
        linkedin_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #333333;")
        linkedin_label.setParent(central_widget)
        
        linkedin = ClickableLabel("www.linkedin.com/in/tomer-baruch-", "https://www.linkedin.com/in/tomer-baruch-")
        linkedin.setGeometry(30, 432, 540, 25)
        linkedin.setParent(central_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setGeometry(490, 480, 80, 40)
        close_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        close_btn.clicked.connect(self.close)
        close_btn.setParent(central_widget)