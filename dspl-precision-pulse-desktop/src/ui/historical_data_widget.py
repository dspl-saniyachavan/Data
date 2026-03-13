"""
Historical Data Widget for viewing parameter history
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen
import requests
from datetime import datetime, timedelta
from src.core.config import Config


class HistoricalDataWidget(QWidget):
    """Widget for viewing historical parameter data"""
    
    def __init__(self, database_manager):
        super().__init__()
        self.db = database_manager
        self.parameters = []
        self.history_data = []
        self.statistics = None
        self.selected_param_id = None
        self.time_range = 60
        
        self.init_ui()
        self.load_parameters()
        
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Parameter History")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1f2937;")
        layout.addWidget(title)
        
        # Filters
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()
        
        # Parameter selector
        filter_layout.addWidget(QLabel("Parameter:"))
        self.param_combo = QComboBox()
        self.param_combo.currentIndexChanged.connect(self.on_parameter_changed)
        filter_layout.addWidget(self.param_combo, 1)
        
        # Time range selector
        filter_layout.addWidget(QLabel("Time Range:"))
        self.time_combo = QComboBox()
        self.time_combo.addItems([
            "Last 5 minutes",
            "Last 15 minutes",
            "Last 30 minutes",
            "Last 1 hour",
            "Last 3 hours",
            "Last 6 hours",
            "Last 12 hours",
            "Last 24 hours"
        ])
        self.time_combo.setCurrentIndex(3)
        self.time_combo.currentIndexChanged.connect(self.on_time_range_changed)
        filter_layout.addWidget(self.time_combo, 1)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        filter_layout.addWidget(refresh_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QGridLayout()
        
        self.records_label = QLabel("0")
        self.records_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        stats_layout.addWidget(QLabel("Records:"), 0, 0)
        stats_layout.addWidget(self.records_label, 1, 0)
        
        self.min_label = QLabel("--")
        self.min_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        stats_layout.addWidget(QLabel("Minimum:"), 0, 1)
        stats_layout.addWidget(self.min_label, 1, 1)
        
        self.max_label = QLabel("--")
        self.max_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        stats_layout.addWidget(QLabel("Maximum:"), 0, 2)
        stats_layout.addWidget(self.max_label, 1, 2)
        
        self.avg_label = QLabel("--")
        self.avg_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        stats_layout.addWidget(QLabel("Average:"), 0, 3)
        stats_layout.addWidget(self.avg_label, 1, 3)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Chart placeholder
        self.chart_widget = SimpleHistoryChart()
        self.chart_widget.setMinimumHeight(300)
        layout.addWidget(self.chart_widget)
        
        # Data table
        table_group = QGroupBox("Recent Records")
        table_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        table_layout.addWidget(self.table)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
    def load_parameters(self):
        """Load parameters from database"""
        try:
            params = self.db.get_enabled_parameters()
            self.parameters = params
            
            self.param_combo.clear()
            for param in params:
                self.param_combo.addItem(
                    f"{param['name']} ({param['unit']})",
                    param['id']
                )
            
            if params:
                self.selected_param_id = params[0]['id']
                self.refresh_data()
        except Exception as e:
            print(f"[HISTORY] Error loading parameters: {e}")
    
    def on_parameter_changed(self, index):
        """Handle parameter selection change"""
        if index >= 0:
            self.selected_param_id = self.param_combo.itemData(index)
            self.refresh_data()
    
    def on_time_range_changed(self, index):
        """Handle time range change"""
        time_ranges = [5, 15, 30, 60, 180, 360, 720, 1440]
        self.time_range = time_ranges[index]
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh historical data"""
        if not self.selected_param_id:
            return
        
        self.fetch_history()
        self.fetch_statistics()
    
    def fetch_history(self):
        """Fetch historical data from backend"""
        try:
            response = requests.get(
                f"{Config.BACKEND_URL}/api/parameter-stream/parameter/{self.selected_param_id}/history",
                params={'minutes': self.time_range, 'limit': 1000},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.history_data = data.get('data', [])
                self.update_table()
                self.update_chart()
            else:
                print(f"[HISTORY] Error fetching history: {response.status_code}")
        except Exception as e:
            print(f"[HISTORY] Error: {e}")
    
    def fetch_statistics(self):
        """Fetch statistics from backend"""
        try:
            response = requests.get(
                f"{Config.BACKEND_URL}/api/parameter-stream/statistics",
                params={'parameter_id': self.selected_param_id, 'minutes': self.time_range},
                timeout=5
            )
            
            if response.status_code == 200:
                self.statistics = response.json()
                self.update_statistics()
            else:
                print(f"[HISTORY] Error fetching statistics: {response.status_code}")
        except Exception as e:
            print(f"[HISTORY] Error: {e}")
    
    def update_statistics(self):
        """Update statistics display"""
        if not self.statistics:
            return
        
        selected_param = next((p for p in self.parameters if p['id'] == self.selected_param_id), None)
        unit = selected_param['unit'] if selected_param else ''
        
        self.records_label.setText(str(self.statistics.get('count', 0)))
        self.min_label.setText(f"{self.statistics.get('min', 0):.2f} {unit}")
        self.max_label.setText(f"{self.statistics.get('max', 0):.2f} {unit}")
        self.avg_label.setText(f"{self.statistics.get('avg', 0):.2f} {unit}")
    
    def update_table(self):
        """Update data table"""
        self.table.setRowCount(0)
        
        selected_param = next((p for p in self.parameters if p['id'] == self.selected_param_id), None)
        unit = selected_param['unit'] if selected_param else ''
        
        for record in self.history_data[:50]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            self.table.setItem(row, 0, QTableWidgetItem(timestamp.strftime('%Y-%m-%d %H:%M:%S')))
            self.table.setItem(row, 1, QTableWidgetItem(f"{record['value']:.2f} {unit}"))
    
    def update_chart(self):
        """Update chart with new data"""
        self.chart_widget.set_data(self.history_data)


class SimpleHistoryChart(QWidget):
    """Simple line chart for historical data"""
    
    def __init__(self):
        super().__init__()
        self.data = []
        self.setMinimumHeight(300)
        
    def set_data(self, data):
        """Set chart data"""
        self.data = data
        self.update()
    
    def paintEvent(self, event):
        """Paint the chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#ffffff"))
        
        if not self.data or len(self.data) < 2:
            painter.setPen(QColor("#9ca3af"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No data available")
            return
        
        # Margins
        margin_left = 60
        margin_right = 20
        margin_top = 20
        margin_bottom = 40
        
        chart_width = self.width() - margin_left - margin_right
        chart_height = self.height() - margin_top - margin_bottom
        
        # Get value range
        values = [d['value'] for d in self.data]
        min_val = min(values)
        max_val = max(values)
        value_range = max_val - min_val if max_val != min_val else 1
        
        # Draw axes
        painter.setPen(QPen(QColor("#d1d5db"), 2))
        painter.drawLine(margin_left, margin_top, margin_left, self.height() - margin_bottom)
        painter.drawLine(margin_left, self.height() - margin_bottom, 
                        self.width() - margin_right, self.height() - margin_bottom)
        
        # Draw grid lines
        painter.setPen(QPen(QColor("#e5e7eb"), 1))
        for i in range(5):
            y = margin_top + (chart_height * i / 4)
            painter.drawLine(margin_left, int(y), self.width() - margin_right, int(y))
        
        # Draw data line
        painter.setPen(QPen(QColor("#3b82f6"), 2))
        
        points = []
        for i, record in enumerate(self.data):
            x = margin_left + (chart_width * i / (len(self.data) - 1))
            normalized = (record['value'] - min_val) / value_range
            y = self.height() - margin_bottom - (chart_height * normalized)
            points.append((int(x), int(y)))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
        
        # Draw value labels
        painter.setPen(QColor("#6b7280"))
        for i in range(5):
            value = max_val - (value_range * i / 4)
            y = margin_top + (chart_height * i / 4)
            painter.drawText(5, int(y) + 5, f"{value:.1f}")
