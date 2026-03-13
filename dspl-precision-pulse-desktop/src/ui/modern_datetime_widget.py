"""
Elegant date and time widget matching modern design with seconds
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont, QColor


class ModernDateTimeWidget(QWidget):
    """Modern date and time widget with gradient background"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(90)
        self.setMaximumHeight(90)
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """Setup widget UI"""
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 24px;
                padding: 16px;
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 12, 24, 12)
        main_layout.setSpacing(32)
        
        # Left side - Date and Day
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Day label
        self.day_label = QLabel()
        self.day_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: 600;
                background: rgba(255, 255, 255, 0.2);
                padding: 5px 10px;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.day_label.setAlignment(Qt.AlignCenter)
        
        # Date label
        self.date_label = QLabel()
        self.date_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: 700;
                background: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.date_label.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(self.day_label)
        left_layout.addWidget(self.date_label)
        
        # Center - Time with seconds
        center_layout = QVBoxLayout()
        center_layout.setSpacing(0)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Time container
        time_container_layout = QHBoxLayout()
        time_container_layout.setSpacing(2)
        time_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: 700;
                background: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        
        self.period_label = QLabel()
        self.period_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.period_label.setAlignment(Qt.AlignBottom)
        
        time_container_layout.addWidget(self.time_label)
        time_container_layout.addWidget(self.period_label)
        
        self.seconds_label = QLabel()
        self.seconds_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.seconds_label.setAlignment(Qt.AlignCenter)
        
        center_layout.addLayout(time_container_layout)
        center_layout.addWidget(self.seconds_label)
        
        # Right side - Empty for balance
        right_spacer = QLabel()
        right_spacer.setStyleSheet("background: transparent;")
        right_spacer.setMinimumWidth(80)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(center_layout, 2)
        main_layout.addWidget(right_spacer, 1)
        
        self.update_time()
    
    def setup_timer(self):
        """Setup timer to update time every second"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
    
    def update_time(self):
        """Update time and date display"""
        now = QDateTime.currentDateTime()
        
        # Format day and date
        day_str = now.toString("ddd").upper()
        date_str = now.toString("dd MMM").upper()
        self.day_label.setText(f"{day_str} → {date_str}")
        
        # Format time
        hours = now.time().hour()
        minutes = now.time().minute()
        seconds = now.time().second()
        
        # 12-hour format
        period = "AM" if hours < 12 else "PM"
        hours_12 = hours % 12
        if hours_12 == 0:
            hours_12 = 12
        
        time_str = f"{hours_12:02d}:{minutes:02d}"
        seconds_str = f"{seconds:02d}"
        
        self.time_label.setText(time_str)
        self.seconds_label.setText(seconds_str)
        self.period_label.setText(period)
    
    def closeEvent(self, event):
        """Stop timer on close"""
        self.timer.stop()
        event.accept()
