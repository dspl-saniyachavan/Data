from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
import os

class BufferPage(QWidget):
    """Display buffered telemetry records"""
    
    def __init__(self, telemetry_service=None, database_manager=None):
        super().__init__()
        self.telemetry_service = telemetry_service
        self.database_manager = database_manager
        self.setup_ui()
        
        # Refresh buffer every 5 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_buffer)
        self.refresh_timer.start(5000)
    
    def setup_ui(self):
        """Setup buffer UI"""
        self.setStyleSheet("background-color: #1e293b;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.create_header(layout)
        
        # Content
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #1e293b;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Buffered Telemetry")
        title_label.setStyleSheet("font-size: 36px; font-weight: 700; color: white;")
        content_layout.addWidget(title_label)
        
        # Info
        self.info_label = QLabel("Loading buffer...")
        self.info_label.setStyleSheet("font-size: 14px; color: #94a3b8;")
        content_layout.addWidget(self.info_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Unit", "Updated At"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                border: none;
                color: white;
                gridline-color: #1e293b;
            }
            QTableWidget::item {
                padding: 16px;
                border-bottom: 1px solid #1e293b;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #64748b;
                padding: 16px;
                border: none;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        content_layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        flush_btn = QPushButton("Flush Synced Records")
        flush_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #b91c1c; }
        """)
        flush_btn.clicked.connect(self.flush_buffer)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        refresh_btn.clicked.connect(self.load_buffer)
        
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(flush_btn)
        btn_layout.addStretch()
        content_layout.addLayout(btn_layout)
        
        layout.addWidget(content_widget)
    
    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(90)
        header_frame.setStyleSheet("background-color: #2d3748; border: none;")
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)
        title_layout = QVBoxLayout()
        title_label = QLabel("Buffer Management")
        title_label.setStyleSheet("color: white; font-size: 22px; font-weight: 700; background: transparent;")
        subtitle_label = QLabel("Buffered telemetry records")
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addWidget(header_frame)
    
    def load_buffer(self):
        """Load buffer records from local database"""
        try:
            if self.database_manager:
                buffer_records = self.database_manager.get_buffered_data()
                count = len(buffer_records)
                self.info_label.setText(f"Total buffered records: {count}")
                self.display_buffer(buffer_records)
            else:
                self.info_label.setText("Database manager not available")
        except Exception as e:
            self.info_label.setText(f"Error loading buffer: {e}")
    
    def display_buffer(self, records):
        """Display buffer records in table"""
        self.table.setRowCount(len(records))
        
        for i, record in enumerate(records):
            # Name
            param_item = QTableWidgetItem(record.get('parameter_name', ''))
            param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, param_item)
            
            # Value
            value_item = QTableWidgetItem(str(record.get('value', '')))
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 1, value_item)
            
            # Unit
            unit_item = QTableWidgetItem(record.get('unit', ''))
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 2, unit_item)
            
            # Updated At
            timestamp_item = QTableWidgetItem(record.get('timestamp', '')[:19])
            timestamp_item.setFlags(timestamp_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 3, timestamp_item)
    
    def flush_buffer(self):
        """Flush synced records from local database"""
        try:
            if self.database_manager:
                self.database_manager.clear_synced_data()
                self.info_label.setText("Flushed synced records")
                self.load_buffer()
            else:
                self.info_label.setText("Database manager not available")
        except Exception as e:
            self.info_label.setText(f"Error flushing buffer: {e}")
