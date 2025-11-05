"""
Pytest configuration and fixtures
"""
import pytest
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock environment variables for testing
os.environ['GEMINI_API_KEY'] = 'test_key'
os.environ['OPENROUTER_API_KEY'] = 'test_key'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_ANON_KEY'] = 'test_key'
os.environ['SUPABASE_SERVICE_KEY'] = 'test_key'


@pytest.fixture
def config():
    """Provide test configuration"""
    from config.settings import Config
    return Config(validate_on_init=False)


@pytest.fixture
def mock_file(tmp_path):
    """Create a mock test file"""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"mock pdf content")
    return str(test_file)


@pytest.fixture
def app():
    """Create Flask test app"""
    from api.process import app, limiter
    
    # Disable rate limiting for tests
    limiter.enabled = False
    
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()
