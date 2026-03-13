import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/precision_pulse')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.getenv('JWT_SECRET', 'precision-pulse-super-secret-jwt-key-2024-development-only')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION = int(os.getenv('JWT_EXPIRATION', 86400))
    
    # MQTT Configuration
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 18883))
    MQTT_USE_TLS = os.getenv('MQTT_USE_TLS', 'true').lower() == 'true'
    MQTT_CA_CERTS = os.getenv('MQTT_CA_CERTS', 'config/ca.crt')
    MQTT_KEEPALIVE = int(os.getenv('MQTT_KEEPALIVE', 60))
