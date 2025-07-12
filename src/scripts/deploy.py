#!/usr/bin/env python3
"""
ResearchMate Deployment Script
A complete Python-based deployment system for ResearchMate
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path
from typing import Dict, List, Optional
import venv
import shutil
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent.parent / 'logs' / 'deployment.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ResearchMateDeployer:
    """Complete deployment system for ResearchMate"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.venv_path = self.project_root / "venv"
        self.requirements_file = self.project_root / "requirements.txt"
        self.is_windows = platform.system() == "Windows"
        
        # Load environment variables from .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")
        else:
            logger.warning(f"No .env file found at {env_file}")
        
    def print_banner(self):
        """Print deployment banner"""
        banner = """
ResearchMate Deployment System
==============================
AI Research Assistant powered by Groq Llama 3.3 70B
Version: 2.0.0
"""
        print(banner)
        logger.info("Starting ResearchMate deployment")
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        min_version = (3, 11)
        current_version = sys.version_info[:2]
        
        if current_version < min_version:
            logger.error(f"Python {min_version[0]}.{min_version[1]}+ required, got {current_version[0]}.{current_version[1]}")
            return False
        
        logger.info(f"Python version {current_version[0]}.{current_version[1]} is compatible")
        return True
    
    def create_virtual_environment(self) -> bool:
        """Create virtual environment if it doesn't exist"""
        # Check if we're in a Conda environment
        if 'CONDA_DEFAULT_ENV' in os.environ:
            logger.info(f"Using existing Conda environment: {os.environ['CONDA_DEFAULT_ENV']}")
            return True
        
        if self.venv_path.exists():
            logger.info("Virtual environment already exists")
            # Verify it's properly set up
            python_exe = self.get_venv_python()
            if python_exe.exists():
                logger.info("Virtual environment is properly configured")
                return True
            else:
                # Check if we're running from within the venv - if so, don't try to recreate
                if sys.prefix == str(self.venv_path) or sys.base_prefix != sys.prefix:
                    logger.warning("Running from within virtual environment, cannot recreate. Assuming it's properly set up.")
                    return True
                
                logger.warning("Virtual environment exists but Python executable not found, recreating...")
                try:
                    shutil.rmtree(self.venv_path)
                except PermissionError:
                    logger.error("Cannot recreate virtual environment - permission denied. Please deactivate the virtual environment first.")
                    return False
        
        try:
            logger.info("Creating virtual environment...")
            venv.create(self.venv_path, with_pip=True)
            
            # Verify the virtual environment was created properly
            python_exe = self.get_venv_python()
            if python_exe.exists():
                logger.info("Virtual environment created successfully")
                return True
            else:
                logger.error("Virtual environment creation failed - Python executable not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False
    
    def get_venv_python(self) -> Path:
        """Get path to Python executable in virtual environment"""
        # If we're already in a virtual environment, use the current Python executable
        if sys.prefix != sys.base_prefix or 'CONDA_DEFAULT_ENV' in os.environ:
            return Path(sys.executable)
        
        # Check for Conda environment first
        if 'CONDA_DEFAULT_ENV' in os.environ:
            return Path(sys.executable)
        
        # Otherwise, construct the path to the venv Python executable
        if self.is_windows:
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def get_venv_pip(self) -> Path:
        """Get path to pip executable in virtual environment"""
        # If we're already in a virtual environment (including Conda), use python -m pip
        if sys.prefix != sys.base_prefix or 'CONDA_DEFAULT_ENV' in os.environ:
            return Path(sys.executable)
        
        # Otherwise, construct the path to the venv pip executable
        if self.is_windows:
            return self.venv_path / "Scripts" / "pip.exe"
        else:
            return self.venv_path / "bin" / "pip"
    
    def install_dependencies(self):
        """Install Python dependencies"""
        try:
            logger.info("Installing dependencies...")
            
            # Get executable paths
            python_executable = self.get_venv_python()
            
            # Check if we're in a virtual environment (including Conda)
            in_venv = sys.prefix != sys.base_prefix or 'CONDA_DEFAULT_ENV' in os.environ
            
            if in_venv:
                logger.info("Running from within virtual environment, using current Python executable")
                if 'CONDA_DEFAULT_ENV' in os.environ:
                    logger.info(f"Conda environment detected: {os.environ['CONDA_DEFAULT_ENV']}")
            else:
                # Check if executables exist
                if not python_executable.exists():
                    logger.error(f"Python executable not found at: {python_executable}")
                    return False
                
                pip_executable = self.get_venv_pip()
                if not pip_executable.exists():
                    logger.error(f"Pip executable not found at: {pip_executable}")
                    return False
            
            # Skip pip upgrade for Conda environments due to potential pyexpat issues
            if 'CONDA_DEFAULT_ENV' not in os.environ:
                logger.info("Upgrading pip...")
                try:
                    result = subprocess.run([
                        str(python_executable), "-m", "pip", "install", "--upgrade", "pip"
                    ], check=True, capture_output=True, text=True, cwd=self.project_root, timeout=60)
                    logger.info("Pip upgraded successfully")
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    logger.warning("Pip upgrade failed, skipping and continuing with installation")
                    logger.debug(f"Pip upgrade error: {e}")
            else:
                logger.info("Skipping pip upgrade in Conda environment")
            
            # Install requirements
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                logger.info("Installing requirements from requirements.txt...")
                try:
                    # For Conda environments, use --no-deps to avoid conflicts
                    cmd = [str(python_executable), "-m", "pip", "install", "-r", str(requirements_file)]
                    if 'CONDA_DEFAULT_ENV' in os.environ:
                        cmd.insert(-2, "--no-deps")
                        logger.info("Using --no-deps flag for Conda environment")
                    
                    result = subprocess.run(
                        cmd, 
                        check=True, 
                        capture_output=True, 
                        text=True, 
                        cwd=self.project_root, 
                        timeout=600
                    )
                    logger.info("Requirements installed successfully")
                except subprocess.TimeoutExpired:
                    logger.error("Requirements installation timed out")
                    return False
            else:
                logger.warning("requirements.txt not found")
            
            logger.info("Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e.stderr}")
            # Try a fallback installation of critical packages
            logger.info("Attempting fallback installation of critical packages...")
            return self._install_critical_packages()
        except Exception as e:
            logger.error(f"Unexpected error during dependency installation: {e}")
            return False
    
    def _install_critical_packages(self):
        """Install only the most critical packages for ResearchMate to run"""
        try:
            python_executable = self.get_venv_python()
            critical_packages = [
                "fastapi", "uvicorn", "pydantic", "jinja2", 
                "python-dotenv", "groq", "requests"
            ]
            
            logger.info("Installing critical packages individually...")
            for package in critical_packages:
                try:
                    subprocess.run([
                        str(python_executable), "-m", "pip", "install", package, "--no-deps"
                    ], check=True, capture_output=True, text=True, cwd=self.project_root, timeout=60)
                    logger.info(f"Installed {package}")
                except Exception as e:
                    logger.warning(f"Failed to install {package}: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Critical package installation failed: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories"""
        directories = [
            "uploads",           # User file uploads
            "chroma_db",         # ChromaDB database files
            "chroma_persist",    # ChromaDB persistence
            "logs",              # Application logs
            "backups",           # System backups (for manager.py)
            "config"             # Configuration files
        ]

        try:
            logger.info("Creating directories...")
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")

            # Ensure src/static exists (but don't recreate if it exists)
            static_dir = self.project_root / "src" / "static"
            static_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Verified src/static directory exists")

            return True
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            return False
    
    def check_environment_variables(self) -> bool:
        """Check for required environment variables"""
        required_vars = ["GROQ_API_KEY"]
        missing_vars = []
        
        logger.info("Checking environment variables...")
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning("Missing environment variables:")
            for var in missing_vars:
                logger.warning(f"   - {var}")
            
            logger.info("Please set the missing variables:")
            if self.is_windows:
                for var in missing_vars:
                    logger.info(f"   set {var}=your_value_here")
            else:
                for var in missing_vars:
                    logger.info(f"   export {var}='your_value_here'")
            
            logger.info("Get your Groq API key from: https://console.groq.com/keys")
            return False
        
        logger.info("All required environment variables are set")
        return True
    
    def test_imports(self) -> bool:
        """Test if all required modules can be imported"""
        try:
            logger.info("Testing imports...")
            python_path = self.get_venv_python()
            
            test_script = """
import sys
sys.path.append('.')
try:
    from src.components import ResearchMate
    from fastapi import FastAPI
    from groq import Groq
    import chromadb
    print("All imports successful")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
"""
            
            result = subprocess.run([
                str(python_path), "-c", test_script
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("All imports successful")
                return True
            else:
                logger.error(f"Import test failed: {result.stderr}")
                logger.error(f"Import test stdout: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"Failed to test imports: {e}")
            return False
    
    def deploy(self) -> bool:
        """Run complete deployment process"""
        self.print_banner()
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing dependencies", self.install_dependencies),
            ("Creating directories", self.create_directories),
            ("Checking environment variables", self.check_environment_variables),
            ("Testing imports", self.test_imports),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Running: {step_name}")
            if not step_func():
                logger.error(f"Failed at step: {step_name}")
                return False
        
        logger.info("Deployment completed successfully!")
        logger.info("Web Interface: http://localhost:8000")
        logger.info("API Documentation: http://localhost:8000/docs")
        logger.info("Use Ctrl+C to stop the server")
        
        return True
    
    def start_server(self, host: str = None, port: int = None, reload: bool = False):
        """Start the ResearchMate server"""
        try:
            # Import settings to get default values
            sys.path.append(str(self.project_root))
            from src.settings import get_settings
            settings = get_settings()
            
            # Use provided values or defaults from settings
            host = host or settings.server.host
            port = port or settings.server.port
            
            python_path = self.get_venv_python()
            
            cmd = [
                str(python_path), "-m", "uvicorn", 
                "main:app", 
                "--host", host, 
                "--port", str(port)
            ]
            
            if reload:
                cmd.append("--reload")
            
            logger.info(f"Starting server on {host}:{port}")
            subprocess.run(cmd, cwd=self.project_root)
            
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ResearchMate Deployment System")
    parser.add_argument("--deploy-only", action="store_true", help="Only run deployment, don't start server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    deployer = ResearchMateDeployer()
    
    if deployer.deploy():
        if not args.deploy_only:
            deployer.start_server(host=args.host, port=args.port, reload=args.reload)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
