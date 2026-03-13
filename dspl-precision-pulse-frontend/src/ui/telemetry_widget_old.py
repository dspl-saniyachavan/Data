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
        self.setup_ui()
        
        if self.telemetry_service:
            self.telemetry_service.parameters_updated.connect(self.update_all_parameters)
            self.telemetry_service.parameter_changed.connect(self.update_single_parameter)
            # Force initial parameter refresh
            print(" Forcing initial parameter refresh...")
            self.telemetry_service.refresh_parameters()
            # Auto-start streaming only for client role (admin/user receive from clients)
            if self.auth_service:
                current_user = self.auth_service.get_current_user()
                if current_user and current_user.get('role') == 'client':
                    print(" Client mode: Starting telemetry streaming")
                    self.telemetry_service.start_streaming(3)
                elif current_user and current_user.get('role') in ['admin', 'user']:
                    print(f" {current_user.get('role').title()} mode: Receiving telemetry from clients")
                    # Admin/User needs to connect to MQTT to receive data
                    if not self.telemetry_service.mqtt_service.is_connected:
                        print(" Connecting to MQTT broker...")
                        self.telemetry_service.mqtt_service.connect()
    
    def refresh_parameters(self):
        """Refresh parameters display"""
        print("🔄 Refreshing telemetry widget parameters...")
        
        if self.telemetry_service:
            self.telemetry_service.refresh_parameters()
        
        # Clear and recreate parameter cards
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.parameter_widgets.clear()
        
        # Clear and recreate line charts
        for i in reversed(range(self.charts_layout.count())):
            widget = self.charts_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.line_charts.clear()
        
        # Recreate UI elements
        self.create_parameter_cards()
        self.create_line_charts()
        
        print(f"✅ Telemetry widget refreshed with {len(self.parameter_widgets)} parameters")
    
    def setup_ui(self):
        """Setup telemetry UI"""
        self.setStyleSheet("background-color: #0f172a;")
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(80, 50, 80, 50)
        
        # Welcome section
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
        
        # Section title
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
        
        # Scroll area
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
        
        # Parameter cards grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(16)
        self.create_parameter_cards()
        scroll_layout.addLayout(self.grid_layout)
        
        
        # Historical trends section
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
        
        # Line charts layout
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
            print("⚠️ No telemetry service available")
        
        if not parameters:
            print("⚠️ No parameters found - dashboard will be empty")
            # Create a placeholder message
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
    
    def _get_default_parameters(self):
        """Get default parameters - empty list since parameters come from backend"""
        return []
    
    def create_parameter_card(self, param):
        """Create individual parameter card with trend indicator"""
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
        
        # Header with value and trend
        header_layout = QHBoxLayout()
        
        # Value
        value_label = QLabel(f"{param['value']:.1f}")
        value_label.setStyleSheet("""
            font-size: 56px; 
            font-weight: 700; 
            color: #0f172a; 
            letter-spacing: -1.5px;
            font-family: 'Inter', 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
            background: transparent;
        """)
        
        # Trend indicator
        trend_label = QLabel("•")
        trend_label.setStyleSheet("""
            font-size: 32px;
            color: #64748b;
            background: transparent;
        """)
        
        header_layout.addWidget(value_label)
        header_layout.addWidget(trend_label, alignment=Qt.AlignTop)
        header_layout.addStretch()
        
        # Name
        name_label = QLabel(f"{param['name']} ({param['unit']})")
        name_label.setStyleSheet("""
            font-size: 15px; 
            color: #64748b; 
            font-weight: 500;
            font-family: 'Inter', 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
            background: transparent;
        """)
        
        # Mini chart
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
        """Create line charts for historical trends"""
        if self.telemetry_service:
            parameters = list(self.telemetry_service.get_parameters().values())
            print(f" Creating line charts for {len(parameters)} parameters")
        else:
            parameters = []
            print(" No telemetry service for charts")
        
        if not parameters:
            print(" No parameters for charts")
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

    
    @Slot()
    def update_all_parameters(self):
        """Update all parameters with trend indicators"""
        if not self.telemetry_service:
            return
        
        parameters = self.telemetry_service.get_parameters()
        timestamp = datetime.now()
        
        for param_id, param in parameters.items():
            if param_id in self.parameter_widgets:
                value = param['value']
                widget = self.parameter_widgets[param_id]
                prev_value = widget.get('prev_value', value)
                
                # Update value
                widget['value_label'].setText(f"{value:.1f}")
                
                # Update trend indicator
                if value > prev_value + 0.1:
                    widget['trend_label'].setText("▲")
                    widget['trend_label'].setStyleSheet("font-size: 32px; color: #059669; background: transparent;")
                elif value < prev_value - 0.1:
                    widget['trend_label'].setText("▼")
                    widget['trend_label'].setStyleSheet("font-size: 32px; color: #dc2626; background: transparent;")
                else:
                    widget['trend_label'].setText("•")
                    widget['trend_label'].setStyleSheet("font-size: 32px; color: #64748b; background: transparent;")
                
                widget['prev_value'] = value
                
                # Update mini chart
                min_val = widget['min']
                max_val = widget['max']
                normalized = ((value - min_val) / (max_val - min_val)) * 100
                widget['chart'].update_value(normalized)
                
            # Update line chart
            if param_id in self.line_charts:
                print(f"[CHART_UPDATE] Adding value {param['value']} to chart {param_id}")
                self.line_charts[param_id].add_value(param['value'], timestamp)
            else:
                print(f"[CHART_UPDATE] Chart not found for param {param_id}. Available: {list(self.line_charts.keys())}")
    
    @Slot(str, float)
    def update_single_parameter(self, param_id, value):
        """Update single parameter with trend"""
        timestamp = datetime.now()
        if param_id in self.parameter_widgets:
            widget = self.parameter_widgets[param_id]
            prev_value = widget.get('prev_value', value)
            
            # Update value
            widget['value_label'].setText(f"{value:.1f}")
            
            # Update trend indicator
            if value > prev_value + 0.1:
                widget['trend_label'].setText("▲")
                widget['trend_label'].setStyleSheet("font-size: 32px; color: #059669; background: transparent;")
            elif value < prev_value - 0.1:
                widget['trend_label'].setText("▼")
                widget['trend_label'].setStyleSheet("font-size: 32px; color: #dc2626; background: transparent;")
            else:
                widget['trend_label'].setText("•")
                widget['trend_label'].setStyleSheet("font-size: 32px; color: #64748b; background: transparent;")
            
            widget['prev_value'] = value
            
            # Update mini chart
            min_val = widget['min']
            max_val = widget['max']
            normalized = ((value - min_val) / (max_val - min_val)) * 100
            widget['chart'].update_value(normalized)
        
        # Update line chart
        if param_id in self.line_charts:
            self.line_charts[param_id].add_value(value, timestamp)
