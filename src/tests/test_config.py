"""
Test configuration loading and validation
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.settings import Settings

def test_settings_load():
    """Test that settings can be loaded"""
    settings = Settings()
    assert settings is not None
    assert hasattr(settings, 'server')
    assert hasattr(settings, 'database')
    print("PASS: Settings loading test passed")

def test_default_settings():
    """Test that default settings are reasonable"""
    settings = Settings()
    
    # Check that basic settings exist
    assert settings.server.host is not None
    assert settings.server.port is not None
    assert settings.ai_model.model_name is not None
    
    print("PASS: Default settings test passed")

def test_settings_types():
    """Test that settings have correct types"""
    settings = Settings()
    
    # Port should be integer
    port = settings.server.port
    assert isinstance(port, int)
    assert 1000 <= port <= 65535
    
    # Host should be string
    host = settings.server.host
    assert isinstance(host, str)
    
    print("PASS: Settings types test passed")

if __name__ == "__main__":
    success = True
    success &= test_settings_load()
    success &= test_default_settings()
    success &= test_settings_types()
    
    if success:
        print("All configuration tests passed!")
    else:
        print("Some tests failed!")
        sys.exit(1)
