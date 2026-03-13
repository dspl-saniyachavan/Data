from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO
from flasgger import Swagger
from config.config import Config
from app.models import db
from app.models.user import User
from app.models.parameter import Parameter
from app.models.telemetry import Telemetry
from app.models.telemetry_buffer import TelemetryBuffer
from app.models.parameter_stream import ParameterStream
from app.models.system_config import SystemConfig
from app.routes.auth_routes import auth_bp
from app.routes.user_routes import user_bp
from app.routes.parameter_routes import parameter_bp
from app.routes.sync_routes import sync_bp
from app.routes.internal_routes import internal_bp
from app.routes.telemetry_routes import telemetry_bp
from app.routes.buffer_routes import buffer_bp
from app.routes.parameter_stream_routes import parameter_stream_bp
from app.routes.mqtt_bridge_routes import mqtt_bridge_bp
from app.routes.remote_commands_routes import remote_commands_bp
from app.routes.mqtt_status_routes import mqtt_status_bp
from app.routes.config_routes import config_bp
from app.routes.audit_log_routes import audit_log_bp
from app.routes.report_routes import report_bp
from app.services.data_freshness_monitor import DataFreshnessMonitor
import asyncio
import threading
import logging
import time

logger = logging.getLogger(__name__)

socketio = None

def create_app():
    global socketio
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Configure CORS for both Flask and Socket.IO
    CORS(app, 
        origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Authorization"],
        supports_credentials=True,
        max_age=3600
    )
    
    # Initialize Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "PrecisionPulse API",
            "description": "API documentation for PrecisionPulse backend",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
            }
        },
        "security": [
            {"Bearer": []}
        ]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Initialize Socket.IO with proper CORS
    socketio = SocketIO(
        app,
        cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"],
        async_mode='threading',
        ping_timeout=60,
        ping_interval=25,
        logger=True,
        engineio_logger=True,
        transports=['websocket', 'polling']
    )
    
    # Store socketio in app for access in routes
    app.socketio = socketio
    
    # Initialize data freshness monitor with 3-second threshold
    data_freshness_monitor = DataFreshnessMonitor(socketio, stale_threshold_seconds=3)
    app.data_freshness_monitor = data_freshness_monitor
    logger.info("Data freshness monitor initialized with 3-second threshold")
    
    with app.app_context():
        db.create_all()
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(parameter_bp)
    app.register_blueprint(sync_bp)
    app.register_blueprint(internal_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(buffer_bp)
    app.register_blueprint(parameter_stream_bp)
    app.register_blueprint(mqtt_bridge_bp)
    app.register_blueprint(remote_commands_bp)
    app.register_blueprint(mqtt_status_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(audit_log_bp)
    app.register_blueprint(report_bp)
    
    # Socket.IO event handlers
    @socketio.on('connect')
    def handle_connect():
        client_id = request.sid
        logger.info(f"[SOCKETIO] Client connected: {client_id}")
        socketio.emit('connection_response', {'data': 'Connected to server', 'sid': client_id}, room=client_id)
        
        # Send current MQTT status to newly connected client
        try:
            from app.services.mqtt_publisher import get_mqtt_publisher
            publisher = get_mqtt_publisher()
            status = 'online' if publisher.connected else 'offline'
            logger.info(f"[SOCKETIO] Sending MQTT status to new client {client_id}: {status}")
            socketio.emit('mqtt_status', {'status': status}, room=client_id)
            logger.info(f"[SOCKETIO] Sent MQTT status to client {client_id}")
        except Exception as e:
            logger.error(f"[SOCKETIO] Error sending MQTT status: {e}")
            import traceback
            traceback.print_exc()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        client_id = request.sid
        logger.info(f"[SOCKETIO] Client disconnected: {client_id}")
    
    @socketio.on('authenticate')
    def handle_authenticate(data):
        user_id = data.get('user_id')
        logger.info(f"[SOCKETIO] Client authenticated as user {user_id}")
        socketio.emit('auth_response', {'status': 'authenticated'})
    
    @socketio.on('ping')
    def handle_ping():
        logger.debug(f"[SOCKETIO] Ping received from {request.sid}")
        socketio.emit('pong', {'timestamp': time.time()}, room=request.sid)
    
    # Start MQTT subscriber in background thread
    def start_mqtt_subscriber():
        try:
            # Small delay to ensure socketio is fully initialized
            time.sleep(2)
            
            from app.services.mqtt_subscriber import MQTTSubscriber
            from app.services.mqtt_publisher import init_mqtt_publisher
            from config.config import Config
            
            logger.info("[MQTT] Initializing MQTT publisher with socketio")
            init_mqtt_publisher(socketio)
            
            logger.info("[MQTT] Creating MQTT subscriber")
            subscriber = MQTTSubscriber(
                broker=Config.MQTT_BROKER,
                port=Config.MQTT_PORT,
                use_tls=Config.MQTT_USE_TLS,
                ca_certs=Config.MQTT_CA_CERTS,
                app=app
            )
            subscriber.set_socketio(socketio)
            subscriber.set_app(app)
            
            logger.info("[MQTT] Connecting MQTT subscriber")
            subscriber.connect()
        except Exception as e:
            logger.error(f"[MQTT] Error in MQTT subscriber thread: {e}")
            import traceback
            traceback.print_exc()
    
    # Periodic MQTT status broadcast
    def broadcast_mqtt_status():
        """Periodically broadcast MQTT status to all clients"""
        time.sleep(3)  # Wait for MQTT to initialize
        
        while True:
            try:
                from app.services.mqtt_publisher import get_mqtt_publisher
                publisher = get_mqtt_publisher()
                status = 'online' if publisher.connected else 'offline'
                socketio.emit('mqtt_status', {'status': status}, namespace='/')
                logger.debug(f"[MQTT] Broadcasted MQTT status: {status}")
            except Exception as e:
                logger.error(f"[MQTT] Error broadcasting MQTT status: {e}")
            
            time.sleep(5)  # Broadcast every 5 seconds
    
    # Start threads
    try:
        mqtt_sub_thread = threading.Thread(target=start_mqtt_subscriber, daemon=True)
        mqtt_sub_thread.start()
        logger.info("[MQTT] MQTT subscriber thread started")
    except Exception as e:
        logger.error(f"[MQTT] Error starting MQTT subscriber thread: {e}")
    
    try:
        status_broadcast_thread = threading.Thread(target=broadcast_mqtt_status, daemon=True)
        status_broadcast_thread.start()
        logger.info("[MQTT] MQTT status broadcast thread started")
    except Exception as e:
        logger.error(f"[MQTT] Error starting status broadcast thread: {e}")
    
    return app

def get_socketio():
    """Get Socket.IO instance"""
    return socketio
