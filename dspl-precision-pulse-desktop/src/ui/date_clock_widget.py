"""
Interactive date and clock widget for dashboard
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont


class DateClockWidget(QWidget):
    """Interactive date and clock widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """Setup widget UI"""
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Time label
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 48px;
                font-weight: 700;
                background: transparent;
                font-family: 'Courier New', monospace;
            }
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        
        # Date label
        self.date_label = QLabel()
        self.date_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 16px;
                font-weight: 500;
                background: transparent;
            }
        """)
        self.date_label.setAlignment(Qt.AlignCenter)
        
        # Day label
        self.day_label = QLabel()
        self.day_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 14px;
                font-weight: 400;
                background: transparent;
            }
        """)
        self.day_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        layout.addWidget(self.day_label)
        
        self.update_time()
    
    def setup_timer(self):
        """Setup timer to update time every second"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
    
    def update_time(self):
        """Update time and date display"""
        now = QDateTime.currentDateTime()
        
        # Format time as HH:MM:SS
        time_str = now.toString("hh:mm:ss")
        self.time_label.setText(time_str)
        
        # Format date as MMMM DD, YYYY
        date_str = now.toString("MMMM dd, yyyy")
        self.date_label.setText(date_str)
        
        # Format day
        day_str = now.toString("dddd")
        self.day_label.setText(day_str)
    
    def closeEvent(self, event):
        """Stop timer on close"""
        self.timer.stop()
        event.accept()
