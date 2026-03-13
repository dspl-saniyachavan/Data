"""
Main window for PrecisionPulse Desktop Application
"""

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFrame, QStackedWidget, QMessageBox)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap
from src.ui.login_dialog import LoginDialog
from src.ui.telemetry_widget import TelemetryWidget
from src.ui.parameters_page import ParametersPage
from src.ui.profile_page import ProfilePage
from src.ui.manage_users_page import ManageUsersPage
from src.ui.sync_status_widget import SyncStatusWidget
from src.ui.modern_datetime_widget import ModernDateTimeWidget
from src.ui.historical_data_widget import HistoricalDataWidget
from src.services.mqtt_service import MQTTService
from src.services.mqtt_factory import MQTTClientFactory
from src.services.mqtt_broker import MQTTBroker
from src.services.telemetry_service import TelemetryService
from src.services.sync_service import SyncService
from src.services.parameter_sync_service import ParameterSyncService
from src.services.user_sync_service import UserSyncService
from src.core.database import DatabaseManager
from src.core.router import Router
from src.core.auth_service import AuthService
from src.core.rbac import RoleBasedAccessControl
import uuid
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QDialog

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.device_id = str(uuid.uuid4())
        self.header_btn_layout = None  # Store reference to button layout
        
        # Initialize database
        self.db = DatabaseManager()
        self.db.initialize_database()
        
        # Initialize auth service
        self.auth_service = AuthService(self.db)
        self.auth_service.user_logged_in.connect(self.on_user_logged_in)
        self.auth_service.user_logged_out.connect(self.on_user_logged_out)
        self.auth_service.session_expired.connect(self.on_session_expired)
        
        # Initialize router
        self.router = Router()
        self.router.route_changed.connect(self.on_route_changed)
        self.router.unauthorized_access.connect(self.on_unauthorized_access)
        
        # Initialize services (connect to backend MQTT broker)
        mqtt_client = MQTTClientFactory.create_client(self.device_id)
        self.mqtt_service = MQTTService(self.device_id, mqtt_client)
        
        # Import parameter sync service
        self.parameter_sync_service = ParameterSyncService(mqtt_service=self.mqtt_service)
        self.mqtt_service.message_received.connect(self.parameter_sync_service._on_mqtt_message)
        self.parameter_sync_service.parameter_updated.connect(self._on_parameter_synced)
        
        # Import user sync service
        self.user_sync_service = UserSyncService(mqtt_service=self.mqtt_service)
        self.mqtt_service.message_received.connect(self.user_sync_service._on_mqtt_message)
        
        self.telemetry_service = TelemetryService(self.mqtt_service, self.db, self.parameter_sync_service)
        self.sync_service = SyncService(self.mqtt_service, self.db)
        
        # Connect user sync service signals
        self.user_sync_service.user_created.connect(self._on_user_created)
        self.user_sync_service.user_updated.connect(self._on_user_updated)
        self.user_sync_service.user_deleted.connect(self._on_user_deleted)
        self.user_sync_service.role_changed.connect(self._on_role_changed)
        
        # Connect telemetry service signals
        self.telemetry_service.connection_status_changed.connect(self._on_telemetry_status_changed)
        self.telemetry_service.buffered_data_synced.connect(self._on_buffered_data_synced)
        
        # Also connect MQTT service signals directly for immediate updates
        self.mqtt_service.connected.connect(lambda: self.update_connection_status(True))
        self.mqtt_service.disconnected.connect(lambda: self.update_connection_status(False))
        
        # Connect sync service signals
        self.sync_service.user_synced.connect(self._on_user_synced)
        self.sync_service.parameter_synced.connect(self._on_parameter_synced)
        
        # Setup parameter refresh timer
        from PySide6.QtCore import QTimer
        self.parameter_refresh_timer = QTimer()
        self.parameter_refresh_timer.timeout.connect(self._refresh_parameters)
        self.parameter_refresh_timer.start(10000)  # Refresh every 10 seconds
        
        # Show login first
        if not self.show_login():
            import sys
            sys.exit(0)
        
        # Setup UI after successful login
        self.setup_ui()
        self.setup_routes()
        self.setup_style()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("PrecisionPulse Desktop")
        
        # Responsive window sizing
        screen = self.screen().availableGeometry()
        if screen.width() < 1200:
            self.resize(int(screen.width() * 0.95), int(screen.height() * 0.95))
        else:
            self.resize(int(screen.width() * 0.9), int(screen.height() * 0.9))
        
        # Center window
        self.move(screen.center() - self.rect().center())
        
        # Central widget with stacked layout
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Dashboard page
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_layout.setSpacing(0)
        self.create_header(dashboard_layout)
        self.telemetry_widget = TelemetryWidget(self.telemetry_service, self.auth_service)
        dashboard_layout.addWidget(self.telemetry_widget)
        
        # Parameters page
        self.parameters_page = ParametersPage(self.db, self.auth_service, self.sync_service, self.parameter_sync_service)
        self.parameters_page.back_clicked.connect(lambda: self.router.navigate('dashboard'))
        self.parameters_page.parameters_changed.connect(self.on_parameters_changed)
        
        # Profile page
        self.profile_page = ProfilePage(self.auth_service.get_current_user())
        self.profile_page.back_clicked.connect(lambda: self.router.navigate('dashboard'))
        
        # Manage Users page (admin only)
        self.manage_users_page = ManageUsersPage(self.db, self.auth_service, self.sync_service)
        self.manage_users_page.back_clicked.connect(lambda: self.router.navigate('dashboard'))
        
        # Historical Data page
        self.history_page = HistoricalDataWidget(self.db)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(dashboard_widget)
        self.stacked_widget.addWidget(self.parameters_page)
        self.stacked_widget.addWidget(self.profile_page)
        self.stacked_widget.addWidget(self.manage_users_page)
        self.stacked_widget.addWidget(self.history_page)
    
    def setup_routes(self):
        """Setup application routes"""
        self.router.register_route('dashboard', lambda: self.stacked_widget.widget(0), requires_auth=True)
        self.router.register_route('parameters', lambda: self.stacked_widget.widget(1), requires_auth=True)
        self.router.register_route('profile', lambda: self.stacked_widget.widget(2), requires_auth=True)
        self.router.register_route('manage_users', lambda: self.stacked_widget.widget(3), requires_auth=True, allowed_roles=['admin'])
        self.router.register_route('history', lambda: self.stacked_widget.widget(4), requires_auth=True)
        
        # Set initial route
        self.router.navigate('dashboard')
    
    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(90)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1f3a, stop:1 #0f172a);
                border: none;
                border-bottom: 1px solid rgba(99, 102, 241, 0.2);
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        # Responsive margins
        margin = 15 if self.width() < 1200 else 30
        header_layout.setContentsMargins(margin, 0, margin, 0)
        
        # Logo and title
        logo_title_layout = QHBoxLayout()
        logo_title_layout.setSpacing(15)
        
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
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ec4899, stop:1 #06b6d4);
                    color: white;
                    font-size: 28px;
                    border-radius: 12px;
                    padding: 8px;
                }
            """)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(50, 50)
        
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
        
        subtitle_label = QLabel("Real-time Telemetry")
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
        
        # Modern DateTime widget
        self.datetime_widget = ModernDateTimeWidget()
        header_layout.addWidget(self.datetime_widget)
        header_layout.addStretch()
        
        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        self.header_btn_layout = btn_layout  # Store reference
        
        # Create buttons based on current user
        self.update_header_buttons()
        
        header_layout.addLayout(btn_layout)
        layout.addWidget(header_frame)
    
    def update_header_buttons(self):
        """Update header buttons based on current user role"""
        if not self.header_btn_layout:
            return
        
        # Clear existing buttons
        while self.header_btn_layout.count():
            item = self.header_btn_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get current user
        current_user = self.auth_service.get_current_user() if self.auth_service else None
        if not current_user:
            return
        
        user_role = current_user.get('role', 'user')
        
        # Manage Users button (admin only)
        if RoleBasedAccessControl.is_visible(user_role, 'manage_users_button'):
            users_btn = QPushButton("Manage Users")
            users_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ec4899, stop:1 #a855f7);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #db2777, stop:1 #9333ea);
                }
            """)
            users_btn.clicked.connect(lambda: self.router.navigate('manage_users'))
            self.header_btn_layout.addWidget(users_btn)
        
        # Parameters button (admin and client only)
        if RoleBasedAccessControl.is_visible(user_role, 'parameters_button'):
            parameters_btn = QPushButton("Parameters")
            parameters_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #06b6d4, stop:1 #0891b2);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #0891b2, stop:1 #0e7490);
                }
            """)
            parameters_btn.clicked.connect(lambda: self.router.navigate('parameters'))
            self.header_btn_layout.addWidget(parameters_btn)
        
        # History button (always visible)
        history_btn = QPushButton("History")
        history_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7c3aed, stop:1 #6d28d9);
            }
        """)
        history_btn.clicked.connect(lambda: self.router.navigate('history'))
        self.header_btn_layout.addWidget(history_btn)
        
        # Profile button (always visible)
        profile_btn = QPushButton("Profile")
        profile_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
        """)
        profile_btn.clicked.connect(lambda: self.router.navigate('profile'))
        self.header_btn_layout.addWidget(profile_btn)
        
        # Connection status
        self.connected_label = QPushButton("● Disconnected")
        self.connected_label.setEnabled(False)
        self.connected_label.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 38, 38, 0.15);
                color: #fca5a5;
                border: 1px solid rgba(220, 38, 38, 0.3);
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
        """)
        self.header_btn_layout.addWidget(self.connected_label)
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """)
        logout_btn.clicked.connect(self.logout)
        self.header_btn_layout.addWidget(logout_btn)
    
    def setup_style(self):
        """Setup application styling"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a, stop:0.5 #1a1f3a, stop:1 #0f172a);
            }
        """)
    
    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog(self)
        result = login_dialog.exec()
        return result == QDialog.DialogCode.Accepted
    
    def show_error(self, title: str, message: str):
        error_text = f"<b style='color: #dc2626; font-size: 19px;'>✖ {title}</b><br/><span style='color: #991b1b; font-size: 18px;'>{message.replace(chr(10), '<br/>')}</span>"
        self.error_label.setText(error_text)
        self.error_label.setTextFormat(Qt.RichText)
        self.error_label.adjustSize()
        self.error_label.show()
    
    def show_login_error(self, title, message):
        """Show an error message box for failed login"""
        error_message = QMessageBox(self)
        error_message.setIcon(QMessageBox.Critical)  # Critical icon for error
        error_message.setWindowTitle(title)  # Set the title of the message box
        error_message.setText(message)  # Set the error message text
        error_message.setStandardButtons(QMessageBox.Ok)  # Only "Ok" button
        error_message.exec()  # Show the message box
    
    def on_route_changed(self, route_name: str):
        """Handle route changes"""
        route_map = {
            'dashboard': 0,
            'parameters': 1,
            'profile': 2,
            'manage_users': 3,
            'history': 4
        }
        
        if route_name in route_map:
            self.stacked_widget.setCurrentIndex(route_map[route_name])
            
            # Update profile page data if navigating to profile
            if route_name == 'profile':
                self.profile_page.set_user_data(self.auth_service.get_current_user())
            # Reload users if navigating to manage users
            elif route_name == 'manage_users':
                self.manage_users_page.load_users()
            # Refresh history data if navigating to history
            elif route_name == 'history':
                self.history_page.load_parameters()
    
    def on_user_logged_in(self, user: dict):
        """Handle user login - start telemetry"""
        self.router.set_user(user)
        
        print(f" Starting MQTT connection for user: {user.get('name')}")
        self.mqtt_service.connect()
        self.telemetry_service.start_streaming(3)
    
    def _start_telemetry(self):
        """Start telemetry after broker is ready"""
        self.telemetry_service.start_streaming(3)
        self.update_connection_status(True)
    
    def on_user_logged_out(self):
        """Handle user logout - stop telemetry"""
        self.router.set_user(None)
        
        # Stop telemetry streaming
        self.telemetry_service.stop_streaming()
        
        # Close current window
        self.close()
        
        # Show login and create new window if successful
        if self.show_login():
            # Recreate UI with new user
            self.setup_ui()
            self.setup_routes()
            self.show()
        else:
            import sys
            sys.exit(0)
    
    def on_session_expired(self):
        """Handle session expiration"""
        QMessageBox.warning(self, "Session Expired", "Your session has expired. Please login again.")
        self.on_user_logged_out()
    
    def on_unauthorized_access(self):
        """Handle unauthorized access attempt"""
        QMessageBox.warning(self, "Access Denied", "You don't have permission to access this page.")
    
    def logout(self):
        """Handle user logout"""
        self.auth_service.logout()
    
    def _on_telemetry_status_changed(self, connected: bool):
        """Handle telemetry status change"""
        self.update_connection_status(connected)
    
    def update_connection_status(self, connected: bool):
        """Update connection status indicator"""
        print(f"[UI] update_connection_status called with: {connected}")
        if hasattr(self, 'connected_label'):
            if connected:
                self.connected_label.setText("● Connected")
                self.connected_label.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(5, 150, 105, 0.15);
                        color: #86efac;
                        border: 1px solid rgba(5, 150, 105, 0.3);
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-weight: 600;
                        font-size: 14px;
                    }
                """)
            else:
                self.connected_label.setText("● Disconnected")
                self.connected_label.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(220, 38, 38, 0.15);
                        color: #fca5a5;
                        border: 1px solid rgba(220, 38, 38, 0.3);
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-weight: 600;
                        font-size: 14px;
                    }
                """)
    
    @Slot(int)
    def _on_buffered_data_synced(self, count: int):
        """Handle buffered data sync completion"""
        pass
    
    @Slot()
    def on_parameters_changed(self):
        """Handle parameters configuration change"""
        # Refresh telemetry widget to show only enabled parameters
        if hasattr(self, 'telemetry_widget'):
            self.telemetry_widget.refresh_parameters()
    
    @Slot(dict)
    def _on_user_synced(self, user):
        """Handle user sync from remote"""
        # Reload users in manage users page if visible
        if self.router.get_current_route() == 'manage_users':
            self.manage_users_page.load_users()
    
    @Slot(dict)
    def _on_parameter_synced(self, parameter):
        """Handle parameter sync from remote - runs in main thread"""
        try:
            print(f" Parameter synced: {parameter.get('name', 'unknown')}")
            # Refresh telemetry service parameters
            if hasattr(self, 'telemetry_service'):
                self.telemetry_service.refresh_parameters()
            # Refresh telemetry widget immediately
            if hasattr(self, 'telemetry_widget'):
                self.telemetry_widget.refresh_parameters()
            # Don't refresh parameters page here - it handles its own refresh
        except Exception as e:
            print(f"Error handling parameter sync: {e}")
    
    def _on_broker_started(self):
        """Handle broker startup"""
        pass
    
    def _on_broker_error(self, error: str):
        """Handle broker errors"""
        pass
    
    def _refresh_parameters(self):
        """Refresh parameters from backend and update dashboard"""
        if hasattr(self, 'telemetry_widget'):
            self.telemetry_widget.refresh_parameters()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'parameter_refresh_timer'):
            self.parameter_refresh_timer.stop()
        event.accept()
    
    def _on_user_created(self, user: dict):
        """Handle user created event"""
        print(f"[UI] User created: {user.get('email')}")
        if self.router.get_current_route() == 'manage_users':
            self.manage_users_page.load_users()
    
    def _on_user_updated(self, user: dict):
        """Handle user updated event"""
        print(f"[UI] User updated: {user.get('email')}")
        if self.router.get_current_route() == 'manage_users':
            self.manage_users_page.load_users()
    
    def _on_user_deleted(self, user_id: int, email: str):
        """Handle user deleted event"""
        print(f"[UI] User deleted: {email}")
        if self.router.get_current_route() == 'manage_users':
            self.manage_users_page.load_users()
    
    def _on_role_changed(self, user_id: int, email: str, old_role: str, new_role: str):
        """Handle role changed event"""
        print(f"[UI] Role changed for {email}: {old_role} -> {new_role}")
        if self.router.get_current_route() == 'manage_users':
            self.manage_users_page.load_users()
