"""
Parameters page for telemetry configuration
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QCheckBox, QDialog, QLineEdit, QTextEdit)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from typing import Dict
import os

from src.ui.CustomMessageBox import CustomMessageBox1
from src.ui.CustomMessageBox import CustomMessageBox


class ParametersPage(QWidget):
    """Full-page parameters configuration"""
    
    back_clicked = Signal()
    parameters_changed = Signal()
    
    def __init__(self, db_manager=None, auth_service=None, sync_service=None, parameter_sync_service=None):
        super().__init__()
        self.db = db_manager
        self.auth_service = auth_service
        self.sync_service = sync_service
        self.parameter_sync_service = parameter_sync_service
        self.desktop_sync = None
        if sync_service:
            from src.services.desktop_sync_service import DesktopSyncService
            self.desktop_sync = DesktopSyncService(db_manager)
        
        # Connect to parameter sync service signals
        if parameter_sync_service:
            parameter_sync_service.parameters_fetched.connect(self._on_parameters_fetched)
            parameter_sync_service.parameter_updated.connect(self._on_parameter_updated)
        
        self.parameters = self.get_default_parameters()
        self._refresh_pending = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup parameters page UI"""
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
        
        # Responsive margins and spacing
        screen_width = self.screen().availableGeometry().width()
        margin = 20 if screen_width < 1200 else 40
        spacing = 15 if screen_width < 1200 else 30
        
        content_layout.setContentsMargins(margin, margin, margin, margin)
        content_layout.setSpacing(spacing)
        
        # Title section
        title_layout = QHBoxLayout()
        
        title_section = QVBoxLayout()
        title_label = QLabel("Telemetry Parameters")
        title_label.setStyleSheet("font-size: 36px; font-weight: 700; color: white;")
        
        subtitle_label = QLabel("Configure which parameters the desktop application should collect")
        subtitle_label.setStyleSheet("font-size: 16px; color: #94a3b8;")
        
        title_section.addWidget(title_label)
        title_section.addWidget(subtitle_label)
        
        title_layout.addLayout(title_section)
        title_layout.addStretch()
        
        # Action buttons (admin can add parameters)
        if self.auth_service:
            user = self.auth_service.get_current_user()
            if user and user.get('role') == 'admin':
                add_btn = QPushButton("+ Add Parameter")
                add_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #059669;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-weight: 600;
                        font-size: 14px;
                    }
                    QPushButton:hover { background-color: #047857; }
                """)
                add_btn.clicked.connect(self.add_parameter)
                title_layout.addWidget(add_btn)
        
        content_layout.addLayout(title_layout)
        
        # Info box
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #1e3a5f;
                border: 1px solid #3b82f6;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_label = QLabel(f"{len([p for p in self.parameters if p['enabled']])} of {len(self.parameters)} parameters enabled. Desktop will collect and send only enabled parameters every 3 seconds.")
        info_label.setStyleSheet("color: #93c5fd; font-size: 14px;")
        info_layout.addWidget(info_label)
        content_layout.addWidget(info_frame)
        
        # Parameters table
        self.create_table(content_layout)
        
        layout.addWidget(content_widget)
    
    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(90)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2d3748;
                border: none;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo and title
        logo_title_layout = QHBoxLayout()
        logo_title_layout.setSpacing(15)
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'logo.svg')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setStyleSheet("background-color: transparent;")
        else:
            logo_label.setText("⚡")
            logo_label.setStyleSheet("""
                QLabel {
                    background-color: #2563eb;
                    color: white;
                    font-size: 28px;
                    border-radius: 12px;
                    padding: 8px;
                }
            """)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(50, 50)
        
        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        
        title_label = QLabel("PrecisionPulse")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: 700;
                background: transparent;
            }
        """)
        
        subtitle_label = QLabel("Parameter Configuration")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 14px;
                background: transparent;
            }
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        logo_title_layout.addWidget(logo_label)
        logo_title_layout.addLayout(title_layout)
        
        header_layout.addLayout(logo_title_layout)
        header_layout.addStretch()
        
        # Back button
        back_btn = QPushButton("Back to Dashboard")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #1e293b;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #f1f5f9; }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        
        header_layout.addWidget(back_btn)
        layout.addWidget(header_frame)
    
    def create_table(self, layout):
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Status", "Parameter", "Unit", "Description", "Actions"])
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2d3748;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                selection-background-color: #1e3a5f;
            }
            QTableWidget::item {
                padding: 16px;
                border-bottom: 1px solid #374151;
            }
            QTableWidget::item:selected {
                background-color: #1e3a5f;
            }
            QHeaderView::section {
                background-color: #374151;
                color: #9ca3af;
                padding: 16px;
                border: none;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
            }
        """)
        
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        table.setColumnWidth(0, 150)
        table.setColumnWidth(2, 100)
        table.setColumnWidth(4, 150)
        
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(self.parameters))
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        for i, param in enumerate(self.parameters):
            # Status - clickable button
            status_widget = QWidget()
            status_widget.setStyleSheet("background: transparent;")
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(16, 0, 0, 0)
            
            status_btn = QPushButton(f"{'✓' if param['enabled'] else '✗'} {'Enabled' if param['enabled'] else 'Disabled'}")
            status_btn.setProperty('param_index', i)
            status_btn.setCursor(Qt.PointingHandCursor)
            status_btn.setStyleSheet(f"""
                QPushButton {{
                    color: white;
                    background-color: {'#059669' if param['enabled'] else '#dc2626'};
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 12px;
                    border: none;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {'#047857' if param['enabled'] else '#b91c1c'};
                }}
            """)
            status_btn.clicked.connect(lambda checked, idx=i: self.toggle_parameter(idx))
            
            status_layout.addWidget(status_btn)
            status_layout.addStretch()
            table.setCellWidget(i, 0, status_widget)
            
            # Parameter
            param_item = QTableWidgetItem(param['name'])
            param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(i, 1, param_item)
            
            # Unit
            unit_item = QTableWidgetItem(param['unit'])
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(i, 2, unit_item)
            
            # Description
            desc_item = QTableWidgetItem(param['description'])
            desc_item.setForeground(Qt.gray)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(i, 3, desc_item)
            
            # Actions
            actions_widget = QWidget()
            actions_widget.setStyleSheet("background: transparent;")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 16, 0)
            actions_layout.addStretch()
            
            # Only show remove button for admins
            if self.auth_service:
                user = self.auth_service.get_current_user()
                if user and user.get('role') == 'admin':
                    remove_btn = QPushButton("Remove")
                    remove_btn.setProperty('param_index', i)
                    remove_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #dc2626;
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 8px 16px;
                            font-weight: 600;
                            font-size: 12px;
                        }
                        QPushButton:hover { background-color: #b91c1c; }
                    """)
                    remove_btn.clicked.connect(lambda checked, idx=i: self.remove_parameter(idx))
                    actions_layout.addWidget(remove_btn)
            
            table.setCellWidget(i, 4, actions_widget)
            table.setRowHeight(i, 70)
        
        self.table = table
        layout.addWidget(table)
    
    def toggle_parameter(self, index):
        if not self.auth_service:
            print("Error: Auth service not available")
            return
        
        param = self.parameters[index]
        new_enabled_state = not param['enabled']
        
        try:
            import requests
            token = self.auth_service.get_token()
            if not token:
                print("Error: No authentication token")
                return
            
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
            response = requests.put(
                f"http://localhost:5000/api/parameters/{param['id']}",
                json={"enabled": new_enabled_state},
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                self.parameters[index]['enabled'] = new_enabled_state
                print(f"Parameter updated: {param['name']} - Enabled: {new_enabled_state}")
                self.parameters_changed.emit()
                self._sort_parameters()
                self._refresh_table_full()
            else:
                print(f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error: {e}")
    
    def _sort_parameters(self):
        """Sort parameters: enabled first, then disabled"""
        self.parameters.sort(key=lambda p: (not p['enabled'], p.get('name', '')))
    
    def refresh_ui(self):
        """Update a single table row without full refresh"""
        if not hasattr(self, 'table'):
            return
    
    def _on_parameters_fetched(self, parameters):
        """Handle parameters fetched from sync service"""
        self.parameters = parameters
        self._sort_parameters()
        self._refresh_table_full()
    
    def _on_parameter_updated(self, parameter):
        """Handle single parameter update from MQTT"""
        # Find and update parameter in list
        for i, p in enumerate(self.parameters):
            if p.get('id') == parameter.get('id'):
                self.parameters[i] = parameter
                self._sort_parameters()
                self._refresh_table_full()
                return
        
        # New parameter - add to list
        self.parameters.append(parameter)
        self._sort_parameters()
        self._refresh_table_full()
    
    def _update_table_row(self, index):
        """Update a single table row without full refresh"""
        if not hasattr(self, 'table'):
            return
        
        param = self.parameters[index]
        enabled = param['enabled']
        
        # Update status button
        status_widget = self.table.cellWidget(index, 0)
        if status_widget:
            status_btn = status_widget.findChild(QPushButton)
            if status_btn:
                status_btn.setText(f"{'✓' if enabled else '✗'} {'Enabled' if enabled else 'Disabled'}")
                status_btn.setStyleSheet(f"""
                    QPushButton {{
                        color: white;
                        background-color: {'#059669' if enabled else '#dc2626'};
                        padding: 6px 12px;
                        border-radius: 6px;
                        font-weight: 600;
                        font-size: 12px;
                        border: none;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        background-color: {'#047857' if enabled else '#b91c1c'};
                    }}
                """)
        
        # Update info label
        enabled_count = len([p for p in self.parameters if p['enabled']])
        for child in self.findChildren(QLabel):
            if 'parameters enabled' in child.text():
                child.setText(f"{enabled_count} of {len(self.parameters)} parameters enabled. Desktop will collect and send only enabled parameters every 3 seconds.")
                break
    
    def _refresh_table_full(self):
        """Full table refresh when rows are added/removed"""
        if self._refresh_pending:
            return
        self._refresh_pending = True
        QTimer.singleShot(0, self._do_refresh_table_full)
    
    def _do_refresh_table_full(self):
        """Perform full table refresh"""
        try:
            if hasattr(self, 'table') and self.table:
                old_table = self.table
                for widget in self.findChildren(QWidget):
                    layout = widget.layout()
                    if layout and layout.indexOf(old_table) >= 0:
                        layout.removeWidget(old_table)
                        old_table.deleteLater()
                        self.create_table(layout)
                        return
        except Exception as e:
            print(f"Error in _do_refresh_table_full: {e}")
        finally:
            self._refresh_pending = False
    
    def remove_parameter(self, index):
        if not self.auth_service:
            print("Error: Auth service not available")
            return
        
        user = self.auth_service.get_current_user()
        if not user or user.get('role') != 'admin':
            print("Error: Only admins can delete parameters")
            return
        
        param = self.parameters[index]
        msg = CustomMessageBox1("Confirm Action", "Do you want to delete this parameter?")
        result = msg.exec()
        
        if result == QDialog.Accepted:
            try:
                import requests
                token = self.auth_service.get_token()
                if not token:
                    print("Error: No authentication token")
                    return
                
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
                response = requests.delete(
                    f"http://localhost:5000/api/parameters/{param['id']}",
                    headers=headers,
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"Parameter deleted: {param['name']}")
                    self.parameters_changed.emit()
                    self.parameters = self.get_default_parameters()
                else:
                    print(f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error: {e}")
            
            self._refresh_table_full()
    
    def add_parameter(self):
        if not self.auth_service:
            print("Error: Auth service not available")
            return
        
        user = self.auth_service.get_current_user()
        if not user or user.get('role') != 'admin':
            print("Error: Only admins can add parameters")
            return
        
        from PySide6.QtWidgets import QApplication
        
        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        overlay.show()
        
        dialog = AddParameterDialog(self, self.parameters)
        screen = QApplication.primaryScreen().geometry()
        dialog.move(screen.center().x() - dialog.width() // 2, screen.center().y() - dialog.height() // 2)
        
        result = dialog.exec()
        overlay.deleteLater()
        
        if result:
            param_data = dialog.get_parameter_data()
            try:
                import requests
                token = self.auth_service.get_token()
                if not token:
                    print("Error: No authentication token")
                    return
                
                print(f"Adding parameter: {param_data}")
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
                response = requests.post(
                    "http://localhost:5000/api/parameters",
                    json={"name": param_data['name'], "unit": param_data['unit'], "description": param_data['description'], "enabled": param_data['enabled']},
                    headers=headers,
                    timeout=5
                )
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")
                
                if response.status_code in [200, 201]:
                    print(f"Parameter created successfully")
                    self.parameters_changed.emit()
                    self.parameters = self.get_default_parameters()
                else:
                    print(f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
            self._refresh_table_full()
    
    def get_default_parameters(self):
        try:
            import requests
            token = None
            if self.auth_service:
                token = self.auth_service.get_token()
            
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            response = requests.get(
                "http://localhost:5000/api/parameters",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                params = data.get('parameters', [])
                self._sort_parameters_list(params)
                
                if self.db:
                    import sqlite3
                    with sqlite3.connect(self.db.db_path) as conn:
                        cursor = conn.cursor()
                        for param in params:
                            cursor.execute('''
                                INSERT OR REPLACE INTO parameters (id, name, unit, description, enabled)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (param['id'], param['name'], param['unit'], param.get('description', ''), param.get('enabled', True)))
                        conn.commit()
                
                return params
        except Exception as e:
            print(f"Error fetching parameters: {e}")
        
        return []
    
    def _sort_parameters_list(self, params):
        """Sort a parameters list: enabled first, then disabled"""
        params.sort(key=lambda p: (not p['enabled'], p.get('name', '')))


class AddParameterDialog(QDialog):
    """Dialog for adding new parameters"""
    
    def __init__(self, parent=None, existing_parameters=None):
        super().__init__(parent)
        self.existing_parameters = existing_parameters or []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("")
        self.setModal(True)
        self.setFixedSize(500, 580)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container with rounded corners
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #374151;
                border-radius: 16px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Add New Parameter")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: white;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Parameter Name
        name_label = QLabel("Parameter Name")
        name_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Temperature")
        self.name_input.setFixedHeight(45)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 16px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        layout.addWidget(self.name_input)
        
        # Unit
        unit_label = QLabel("Unit")
        unit_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(unit_label)
        
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("e.g., °C, kPa, L/s")
        self.unit_input.setFixedHeight(45)
        self.unit_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 16px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        layout.addWidget(self.unit_input)
        
        # Description
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Brief description of this parameter")
        self.desc_input.setFixedHeight(100)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #3b82f6;
            }
        """)
        layout.addWidget(self.desc_input)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        add_btn = QPushButton("Add Parameter")
        add_btn.setFixedHeight(45)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        add_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #4b5563;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #374151;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        main_layout.addWidget(container)
    
    def get_parameter_data(self):
        """Get parameter data from form"""
        import time
        return {
            'id': f"param_{int(time.time())}",
            'name': self.name_input.text() or "New Parameter",
            'unit': self.unit_input.text() or "unit",
            'description': self.desc_input.toPlainText() or "No description",
            'enabled': True
        }
    
    def accept(self):
        """Validate and accept dialog"""
        name = self.name_input.text().strip()
        unit = self.unit_input.text().strip()
        
        if not name:
            from src.ui.CustomMessageBox import CustomMessageBox
            msg = CustomMessageBox("Validation Error", "Parameter name is required")
            msg.exec()
            return
        
        if not unit:
            from src.ui.CustomMessageBox import CustomMessageBox
            msg = CustomMessageBox("Validation Error", "Parameter unit is required")
            msg.exec()
            return
        
        # Check for duplicate parameter name
        for param in self.existing_parameters:
            if param['name'].lower() == name.lower():
                from src.ui.CustomMessageBox import CustomMessageBox
                msg = CustomMessageBox("Validation Error", f"Parameter '{name}' already exists")
                msg.exec()
                return        
        super().accept()
