#!/usr/bin/env python3
"""
ResearchMate Setup Script
Complete setup and configuration for ResearchMate
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import configparser
import getpass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent.parent / 'logs' / 'setup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ResearchMateSetup:
    """Complete setup system for ResearchMate"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self.settings_file = self.config_dir / "settings.json"
        self.env_file = self.project_root / ".env"
        
    def print_banner(self):
        """Print setup banner"""
        banner = """
ResearchMate Setup System
============================
AI Research Assistant Configuration
Version: 2.0.0
"""
        print(banner)
        logger.info("Starting ResearchMate setup")
    
    def create_config_structure(self):
        """Create configuration directory structure"""
        try:
            logger.info("Creating configuration structure...")
            
            # Create directories
            directories = [
                "config",
                "logs",
                "uploads",
                "chroma_db",
                "chroma_persist",
                "src/templates",
                "src/tests"
            ]
            
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create configuration structure: {e}")
            return False
    
    def collect_configuration(self) -> Dict[str, Any]:
        """Collect configuration from user"""
        config = {}
        
        print("\nConfiguration Setup")
        print("Please provide the following information:")
        
        # API Keys
        print("\nAPI Configuration:")
        groq_api_key = getpass.getpass("Enter your Groq API key: ")
        config["groq_api_key"] = groq_api_key
        
        # Server Configuration
        print("\nServer Configuration:")
        config["server"] = {
            "host": input("Host (default: 0.0.0.0): ") or "0.0.0.0",
            "port": int(input("Port (default: 8000): ") or "8000"),
            "debug": input("Debug mode (y/n, default: n): ").lower() == 'y'
        }
        
        # Database Configuration
        print("\nDatabase Configuration:")
        config["database"] = {
            "chroma_persist_dir": input("ChromaDB persist directory (default: ./chroma_persist): ") or "./chroma_persist",
            "collection_name": input("Collection name (default: research_documents): ") or "research_documents"
        }
        
        # AI Model Configuration
        print("\nAI Model Configuration:")
        config["ai_model"] = {
            "model_name": input("Groq model name (default: llama-3.3-70b-versatile): ") or "llama-3.3-70b-versatile",
            "temperature": float(input("Temperature (default: 0.7): ") or "0.7"),
            "max_tokens": int(input("Max tokens (default: 4096): ") or "4096")
        }
        
        # Search Configuration
        print("\nSearch Configuration:")
        config["search"] = {
            "max_results": int(input("Max search results (default: 10): ") or "10"),
            "similarity_threshold": float(input("Similarity threshold (default: 0.7): ") or "0.7")
        }
        
        # Upload Configuration
        print("\nUpload Configuration:")
        config["upload"] = {
            "max_file_size": int(input("Max file size in MB (default: 50): ") or "50") * 1024 * 1024,
            "allowed_extensions": [".pdf", ".txt", ".md", ".docx"]
        }
        
        return config
    
    def save_configuration(self, config: Dict[str, Any]):
        """Save configuration to settings file"""
        try:
            logger.info("Saving configuration...")
            
            # Create settings configuration
            settings_config = {
                "server": {
                    "host": config['server']['host'],
                    "port": config['server']['port'],
                    "debug": config['server']['debug'],
                    "reload": False,
                    "workers": 1,
                    "log_level": "info"
                },
                "database": {
                    "chroma_persist_dir": config['database']['chroma_persist_dir'],
                    "collection_name": config['database']['collection_name'],
                    "similarity_threshold": 0.7,
                    "max_results": config['search']['max_results'],
                    "embedding_model": "all-MiniLM-L6-v2"
                },
                "ai_model": {
                    "model_name": config['ai_model']['model_name'],
                    "temperature": config['ai_model']['temperature'],
                    "max_tokens": config['ai_model']['max_tokens'],
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "timeout": 30
                },
                "upload": {
                    "max_file_size": config['upload']['max_file_size'],
                    "allowed_extensions": config['upload']['allowed_extensions'],
                    "upload_directory": "./uploads",
                    "temp_directory": "./tmp"
                },
                "search": {
                    "max_results": config['search']['max_results'],
                    "similarity_threshold": config['search']['similarity_threshold'],
                    "enable_reranking": True,
                    "chunk_size": 1000,
                    "chunk_overlap": 200
                },
                "security": {
                    "cors_origins": ["*"],
                    "cors_methods": ["*"],
                    "cors_headers": ["*"],
                    "rate_limit_enabled": True,
                    "rate_limit_requests": 100,
                    "rate_limit_period": 60
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "file_enabled": True,
                    "file_path": "./logs/app.log",
                    "max_file_size": 10485760,
                    "backup_count": 5,
                    "console_enabled": True
                }
            }
            
            # Save to settings.json
            settings_file = self.config_dir / "settings.json"
            with open(settings_file, 'w') as f:
                json.dump(settings_config, f, indent=2)
            
            # Save environment variables
            env_content = f"""# ResearchMate Environment Variables
GROQ_API_KEY={config['groq_api_key']}
ENVIRONMENT=production
DEBUG={str(config['server']['debug']).lower()}
HOST={config['server']['host']}
PORT={config['server']['port']}
"""
            
            with open(self.env_file, 'w') as f:
                f.write(env_content)
            
            logger.info("Configuration saved successfully")
            logger.info(f"Settings file: {settings_file}")
            logger.info(f"Environment file: {self.env_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def create_startup_script(self):
        """Create startup script"""
        try:
            logger.info("Creating startup script...")
            
            startup_content = """#!/usr/bin/env python3
# ResearchMate Startup Script
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from scripts.deploy import ResearchMateDeployer

def main():
    deployer = ResearchMateDeployer()
    if deployer.deploy():
        deployer.start_server()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
            
            startup_script = self.project_root / "start_researchmate.py"
            with open(startup_script, 'w') as f:
                f.write(startup_content)
            
            # Make executable on Unix systems
            if os.name != 'nt':
                os.chmod(startup_script, 0o755)
            
            logger.info("Startup script created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create startup script: {e}")
            return False
    
    def create_test_files(self):
        """Create test files structure"""
        try:
            logger.info("Creating test files...")
            
            # Create test directory structure
            test_dirs = [
                "src/tests",
                "src/tests/unit",
                "src/tests/integration",
                "src/tests/fixtures"
            ]
            
            for test_dir in test_dirs:
                (self.project_root / test_dir).mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files
            for test_dir in test_dirs:
                init_file = self.project_root / test_dir / "__init__.py"
                init_file.touch()
            
            # Create basic test files
            test_files = {
                "src/tests/test_basic.py": '''"""Basic tests for ResearchMate"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test that core modules can be imported"""
    try:
        from src.components import ResearchAssistant
        from src.components.config import Config
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_config_loading():
    """Test configuration loading"""
    from src.components.config import Config
    config = Config()
    assert config is not None
''',
                "src/tests/conftest.py": '''"""Test configuration"""
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_config():
    """Sample configuration for tests"""
    return {
        "server": {"host": "127.0.0.1", "port": 8000},
        "database": {"chroma_persist_dir": "./test_chroma"},
        "ai_model": {"model_name": "llama-3.3-70b-versatile"}
    }
''',
                "src/tests/unit/test_components.py": '''"""Unit tests for components"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

def test_research_assistant_init():
    """Test ResearchAssistant initialization"""
    # Add your component tests here
    assert True

def test_config_validation():
    """Test configuration validation"""
    # Add your config tests here
    assert True
''',
                "src/tests/integration/test_api.py": '''"""Integration tests for API"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

def test_api_endpoints():
    """Test API endpoints"""
    # Add your API tests here
    assert True
'''
            }
            
            for file_path, content in test_files.items():
                full_path = self.project_root / file_path
                with open(full_path, 'w') as f:
                    f.write(content)
            
            logger.info("Test files created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create test files: {e}")
            return False
    
    def create_development_tools(self):
        """Create development tools and scripts"""
        try:
            logger.info("Creating development tools...")
            
            # Create development requirements
            dev_requirements = """# Development dependencies
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
flake8==6.1.0
isort==5.12.0
watchdog==3.0.0
pre-commit==3.5.0
"""
            
            with open(self.project_root / "requirements-dev.txt", 'w') as f:
                f.write(dev_requirements)
            
            # Create pre-commit configuration
            pre_commit_config = """repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88]
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
"""
            
            with open(self.project_root / ".pre-commit-config.yaml", 'w') as f:
                f.write(pre_commit_config)
            
            # Create setup.cfg for tool configuration
            setup_cfg = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,venv,build,dist
ignore = E203,W503

[isort]
profile = black
multi_line_output = 3
line_length = 88

[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
"""
            
            with open(self.project_root / "setup.cfg", 'w') as f:
                f.write(setup_cfg)
            
            logger.info("Development tools created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create development tools: {e}")
            return False
    
    def update_requirements(self):
        """Update requirements.txt with additional development packages"""
        try:
            logger.info("Updating requirements...")
            
            # Add development packages to main requirements
            additional_packages = [
                "python-dotenv==1.0.0",
                "watchdog==3.0.0"
            ]
            
            with open(self.project_root / "requirements.txt", 'r') as f:
                current_requirements = f.read()
            
            # Add packages if not already present
            for package in additional_packages:
                if package.split('==')[0] not in current_requirements:
                    current_requirements += f"\n{package}"
            
            with open(self.project_root / "requirements.txt", 'w') as f:
                f.write(current_requirements)
            
            logger.info("Requirements updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update requirements: {e}")
            return False
    
    def run_setup(self):
        """Run complete setup process"""
        self.print_banner()
        
        steps = [
            ("Creating configuration structure", self.create_config_structure),
            ("Updating requirements", self.update_requirements),
            ("Creating test files", self.create_test_files),
            ("Creating development tools", self.create_development_tools),
            ("Creating startup script", self.create_startup_script),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Running: {step_name}")
            if not step_func():
                logger.error(f"Failed at step: {step_name}")
                return False
        
        # Collect and save configuration
        config = self.collect_configuration()
        if not self.save_configuration(config):
            return False
        
        logger.info("Setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Run: python scripts/deploy.py")
        logger.info("2. Or run: python start_researchmate.py")
        logger.info("3. For development: python scripts/dev_server.py")
        
        return True

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ResearchMate Setup System")
    parser.add_argument("--skip-config", action="store_true", help="Skip configuration collection")
    
    args = parser.parse_args()
    
    setup = ResearchMateSetup()
    
    if setup.run_setup():
        logger.info("Setup completed successfully!")
    else:
        logger.error("Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
