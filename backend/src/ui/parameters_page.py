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
    
    def __init__(self, db_manager=None, auth_service=None, sync_service=None):
        super().__init__()
        self.db = db_manager
        self.auth_service = auth_service
        self.sync_service = sync_service
        self.desktop_sync = None
        if sync_service:
            from src.services.desktop_sync_service import DesktopSyncService
            self.desktop_sync = DesktopSyncService(db_manager)
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
        """Create parameters table"""
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
            
            # Only show remove button for users with write permission
            if self.auth_service and self.db:
                user = self.auth_service.get_current_user()
                if user and self.db.check_permission(user['role'], 'parameters', 'write'):
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
                else:
                    # Show empty space for non-admin users
                    empty_label = QLabel("View Only")
                    empty_label.setStyleSheet("color: #6b7280; font-size: 12px; font-style: italic;")
                    actions_layout.addWidget(empty_label)
            
            table.setCellWidget(i, 4, actions_widget)
            table.setRowHeight(i, 70)
        
        self.table = table
        layout.addWidget(table)
    
    def toggle_parameter(self, index):
        """Toggle parameter enabled/disabled state"""
        self.parameters[index]['enabled'] = not self.parameters[index]['enabled']
        
        # Sync to backend
        try:
            import requests
            param = self.parameters[index]
            response = requests.put(
                f"http://localhost:5000/api/internal/sync-parameter",
                json={
                    "name": param['name'],
                    "unit": param['unit'],
                    "description": param['description'],
                    "enabled": param['enabled']
                },
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if response.status_code == 200:
                print(f"✓ Parameter synced to backend: {param['name']}")
                
                # Update local SQLite
                import sqlite3
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE parameters SET enabled = ? WHERE id = ?
                    ''', (param['enabled'], param['id']))
                    conn.commit()
                print(f"✓ Parameter updated in local SQLite: {param['name']}")
                
                # Emit signal to notify dashboard of parameter change
                self.parameters_changed.emit()
                
                # Update table cell directly (zero-refresh)
                self._update_table_row(index)
        except Exception as e:
            print(f"✗ Backend sync failed for parameter update: {e}")
    
    def refresh_ui(self):
        """Update a single table row without full refresh"""
        if not hasattr(self, 'table'):
            return
        
        # This is now a zero-refresh method - called after toggle_parameter
        # The row update happens in _update_table_row
    
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
        """Remove parameter from list"""
        from PySide6.QtWidgets import QMessageBox
        param = self.parameters[index]
        msg = CustomMessageBox1("Confirm Action", "Do you want to delete this parameter?")
        result = msg.exec()  # Waits for user input

        
        
        if result == QDialog.Accepted:
            # Sync to backend
            try:
                import requests
                response = requests.delete(
                    f"http://localhost:5000/api/internal/sync-parameter-delete",
                    json={"id": param['id']},  # Use ID instead of name
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"✓ Parameter deleted from backend: {param['name']}")
                    
                    # Remove from local SQLite
                    import sqlite3
                    with sqlite3.connect(self.db.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM parameters WHERE id = ?', (param['id'],))
                        conn.commit()
                    print(f"✓ Parameter deleted from local SQLite: {param['name']}")
                    
                    # Emit signal to notify dashboard of parameter change
                    self.parameters_changed.emit()
            except Exception as e:
                print(f"✗ Backend sync failed for parameter deletion: {e}")
            
            self.parameters.pop(index)
            self._refresh_table_full()
    
    def add_parameter(self):
        """Show add parameter dialog"""
        from PySide6.QtWidgets import  QApplication
        
        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        overlay.show()
        
        dialog = AddParameterDialog(self)
        
        screen = QApplication.primaryScreen().geometry()
        dialog.move(
            screen.center().x() - dialog.width() // 2,
            screen.center().y() - dialog.height() // 2
        )
        
        result = dialog.exec()
        overlay.deleteLater()
        
        if result:
            param_data = dialog.get_parameter_data()
            # Sync to backend first
            try:
                import requests
                response = requests.post(
                    "http://localhost:5000/api/internal/sync-parameter",
                    json={
                        "name": param_data['name'],
                        "unit": param_data['unit'],
                        "description": param_data['description'],
                        "enabled": param_data['enabled']
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                if response.status_code in [200, 201]:
                    print(f"✓ Parameter synced to backend: {param_data['name']}")
                    
                    # Get the parameter ID from backend response
                    backend_data = response.json()
                    
                    # Fetch updated parameters from backend to get the real ID
                    params_response = requests.get(
                        "http://localhost:5000/api/internal/parameters",
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    
                    if params_response.status_code == 200:
                        backend_params = params_response.json().get('parameters', [])
                        # Find the newly created parameter
                        new_param = next((p for p in backend_params if p['name'] == param_data['name']), None)
                        if new_param:
                            # Save to local SQLite with real ID
                            import sqlite3
                            with sqlite3.connect(self.db.db_path) as conn:
                                cursor = conn.cursor()
                                cursor.execute('''
                                    INSERT OR REPLACE INTO parameters (id, name, unit, enabled, description)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (new_param['id'], new_param['name'], new_param['unit'], 
                                      new_param['enabled'], new_param['description']))
                                conn.commit()
                            print(f"✓ Parameter saved to local SQLite: {new_param['name']}")
                            
                            # Update local parameters list
                            self.parameters.append(new_param)
                            
                            # Emit signal to notify dashboard of parameter change
                            self.parameters_changed.emit()
                else:
                    print(f"✗ Backend sync failed: {response.status_code}")
            except Exception as e:
                print(f"✗ Backend sync failed: {e}")
            self._refresh_table_full()
    
    def get_default_parameters(self):
        """Get parameters from backend API"""
        try:
            import requests
            response = requests.get(
                "http://localhost:5000/api/internal/parameters",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('parameters', [])
        except Exception as e:
            print(f"Error fetching parameters: {e}")
        
        return []




class AddParameterDialog(QDialog):
    """Dialog for adding new parameters"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
