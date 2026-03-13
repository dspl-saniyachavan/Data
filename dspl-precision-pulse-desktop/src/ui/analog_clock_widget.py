"""
Elegant analog clock widget for dashboard
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QDateTime, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush
import math


class AnalogClockWidget(QWidget):
    """Elegant analog clock widget with modern design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 320)
        self.setMaximumSize(280, 320)
        self.setup_timer()
    
    def setup_timer(self):
        """Setup timer to update clock every second"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)
    
    def paintEvent(self, event):
        """Paint the clock"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get current time
        now = QDateTime.currentDateTime()
        hours = now.time().hour() % 12
        minutes = now.time().minute()
        seconds = now.time().second()
        
        # Clock dimensions
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2 - 30  # Adjust for date display below
        radius = min(width, height) / 2 - 20
        
        # Draw outer circle (clock face background)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#e5e7eb"), 2))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                           int(radius * 2), int(radius * 2))
        
        # Draw decorative outer ring
        painter.setPen(QPen(QColor("#d1d5db"), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(int(center_x - radius - 5), int(center_y - radius - 5), 
                           int((radius + 5) * 2), int((radius + 5) * 2))
        
        # Draw hour markers
        painter.setPen(QPen(QColor("#1e293b"), 2))
        for i in range(12):
            angle = i * 30 * math.pi / 180
            x1 = center_x + (radius - 15) * math.sin(angle)
            y1 = center_y - (radius - 15) * math.cos(angle)
            x2 = center_x + (radius - 5) * math.sin(angle)
            y2 = center_y - (radius - 5) * math.cos(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw minute markers (smaller dots)
        painter.setPen(QPen(QColor("#94a3b8"), 1))
        for i in range(60):
            if i % 5 != 0:  # Skip hour markers
                angle = i * 6 * math.pi / 180
                x = center_x + (radius - 8) * math.sin(angle)
                y = center_y - (radius - 8) * math.cos(angle)
                painter.drawPoint(int(x), int(y))
        
        # Draw center circle
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - 6), int(center_y - 6), 12, 12)
        
        # Draw hour hand
        hour_angle = (hours + minutes / 60) * 30 * math.pi / 180
        hour_length = radius * 0.5
        hour_x = center_x + hour_length * math.sin(hour_angle)
        hour_y = center_y - hour_length * math.cos(hour_angle)
        painter.setPen(QPen(QColor("#1e293b"), 6))
        painter.drawLine(int(center_x), int(center_y), int(hour_x), int(hour_y))
        
        # Draw minute hand
        minute_angle = minutes * 6 * math.pi / 180
        minute_length = radius * 0.7
        minute_x = center_x + minute_length * math.sin(minute_angle)
        minute_y = center_y - minute_length * math.cos(minute_angle)
        painter.setPen(QPen(QColor("#475569"), 4))
        painter.drawLine(int(center_x), int(center_y), int(minute_x), int(minute_y))
        
        # Draw second hand
        second_angle = seconds * 6 * math.pi / 180
        second_length = radius * 0.8
        second_x = center_x + second_length * math.sin(second_angle)
        second_y = center_y - second_length * math.cos(second_angle)
        painter.setPen(QPen(QColor("#ef4444"), 2))
        painter.drawLine(int(center_x), int(center_y), int(second_x), int(second_y))
        
        # Draw date and day below clock
        painter.setPen(QPen(QColor("#1e293b")))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        
        date_str = now.toString("MMM dd")
        day_str = now.toString("dddd")
        
        # Draw date
        painter.drawText(int(center_x - 50), int(center_y + radius + 20), 100, 20, 
                        Qt.AlignCenter, date_str)
        
        # Draw day
        painter.setFont(QFont("Arial", 10, QFont.Normal))
        painter.setPen(QPen(QColor("#64748b")))
        painter.drawText(int(center_x - 50), int(center_y + radius + 40), 100, 20, 
                        Qt.AlignCenter, day_str)
    
    def closeEvent(self, event):
        """Stop timer on close"""
        self.timer.stop()
        event.accept()
