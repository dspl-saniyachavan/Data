import pytest
import sys
import os
from PySide6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope='session')
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def test_db_path(tmp_path):
    """Provide temporary database path"""
    return str(tmp_path / "precision_pulse.db")

@pytest.fixture
def app():
    """Create Flask app for testing"""
    from app import create_app
    from app.models import db
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
