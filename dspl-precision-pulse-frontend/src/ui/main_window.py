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
from src.services.mqtt_service import MQTTService
from src.services.mqtt_factory import MQTTClientFactory
from src.services.mqtt_broker import MQTTBroker
from src.services.telemetry_service import TelemetryService
from src.services.sync_service import SyncService
from src.services.parameter_sync_service import ParameterSyncService
from src.core.database import DatabaseManager
from src.core.router import Router
from src.core.auth_service import AuthService
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
        from src.services.parameter_sync_service import ParameterSyncService
        self.parameter_sync_service = ParameterSyncService()
        
        self.telemetry_service = TelemetryService(self.mqtt_service, self.db, self.parameter_sync_service)
        self.sync_service = SyncService(self.mqtt_service, self.db)
        
        # Remove embedded MQTT broker - connect to backend instead
        
        # Connect telemetry service signals
        self.telemetry_service.connection_status_changed.connect(self.update_connection_status)
        self.telemetry_service.buffered_data_synced.connect(self._on_buffered_data_synced)
        
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
        self.parameters_page = ParametersPage(self.db, self.auth_service, self.sync_service)
        self.parameters_page.back_clicked.connect(lambda: self.router.navigate('dashboard'))
        self.parameters_page.parameters_changed.connect(self.on_parameters_changed)
        
        # Profile page
        self.profile_page = ProfilePage(self.auth_service.get_current_user())
        self.profile_page.back_clicked.connect(lambda: self.router.navigate('dashboard'))
        
        # Manage Users page (admin only)
        self.manage_users_page = ManageUsersPage(self.db, self.auth_service, self.sync_service)
        self.manage_users_page.back_clicked.connect(lambda: self.router.navigate('dashboard'))
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(dashboard_widget)
        self.stacked_widget.addWidget(self.parameters_page)
        self.stacked_widget.addWidget(self.profile_page)
        self.stacked_widget.addWidget(self.manage_users_page)
    
    def setup_routes(self):
        """Setup application routes"""
        self.router.register_route('dashboard', lambda: self.stacked_widget.widget(0), requires_auth=True)
        self.router.register_route('parameters', lambda: self.stacked_widget.widget(1), requires_auth=True)
        self.router.register_route('profile', lambda: self.stacked_widget.widget(2), requires_auth=True)
        self.router.register_route('manage_users', lambda: self.stacked_widget.widget(3), requires_auth=True, allowed_roles=['admin'])
        
        # Set initial route
        self.router.navigate('dashboard')
    
    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(90)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #e5e7eb;
                border: none;
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
                    background-color: #2563eb;
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
                color: #1e293b;
                font-size: 22px;
                font-weight: 700;
                background: transparent;
            }
        """)
        
        subtitle_label = QLabel("Real-time Telemetry")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #64748b;
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
        
        # Manage Users button (admin only)
        if current_user and current_user.get('role') == 'admin':
            users_btn = QPushButton("Manage Users")
            users_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7c3aed;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #6d28d9; }
            """)
            users_btn.clicked.connect(lambda: self.router.navigate('manage_users'))
            self.header_btn_layout.addWidget(users_btn)
        
        # Parameters button (admin and client only - users cannot access)
        if current_user and current_user.get('role') in ['admin', 'client']:
            parameters_btn = QPushButton("Parameters")
            parameters_btn.setStyleSheet("""
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
            parameters_btn.clicked.connect(lambda: self.router.navigate('parameters'))
            
            # Check if user has parameters write permission
            if self.db and not self.db.check_permission(current_user['role'], 'parameters', 'write'):
                # User can only view parameters, not edit
                parameters_btn.setText("View Parameters")
            
            self.header_btn_layout.addWidget(parameters_btn)
        
        profile_btn = QPushButton("Profile")
        profile_btn.setStyleSheet("""
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
        profile_btn.clicked.connect(lambda: self.router.navigate('profile'))
        
        self.connected_label = QPushButton("● Connected")
        self.connected_label.setEnabled(False)
        self.connected_label.setStyleSheet("""
            QPushButton {
                background-color: rgba(5, 150, 105, 0.15);
                color: #059669;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
        """)
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #dc2626;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #fee2e2; }
        """)
        logout_btn.clicked.connect(self.logout)
        
        self.header_btn_layout.addWidget(profile_btn)
        self.header_btn_layout.addWidget(self.connected_label)
        self.header_btn_layout.addWidget(logout_btn)
    
    def setup_style(self):
        """Setup application styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e293b;
            }
        """)
    

    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog(self)
        result = login_dialog.exec()  # Dialog stays open until success or user cancels

        if result == QDialog.DialogCode.Accepted:
            return True

    # Dialog was closed without successful login
        return False
    
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
            'manage_users': 3
        }
        
        if route_name in route_map:
            self.stacked_widget.setCurrentIndex(route_map[route_name])
            
            # Update profile page data if navigating to profile
            if route_name == 'profile':
                self.profile_page.set_user_data(self.auth_service.get_current_user())
            # Reload users if navigating to manage users
            elif route_name == 'manage_users':
                self.manage_users_page.load_users()
    
    def on_user_logged_in(self, user: dict):
        """Handle user login - start telemetry"""
        self.router.set_user(user)
        
        print(f"🔗 Starting MQTT connection for user: {user.get('name')}")
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
        QMessageBox.warning(self, "Session Expired", "Your session has expired. Please login again.")
        self.on_user_logged_out()
    
    def on_unauthorized_access(self):
        QMessageBox.warning(self, "Access Denied", "You don't have permission to access this page.")
    
    def logout(self):
        self.auth_service.logout()
    
    def update_connection_status(self, connected: bool):
        if hasattr(self, 'connected_label'):
            if connected:
                self.connected_label.setText("● Connected")
                self.connected_label.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(5, 150, 105, 0.15);
                        color: #059669;
                        border: none;
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
                        color: #dc2626;
                        border: none;
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
            print(f"🔄 Parameter synced: {parameter.get('name', 'unknown')}")
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
        # Stop parameter refresh timer
        if hasattr(self, 'parameter_refresh_timer'):
            self.parameter_refresh_timer.stop()
        event.accept()
