"""
Telemetry widget for real-time data display
"""

import random
from collections import deque
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGridLayout, QScrollArea)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPainter, QColor
from src.ui.simple_line_chart import SimpleLineChart

class MiniChart(QWidget):
    """Mini bar chart widget"""
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.values = deque([random.randint(30, 90) for _ in range(14)], maxlen=14)
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)
    
    def update_value(self, value):
        """Add new value and update chart"""
        self.values.append(int(value))
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        bar_width = width / len(self.values)
        
        for i, value in enumerate(self.values):
            bar_height = (value / 100) * height
            x = i * bar_width
            y = height - bar_height
            
            painter.fillRect(int(x + 1), int(y), int(bar_width - 2), int(bar_height), self.color)


class TelemetryWidget(QWidget):
    """Widget for displaying real-time telemetry data"""
    
    def __init__(self, telemetry_service=None, auth_service=None):
        super().__init__()
        self.telemetry_service = telemetry_service
        self.auth_service = auth_service
        self.parameter_widgets = {}
        self.line_charts = {}
        self.charts_created = False
        self.setup_ui()
        
        if self.telemetry_service:
            self.telemetry_service.parameters_updated.connect(self.update_all_parameters)
            self.telemetry_service.parameter_changed.connect(self.update_single_parameter)
            print(" Forcing initial parameter refresh...")
            self.telemetry_service.refresh_parameters()
            if self.auth_service:
                current_user = self.auth_service.get_current_user()
                if current_user and current_user.get('role') == 'client':
                    print(" Client mode: Starting telemetry streaming")
                    self.telemetry_service.start_streaming(3)
                elif current_user and current_user.get('role') in ['admin', 'user']:
                    print(f" {current_user.get('role').title()} mode: Receiving telemetry from clients")
                    if not self.telemetry_service.mqtt_service.is_connected:
                        print(" Connecting to MQTT broker...")
                        self.telemetry_service.mqtt_service.connect()
    
    def setup_ui(self):
        """Setup telemetry UI"""
        self.setStyleSheet("background-color: #0f172a;")
        layout = QVBoxLayout(self)
        
        # Responsive spacing and margins
        screen_width = self.screen().availableGeometry().width()
        spacing = 12 if screen_width < 1200 else 24
        margin = 30 if screen_width < 1200 else 80
        
        layout.setSpacing(spacing)
        layout.setContentsMargins(margin, 30, margin, 30)
        
        user_name = "User"
        if self.auth_service:
            current_user = self.auth_service.get_current_user()
            if current_user:
                user_name = current_user.get('name', 'User')
        
        welcome_label = QLabel(f"Welcome back, {user_name}!")
        welcome_label.setStyleSheet("""
            font-size: 48px; 
            font-weight: 700; 
            color: white; 
            letter-spacing: -0.5px;
            font-family: 'Inter', 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
            background: transparent;
        """)
        
        subtitle_label = QLabel("Monitor your telemetry streams in real-time")
        subtitle_label.setStyleSheet("""
            font-size: 20px; 
            color: #94a3b8; 
            font-weight: 400;
            font-family: 'Inter', 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
            background: transparent;
        """)
        
        layout.addWidget(welcome_label)
        layout.addWidget(subtitle_label)
        layout.addSpacing(16)
        
        section_label = QLabel("LIVE DATA STREAM")
        section_label.setStyleSheet("""
            font-size: 13px; 
            font-weight: 700; 
            color: #64748b; 
            letter-spacing: 2.5px;
            font-family: 'Inter', 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
            background: transparent;
        """)
        layout.addWidget(section_label)
        layout.addSpacing(8)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical { background: #1e293b; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #475569; border-radius: 4px; }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(24)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(16)
        self.create_parameter_cards()
        scroll_layout.addLayout(self.grid_layout)
        
        scroll_layout.addSpacing(32)
        trends_label = QLabel("HISTORICAL TRENDS")
        trends_label.setStyleSheet("""
            font-size: 13px; 
            font-weight: 700; 
            color: #64748b; 
            letter-spacing: 2.5px;
            background: transparent;
        """)
        scroll_layout.addWidget(trends_label)
        scroll_layout.addSpacing(16)
        
        self.charts_layout = QVBoxLayout()
        self.charts_layout.setSpacing(24)
        self.create_line_charts()
        scroll_layout.addLayout(self.charts_layout)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)
    
    def create_parameter_cards(self):
        """Create parameter display cards"""
        if self.telemetry_service:
            parameters = list(self.telemetry_service.get_parameters().values())
            print(f"Creating parameter cards for {len(parameters)} parameters")
        else:
            parameters = []
        
        if not parameters:
            placeholder = QLabel("No parameters configured. Add parameters to see telemetry data.")
            placeholder.setStyleSheet("""
                QLabel {
                    color: #64748b;
                    font-size: 16px;
                    padding: 40px;
                    text-align: center;
                    background: transparent;
                }
            """)
            placeholder.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(placeholder, 0, 0, 1, 3)
            return
        
        for i, param in enumerate(parameters):
            card = self.create_parameter_card(param)
            self.grid_layout.addWidget(card, i // 3, i % 3)
    
    def create_parameter_card(self, param):
        """Create individual parameter card"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
                border: none;
            }
        """)
        card.setFixedSize(450, 200)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 24, 24, 20)
        
        header_layout = QHBoxLayout()
        
        value_label = QLabel(f"{param['value']:.1f}")
        value_label.setStyleSheet("""
            font-size: 56px; 
            font-weight: 700; 
            color: #0f172a; 
            letter-spacing: -1.5px;
            font-family: 'Inter', 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
            background: transparent;
        """)
        
        trend_label = QLabel("")
        trend_label.setStyleSheet("""
            font-size: 32px;
            color: #64748b;
            background: transparent;
        """)
        
        header_layout.addWidget(value_label)
        header_layout.addWidget(trend_label, alignment=Qt.AlignTop)
        header_layout.addStretch()
        
        name_label = QLabel(f"{param['name']} ({param['unit']})")
        name_label.setStyleSheet("""
            font-size: 15px; 
            color: #64748b; 
            font-weight: 500;
            font-family: 'Inter', 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
            background: transparent;
        """)
        
        chart = MiniChart(param['color'])
        chart.setFixedHeight(60)
        
        layout.addLayout(header_layout)
        layout.addWidget(name_label)
        layout.addWidget(chart)
        
        self.parameter_widgets[param['id']] = {
            'value_label': value_label,
            'trend_label': trend_label,
            'chart': chart,
            'min': param.get('min', 0),
            'max': param.get('max', 100),
            'prev_value': param['value']
        }
        
        return card
    
    def create_line_charts(self):
        """Create line charts once"""
        if self.charts_created:
            return
        
        if self.telemetry_service:
            parameters = list(self.telemetry_service.get_parameters().values())
            print(f" Creating line charts for {len(parameters)} parameters")
        else:
            parameters = []
        
        if not parameters:
            return
        
        for param in parameters:
            chart = SimpleLineChart(
                param['id'],
                param['name'],
                param['unit'],
                param['color']
            )
            self.charts_layout.addWidget(chart)
            self.line_charts[param['id']] = chart
        
        self.charts_created = True
    
    @Slot()
    def update_all_parameters(self):
        """Update all parameters"""
        if not self.telemetry_service:
            return
        
        parameters = self.telemetry_service.get_parameters()
        timestamp = datetime.now()
        
        # Check if new parameters were added
        current_param_ids = set(self.parameter_widgets.keys())
        new_param_ids = set(parameters.keys())
        
        if new_param_ids != current_param_ids:
            # Clear and recreate cards
            while self.grid_layout.count():
                self.grid_layout.takeAt(0).widget().deleteLater()
            self.parameter_widgets.clear()
            self.create_parameter_cards()
            
            # Clear and recreate line charts
            while self.charts_layout.count():
                self.charts_layout.takeAt(0).widget().deleteLater()
            self.line_charts.clear()
            self.charts_created = False
            self.create_line_charts()
        
        for param_id, param in parameters.items():
            if param_id in self.parameter_widgets:
                value = param['value']
                widget = self.parameter_widgets[param_id]
                prev_value = widget.get('prev_value', value)
                
                widget['value_label'].setText(f"{value:.1f}")
                
                if value > prev_value + 0.1:
                    widget['trend_label'].setText("▲")
                    widget['trend_label'].setStyleSheet("font-size: 32px; color: #059669; background: transparent;")
                elif value < prev_value - 0.1:
                    widget['trend_label'].setText("▼")
                    widget['trend_label'].setStyleSheet("font-size: 32px; color: #dc2626; background: transparent;")
                else:
                    widget['trend_label'].setText("")
                    widget['trend_label'].setStyleSheet("font-size: 32px; color: #64748b; background: transparent;")
                
                widget['prev_value'] = value
                
                min_val = widget['min']
                max_val = widget['max']
                normalized = ((value - min_val) / (max_val - min_val)) * 100
                widget['chart'].update_value(normalized)
            
            if param_id in self.line_charts:
                self.line_charts[param_id].add_value(param['value'], timestamp)
    
    @Slot(str, float)
    def update_single_parameter(self, param_id, value):
        """Update single parameter"""
        timestamp = datetime.now()
        if param_id in self.parameter_widgets:
            widget = self.parameter_widgets[param_id]
            prev_value = widget.get('prev_value', value)
            
            widget['value_label'].setText(f"{value:.1f}")
            
            if value > prev_value + 0.1:
                widget['trend_label'].setText("▲")
                widget['trend_label'].setStyleSheet("font-size: 32px; color: #059669; background: transparent;")
            elif value < prev_value - 0.1:
                widget['trend_label'].setText("▼")
                widget['trend_label'].setStyleSheet("font-size: 32px; color: #dc2626; background: transparent;")
            else:
                widget['trend_label'].setText("")
                widget['trend_label'].setStyleSheet("font-size: 32px; color: #64748b; background: transparent;")
            
            widget['prev_value'] = value
            
            min_val = widget['min']
            max_val = widget['max']
            normalized = ((value - min_val) / (max_val - min_val)) * 100
            widget['chart'].update_value(normalized)
        
        if param_id in self.line_charts:
            self.line_charts[param_id].add_value(value, timestamp)
    
    def refresh_parameters(self):
        """Refresh parameters - called by main window when parameters change"""
        if not self.telemetry_service:
            return
        
        # Force refresh from backend
        self.telemetry_service.refresh_parameters()
        
        # Update UI with new parameters
        self.update_all_parameters()
