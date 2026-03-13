"""
Manage Users page for admin
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QDialog, QLineEdit, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from typing import Dict
import os

from src.ui.CustomMessageBox import CustomMessageBox1
from src.ui.CustomMessageBox import CustomMessageBox


class ManageUsersPage(QWidget):
    """Admin page for managing users"""
    
    back_clicked = Signal()
    
    def __init__(self, db_manager=None, auth_service=None, sync_service=None):
        super().__init__()
        self.db = db_manager
        self.auth_service = auth_service
        self.sync_service = sync_service
        self.users = []
        self.setup_ui()
        self.load_users()
    
    def setup_ui(self):
        """Setup manage users UI"""
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
        content_layout.setSpacing(30)
        
        # Title section
        title_layout = QHBoxLayout()
        
        title_section = QVBoxLayout()
        title_label = QLabel("Manage Users")
        title_label.setStyleSheet("font-size: 36px; font-weight: 700; color: white;")
        
        subtitle_label = QLabel("Add, edit, or remove user accounts")
        subtitle_label.setStyleSheet("font-size: 16px; color: #94a3b8;")
        
        title_section.addWidget(title_label)
        title_section.addWidget(subtitle_label)
        
        title_layout.addLayout(title_section)
        title_layout.addStretch()
        
        # Add User button
        add_btn = QPushButton("+ Add User")
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
        add_btn.clicked.connect(self.add_user)
        title_layout.addWidget(add_btn)
        
        content_layout.addLayout(title_layout)
        
        # Info box (like parameters page)
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
        self.info_label = QLabel("Total users: 0. Manage user accounts and permissions.")
        self.info_label.setStyleSheet("color: #93c5fd; font-size: 14px;")
        info_layout.addWidget(self.info_label)
        content_layout.addWidget(info_frame)
        
        # Users table
        self.create_table(content_layout)
        
        layout.addWidget(content_widget)
    
    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(90)
        header_frame.setStyleSheet("QFrame { background-color: #2d3748; border: none; }")
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo and title
        logo_title_layout = QHBoxLayout()
        logo_title_layout.setSpacing(15)
        
        logo = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'logo.svg')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo.setStyleSheet("background-color: transparent;")
            
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(50, 50)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        
        title_label = QLabel("PrecisionPulse")
        title_label.setStyleSheet("QLabel { color: white; font-size: 22px; font-weight: 700; background: transparent; }")
        
        subtitle_label = QLabel("User Management")
        subtitle_label.setStyleSheet("QLabel { color: #94a3b8; font-size: 14px; background: transparent; }")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        logo_title_layout.addWidget(logo)
        logo_title_layout.addLayout(title_layout)
        
        header_layout.addLayout(logo_title_layout)
        header_layout.addStretch()
        
        
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
        """Create users table"""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Name", "Email", "Role", "Status", "Actions"])
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
            }
        """)
        
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        table.setColumnWidth(2, 120)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 220)
        
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        self.table = table
        layout.addWidget(table)
    
    def load_users_data(self):
        """Load users data from database"""
        if not self.db:
            return
        
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, email, name, role, is_active FROM users ORDER BY id')
            self.users = [
                {'id': row[0], 'email': row[1], 'name': row[2], 'role': row[3], 'is_active': row[4]}
                for row in cursor.fetchall()
            ]
    
    def load_users(self):
        """Load users from database and refresh table"""
        self.load_users_data()
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh table with current users without reloading from database"""
        # Reload from database first
        self.load_users_data()
        
        self.table.setRowCount(len(self.users))
        
        # Update info label
        if hasattr(self, 'info_label'):
            self.info_label.setText(f"Total users: {len(self.users)}. Manage user accounts and permissions.")
        
        for i, user in enumerate(self.users):
            # Name
            name_item = QTableWidgetItem(user['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, name_item)
            
            # Email
            email_item = QTableWidgetItem(user['email'])
            email_item.setFlags(email_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 1, email_item)
            
            # Role badge
            role_widget = QWidget()
            role_widget.setStyleSheet("background: transparent;")
            role_layout = QHBoxLayout(role_widget)
            role_layout.setContentsMargins(16, 0, 0, 0)
            
            role_colors = {'admin': '#7c3aed', 'client': '#2563eb', 'user': '#059669'}
            role_label = QLabel(user['role'].upper())
            role_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {role_colors.get(user['role'], '#6b7280')};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 11px;
                }}
            """)
            role_layout.addWidget(role_label)
            role_layout.addStretch()
            self.table.setCellWidget(i, 2, role_widget)
            
            # Status
            status_widget = QWidget()
            status_widget.setStyleSheet("background: transparent;")
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(16, 0, 0, 0)
            
            status_label = QLabel("● Active" if user['is_active'] else "● Inactive")
            status_label.setStyleSheet(f"""
                QLabel {{
                    color: {'#059669' if user['is_active'] else '#dc2626'};
                    font-weight: 600;
                    font-size: 12px;
                }}
            """)
            status_layout.addWidget(status_label)
            status_layout.addStretch()
            self.table.setCellWidget(i, 3, status_widget)
            
            # Actions
            actions_widget = QWidget()
            actions_widget.setStyleSheet("background: transparent;")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 16, 0)
            actions_layout.setSpacing(8)
            
            edit_btn = QPushButton("Edit Role")
            edit_btn.setFixedWidth(90)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #1d4ed8; }
            """)
            edit_btn.clicked.connect(lambda checked, idx=i: self.edit_user(idx))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc2626;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-weight: 600;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #b91c1c; }
            """)
            delete_btn.clicked.connect(lambda checked, idx=i: self.delete_user(idx))
            
            # Disable delete for client user
            if user['role'] == 'client':
                delete_btn.setEnabled(False)
                delete_btn.setToolTip("Client user cannot be deleted")
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            self.table.setCellWidget(i, 4, actions_widget)
            self.table.setRowHeight(i, 70)
    
    def add_user(self):
        """Show add user dialog"""
        dialog = AddUserDialog(self)
        if dialog.exec():
            user_data = dialog.get_user_data()
            if self.db:
                import sqlite3
                try:
                    with sqlite3.connect(self.db.db_path) as conn:
                        cursor = conn.cursor()
                        password_hash = self.db.ph.hash(user_data['password'])
                        cursor.execute('''
                            INSERT INTO users (email, name, password_hash, role, is_active)
                            VALUES (?, ?, ?, ?, 1)
                        ''', (user_data['email'], user_data['name'], password_hash, user_data['role']))
                        conn.commit()
                    
                    # Sync to backend PostgreSQL
                    try:
                        import requests
                        import bcrypt
                        # Use bcrypt for backend compatibility
                        bcrypt_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        response = requests.post(
                            "http://localhost:5000/api/internal/sync-user",
                            json={
                                "email": user_data['email'],
                                "name": user_data['name'],
                                "password_hash": bcrypt_hash,
                                "role": user_data['role']
                            },
                            headers={"Content-Type": "application/json"},
                            timeout=5
                        )
                        if response.status_code in [200, 201]:
                            print(f"✓ User synced to backend: {user_data['email']}")
                        else:
                            print(f"✗ Backend sync failed: {response.status_code} - {response.text}")
                    except requests.exceptions.ConnectionError:
                        print("✗ Backend not running - user only saved locally")
                    except Exception as e:
                        print(f"✗ Backend sync error: {e}")
                    
                    # Publish to MQTT for sync
                    if self.sync_service:
                        print(f" Publishing user create to MQTT: {user_data['email']}")
                        self.sync_service.publish_user_change('create', {
                            'email': user_data['email'],
                            'name': user_data['name'],
                            'password_hash': password_hash,
                            'role': user_data['role'],
                            'is_active': True
                        })
                    
                    msg = CustomMessageBox("Success", "User added successfully!")
                    msg.exec()
                    self.refresh_table()
                except sqlite3.IntegrityError:
                    msg = CustomMessageBox("Warning", "Email already exists")
                    msg.exec()
    
    def edit_user(self, index):
        """Edit user"""
        user = self.users[index]
        dialog = EditUserDialog(self, user)
        if dialog.exec():
            user_data = dialog.get_user_data()
            if self.db:
                import sqlite3
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE users SET role = ?
                        WHERE id = ?
                    ''', (user_data['role'], user['id']))
                    conn.commit()
                
                # Sync to backend
                try:
                    import requests
                    response = requests.put(
                        f"http://localhost:5000/api/internal/sync-user-role",
                        json={"email": user['email'], "role": user_data['role']},
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    if response.status_code == 200:
                        print(f"✓ User role synced to backend: {user['email']}")
                except:
                    print("✗ Backend sync failed for user role update")
                
                # Publish to MQTT for sync
                if self.sync_service:
                    self.sync_service.publish_user_change('update', {
                        'email': user['email'],
                        'name': user_data['name'],
                        'role': user_data['role'],
                        'is_active': user_data['is_active']
                    })
                
                msg = CustomMessageBox("Success", "User updated successfully")
                msg.exec()
                self.refresh_table()
    
    def delete_user(self, index):
        """Delete user"""
        user = self.users[index]
        
        if user['role'] == 'client':
            QMessageBox.warning(self, "Cannot Delete", "Client user cannot be deleted as it's required for telemetry data.")
            return
        
        # reply = QMessageBox.question(
        #     self, "Delete User",
        #     f"Are you sure you want to delete user '{user['name']}'?",
        #     QMessageBox.Yes | QMessageBox.No
        # )
        msg = CustomMessageBox1("Confirm Action", "Do you want to delete this user")
        result = msg.exec()  # Waits for user input

        if result == QDialog.Accepted:
           if self.db:
                import sqlite3
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM users WHERE id = ?', (user['id'],))
                    conn.commit()
                
                # Sync to backend
                try:
                    import requests
                    response = requests.delete(
                        f"http://localhost:5000/api/internal/sync-user-delete",
                        json={"email": user['email']},
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    if response.status_code == 200:
                        print(f"✓ User deleted from backend: {user['email']}")
                except:
                    print("✗ Backend sync failed for user deletion")
                
                # Publish to MQTT for sync
                if self.sync_service:
                    self.sync_service.publish_user_change('delete', {
                        'email': user['email'],
                        'name': user['name'],
                        'role': user['role']
                    })
                
                msg = CustomMessageBox("Success", "User deleted successfully")
                msg.exec()
                self.refresh_table()
        else:
            print("User clicked No")
        
        # if reply == QMessageBox.Yes:
        #     if self.db:
        #         import sqlite3
        #         with sqlite3.connect(self.db.db_path) as conn:
        #             cursor = conn.cursor()
        #             cursor.execute('DELETE FROM users WHERE id = ?', (user['id'],))
        #             conn.commit()
                
        #         # Publish to MQTT for sync
        #         if self.sync_service:
        #             self.sync_service.publish_user_change('delete', {
        #                 'email': user['email'],
        #                 'name': user['name'],
        #                 'role': user['role']
        #             })
                
        #         QMessageBox.information(self, "Success", "User deleted successfully!")
        #         self.load_users()


class AddUserDialog(QDialog):
    """Dialog for adding new user"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("")
        self.setModal(True)
        self.setFixedSize(600, 650)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container
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
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("Add New User")
        title.setStyleSheet("font-size: 28px; font-weight: 700; color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Create a new user account with role and permissions")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Name
        name_label = QLabel("Full Name")
        name_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600; margin-top: 5px;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter full name")
        self.name_input.setFixedHeight(50)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 16px;
                color: white;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        
        # Email
        email_label = QLabel("Email Address")
        email_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600; margin-top: 5px;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")
        self.email_input.setFixedHeight(50)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 16px;
                color: white;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        self.name_input.returnPressed.connect(self.email_input.setFocus)
        
        
        
        # Password
        password_label = QLabel("Password")
        password_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600; margin-top: 5px;")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setFixedHeight(50)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 16px;
                color: white;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        self.email_input.returnPressed.connect(self.password_input.setFocus)
        
        
        # Role
        role_label = QLabel("User Role")
        role_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600; margin-top: 5px;")
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "client", "admin"])
        self.role_combo.setFixedHeight(50)
        self.role_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 16px;
                color: white;
                font-size: 15px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: white;
                selection-background-color: #3b82f6;
            }
        """)
        self.password_input.returnPressed.connect(self.role_combo.setFocus)
        
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(role_label)
        layout.addWidget(self.role_combo)
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        add_btn = QPushButton("Add User")
        add_btn.setFixedHeight(50)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        add_btn.clicked.connect(self.validate_and_accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(50)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #4b5563;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #374151; }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        main_layout.addWidget(container)
    
    def validate_and_accept(self):
        """Validate all fields before accepting"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Full Name is required!")
            return
        
        if not self.email_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Email Address is required!")
            return
        
        if '@' not in self.email_input.text():
            QMessageBox.warning(self, "Validation Error", "Please enter a valid email address!")
            return
        
        if not self.password_input.text():
            QMessageBox.warning(self, "Validation Error", "Password is required!")
            return
        
        if len(self.password_input.text()) < 6:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 6 characters!")
            return
        
        self.accept()
    
    def get_user_data(self):
        """Get user data from form"""
        return {
            'name': self.name_input.text().strip(),
            'email': self.email_input.text().strip(),
            'password': self.password_input.text(),
            'role': self.role_combo.currentText()
        }


class EditUserDialog(QDialog):
    """Dialog for editing user role"""
    
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("")
        self.setModal(True)
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container
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
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("Edit User Role")
        title.setStyleSheet("font-size: 28px; font-weight: 700; color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Update the role for this user account")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Name (read-only)
        name_label = QLabel("Full Name")
        name_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600; margin-top: 5px;")
        self.name_input = QLineEdit(self.user['name'])
        self.name_input.setReadOnly(True)
        self.name_input.setFixedHeight(50)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 16px;
                color: #9ca3af;
                font-size: 15px;
            }
        """)
        
        # Email (read-only)
        email_label = QLabel("Email Address")
        email_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600; margin-top: 5px;")
        self.email_input = QLineEdit(self.user['email'])
        self.email_input.setReadOnly(True)
        self.email_input.setFixedHeight(50)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 16px;
                color: #9ca3af;
                font-size: 15px;
            }
        """)
        
        # Role
        role_label = QLabel("User Role")
        role_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600; margin-top: 5px;")
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        self.role_combo.setCurrentText(self.user['role'])
        self.role_combo.setFixedHeight(50)
        self.role_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 16px;
                color: white;
                font-size: 15px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: white;
                selection-background-color: #3b82f6;
            }
        """)
        
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(role_label)
        layout.addWidget(self.role_combo)
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setFixedHeight(50)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(50)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #4b5563;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #374151; }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        main_layout.addWidget(container)
    
    def get_user_data(self):
        """Get user data from form"""
        return {
            'name': self.user['name'],
            'role': self.role_combo.currentText(),
            'is_active': self.user['is_active']
        }
