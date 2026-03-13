"""
User profile page with password synchronization
"""

import os
import sqlite3
import logging
import time
from argon2 import PasswordHasher
import bcrypt
from PySide6.QtWidgets import QMessageBox
    
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QScrollArea)
from PySide6.QtCore import Qt, Signal
from argon2 import PasswordHasher
from PySide6.QtGui import QPixmap

from src.ui.CustomMessageBox import CustomMessageBox

logger = logging.getLogger(__name__)
ph = PasswordHasher()

class ProfilePage(QWidget):
    """User profile page widget"""
    
    back_clicked = Signal()
    
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data
    
    def setup_ui(self):
        """Setup profile UI"""
        self.setStyleSheet("background-color: #1e293b;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.create_header(layout)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: #1e293b; 
            }
            QScrollBar:vertical { 
                background: #334155; 
                width: 10px; 
                border-radius: 5px; 
            }
            QScrollBar::handle:vertical { 
                background: #475569; 
                border-radius: 5px; 
            }
            QScrollBar::handle:vertical:hover { 
                background: #64748b; 
            }
        """)
        
        # Content widget
        content = QWidget()
        content.setStyleSheet("background-color: #1e293b;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 40, 0, 40)
        content_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # Profile Information Card
        profile_card = self.create_profile_card()
        content_layout.addWidget(profile_card)
        content_layout.addSpacing(24)
        
        # Change Password Card
        password_card = self.create_password_card()
        content_layout.addWidget(password_card)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def create_header(self, layout):
        """Create header with back button"""
        header = QFrame()
        header.setFixedHeight(90)
        header.setStyleSheet("background-color: #334155; border: none;")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo and title
        logo_title = QHBoxLayout()
        logo_title.setSpacing(15)
        
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
        
        title = QLabel("PrecisionPulse")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: 700; background: transparent;")
        
        subtitle = QLabel("Profile")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        logo_title.addWidget(logo)
        logo_title.addLayout(title_layout)
        
        header_layout.addLayout(logo_title)
        header_layout.addStretch()
        
        # Back button
        back_btn = QPushButton("Back to Dashboard")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        
        header_layout.addWidget(back_btn)
        layout.addWidget(header)
    
    def create_profile_card(self):
        """Create profile information card"""
        card = QFrame()
        card.setFixedWidth(640)
        card.setStyleSheet("""
            QFrame {
                background-color: #334155;
                border-radius: 16px;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # Title
        title = QLabel("Profile Information")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: 700; background: transparent;")
        layout.addWidget(title)
        
        # Name
        name_label = QLabel("Name")
        name_label.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: 500; background: transparent;")
        
        name_value = QLabel(self.user_data.get('name', 'Admin User'))
        name_value.setStyleSheet("color: white; font-size: 18px; font-weight: 500; background: transparent;")
        
        layout.addWidget(name_label)
        layout.addWidget(name_value)
        
        # Email
        email_label = QLabel("Email")
        email_label.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: 500; background: transparent;")
        
        email_value = QLabel(self.user_data.get('email', 'admin@precisionpulse.com'))
        email_value.setStyleSheet("color: white; font-size: 18px; font-weight: 500; background: transparent;")
        
        layout.addWidget(email_label)
        layout.addWidget(email_value)
        
        # Role
        role_label = QLabel("Role")
        role_label.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: 500; background: transparent;")
        layout.addWidget(role_label)
        
        role_badge = QLabel(self.user_data.get('role', 'ADMIN').upper())
        role_badge.setStyleSheet("""
            background-color: #7c3aed;
            color: white;
            font-size: 12px;
            font-weight: 700;
            padding: 6px 16px;
            border-radius: 6px;
        """)
        role_badge.setFixedWidth(80)
        layout.addWidget(role_badge)
        
        return card
    
    def create_password_card(self):
        """Create change password card"""
        card = QFrame()
        card.setFixedWidth(640)
        card.setStyleSheet("""
            QFrame {
                background-color: #334155;
                border-radius: 16px;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # Title
        title = QLabel("Change Password")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: 700; background: transparent;")
        layout.addWidget(title)
        
        # Current Password
        current_label = QLabel("Current Password")
        current_label.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: 500; background: transparent;")
        layout.addWidget(current_label)
        
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.Password)
        self.current_password.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 16px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.current_password)
        
        # New Password
        new_label = QLabel("New Password")
        new_label.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: 500; background: transparent;")
        layout.addWidget(new_label)
        
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 16px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.new_password)
        
        # Confirm Password
        confirm_label = QLabel("Confirm New Password")
        confirm_label.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: 500; background: transparent;")
        layout.addWidget(confirm_label)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 16px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.confirm_password)
        
        # Update button
        update_btn = QPushButton("Update Password")
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px;
                font-weight: 600;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        update_btn.clicked.connect(self.update_password)
        layout.addWidget(update_btn)
        
        return card
    
    def update_password(self):
        """Update password with synchronization to backend"""
        current_password = self.current_password.text().strip()
        new_password = self.new_password.text().strip()
        confirm_password = self.confirm_password.text().strip()

        # Validation
        if not current_password:
            msg = CustomMessageBox("Warning", "The current password cannot be empty")
            msg.exec()
            return
    
        if not new_password:
            msg = CustomMessageBox("Warning", "The new password cannot be empty")
            msg.exec()
            return
        
        if not confirm_password:
            msg = CustomMessageBox("Warning", "Confirm password cannot be empty.")
            msg.exec()
            return
        
        if current_password == new_password:
            msg = CustomMessageBox("Warning", "New password is same as current.")
            msg.exec()
            return
        
        if new_password != confirm_password:
            msg = CustomMessageBox("Warning", "New password not matches the confirm password.")
            msg.exec()
            return

        db_path = "data/precision_pulse.db" 
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT password_hash FROM users WHERE email=?",
                (self.user_data.get('email'),)
            )
            row = cursor.fetchone()

            if not row:
                msg = CustomMessageBox("Error", "user not found in database")
                msg.exec()
                return

            stored_hash = row[0]

            # Support both bcrypt and argon2 password verification
            try:
                if stored_hash.startswith('$2b$'):
                    # bcrypt hash (from web app)
                    if not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash.encode('utf-8')):
                        msg = CustomMessageBox("Error", "Current password is incorrect")
                        msg.exec()
                        return
                else:
                    # argon2 hash (local)
                    ph.verify(stored_hash, current_password)
            except Exception as e:
                logger.error(f"[PASSWORD] Password verification failed: {e}")
                msg = CustomMessageBox("Error", "Current password is incorrect")
                msg.exec()
                return

            # Update local SQLite database with bcrypt hash for compatibility
            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "UPDATE users SET password_hash=?, updated_at=CURRENT_TIMESTAMP WHERE email=?",
                (new_hash, self.user_data.get('email'))
            )
            conn.commit()
            
            logger.info(f"[PASSWORD] Password updated locally for {self.user_data.get('email')}")
            
            # Sync to PostgreSQL backend with retry logic
            sync_success = self._sync_password_to_backend(new_hash)
            
            if sync_success:
                msg = CustomMessageBox("Success", "Password updated and synchronized successfully!")
                msg.exec()
            else:
                msg = CustomMessageBox(
                    "Warning",
                    "Password updated locally but failed to sync to backend.\nPlease try again or contact support."
                )
                msg.exec()
            
            # Clear fields
            self.current_password.clear()
            self.new_password.clear()
            self.confirm_password.clear()

        except Exception as e:
            logger.error(f"[PASSWORD] Error updating password: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
        finally:
            conn.close()
    
    def _sync_password_to_backend(self, password_hash):
        """Sync password to backend with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                import requests
                
                response = requests.post(
                    "http://localhost:5000/api/internal/sync-user-password",
                    json={
                        "email": self.user_data.get('email'),
                        "password_hash": password_hash
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.info(f"[PASSWORD] Backend sync successful for {self.user_data.get('email')}")
                    return True
                else:
                    retry_count += 1
                    logger.warning(f"[PASSWORD] Backend sync failed (attempt {retry_count}/{max_retries}): {response.status_code}")
                    if retry_count < max_retries:
                        time.sleep(1)
            
            except requests.exceptions.Timeout:
                retry_count += 1
                logger.warning(f"[PASSWORD] Backend sync timeout (attempt {retry_count}/{max_retries})")
                if retry_count < max_retries:
                    time.sleep(1)
            
            except Exception as e:
                retry_count += 1
                logger.error(f"[PASSWORD] Backend sync error (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    time.sleep(1)
        
        logger.error(f"[PASSWORD] Failed to sync password to backend after {max_retries} attempts")
        return False
    
    def set_user_data(self, user_data):
        """Set user data and setup UI"""
        self.user_data = user_data
        self.setup_ui()
