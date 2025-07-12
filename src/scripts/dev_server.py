#!/usr/bin/env python3
"""
ResearchMate Development Server
A complete Python-based development environment for ResearchMate
"""

import os
import sys
import subprocess
import threading
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
import signal
import webbrowser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import platform  # Import platform module

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent.parent / 'logs' / 'development.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FileChangeHandler(FileSystemEventHandler):
    """Handle file changes for auto-reload"""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = {}
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Only watch Python files
        if not event.src_path.endswith('.py'):
            return
            
        # Debounce rapid changes
        current_time = time.time()
        if event.src_path in self.last_modified:
            if current_time - self.last_modified[event.src_path] < 1:
                return
                
        self.last_modified[event.src_path] = current_time
        logger.info(f"File changed: {event.src_path}")
        self.callback()

class ResearchMateDevServer:
    """Development server for ResearchMate"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.venv_path = self.project_root / "venv"
        self.server_process = None
        self.observer = None
        self.is_running = False
        self.is_windows = platform.system() == "Windows"  # Add this line
    
    def print_banner(self):
        """Print development server banner"""
        banner = """
ResearchMate Development Server
=================================
AI Research Assistant - Development Mode
Auto-reload enabled for Python files
"""
        print(banner)
        logger.info("Starting ResearchMate development server")
    
    def get_venv_python(self) -> Path:
        """Get path to Python executable in virtual environment"""
        # If we're already in a virtual environment (including Conda), use the current Python executable
        if sys.prefix != sys.base_prefix or 'CONDA_DEFAULT_ENV' in os.environ:
            return Path(sys.executable)
        
        # Otherwise, construct the path to the venv Python executable
        if self.is_windows:
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def check_virtual_environment(self) -> bool:
        """Check if virtual environment exists"""
        # Check if we're in a Conda environment
        if 'CONDA_DEFAULT_ENV' in os.environ:
            logger.info(f"Using existing Conda environment: {os.environ['CONDA_DEFAULT_ENV']}")
            return True
        
        # Check if we're in any virtual environment
        if sys.prefix != sys.base_prefix:
            logger.info("Using existing virtual environment")
            return True
        
        # Check for traditional venv
        python_path = self.get_venv_python()
        if not python_path.exists():
            logger.error("Virtual environment not found. Please run deployment first.")
            logger.info("Run: python researchmate.py deploy")
            return False
        return True
    
    def start_server_process(self, host: str = "127.0.0.1", port: int = 8000):
        """Start the server process"""
        try:
            python_path = self.get_venv_python()
            
            cmd = [
                str(python_path), "-m", "uvicorn", 
                "main:app", 
                "--host", host, 
                "--port", str(port),
                "--reload"
            ]
            
            logger.info(f"Starting server on {host}:{port}")
            self.server_process = subprocess.Popen(
                cmd, 
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop_server_process(self):
        """Stop the server process"""
        if self.server_process:
            logger.info("Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't stop gracefully, killing...")
                self.server_process.kill()
            self.server_process = None
    
    def restart_server(self):
        """Restart the server"""
        logger.info("Restarting server...")
        self.stop_server_process()
        time.sleep(1)
        self.start_server_process()
    
    def setup_file_watcher(self):
        """Setup file watcher for auto-reload"""
        try:
            self.observer = Observer()
            
            # Watch source files
            watch_paths = [
                self.project_root / "src",
                self.project_root / "main.py"
            ]
            
            handler = FileChangeHandler(self.restart_server)
            
            for path in watch_paths:
                if path.exists():
                    if path.is_file():
                        self.observer.schedule(handler, str(path.parent), recursive=False)
                    else:
                        self.observer.schedule(handler, str(path), recursive=True)
            
            self.observer.start()
            logger.info("File watcher started")
            
        except Exception as e:
            logger.error(f"Failed to setup file watcher: {e}")
    
    def stop_file_watcher(self):
        """Stop file watcher"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
    
    def open_browser(self, url: str):
        """Open browser after server starts"""
        def open_after_delay():
            time.sleep(3)  # Wait for server to start
            try:
                webbrowser.open(url)
                logger.info(f"Opened browser at {url}")
            except Exception as e:
                logger.warning(f"Could not open browser: {e}")
        
        thread = threading.Thread(target=open_after_delay)
        thread.daemon = True
        thread.start()
    
    def run_tests(self):
        """Run project tests"""
        try:
            logger.info("Running tests...")
            logger.info("No tests configured - skipping test run")
            
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
    
    def check_code_quality(self):
        """Check code quality with linting"""
        try:
            logger.info("Checking code quality...")
            python_path = self.get_venv_python()
            
            # Run flake8 if available
            try:
                result = subprocess.run([
                    str(python_path), "-m", "flake8", 
                    "src/", "main.py", "--max-line-length=88"
                ], cwd=self.project_root, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("Code quality checks passed")
                else:
                    logger.warning("Code quality issues found:")
                    print(result.stdout)
                    
            except FileNotFoundError:
                logger.info("flake8 not installed, skipping code quality check")
                
        except Exception as e:
            logger.error(f"Failed to check code quality: {e}")
    
    def start(self, host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
        """Start the development server"""
        self.print_banner()
        
        if not self.check_virtual_environment():
            return False
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info("Received interrupt signal")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            self.is_running = True
            
            # Start server
            if not self.start_server_process(host, port):
                return False
            
            # Setup file watcher
            self.setup_file_watcher()
            
            # Open browser
            if open_browser:
                self.open_browser(f"http://{host}:{port}")
            
            logger.info("Development server started successfully!")
            logger.info(f"Web Interface: http://{host}:{port}")
            logger.info(f"API Documentation: http://{host}:{port}/docs")
            logger.info("Auto-reload enabled")
            logger.info("Use Ctrl+C to stop")
            
            # Keep the main thread alive
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Development server error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the development server"""
        self.is_running = False
        self.stop_file_watcher()
        self.stop_server_process()
        logger.info("Development server stopped")

def main():
    """Main development server function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ResearchMate Development Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    parser.add_argument("--test", action="store_true", help="Run tests only")
    parser.add_argument("--lint", action="store_true", help="Check code quality only")
    
    args = parser.parse_args()
    
    dev_server = ResearchMateDevServer()
    
    if args.test:
        dev_server.run_tests()
    elif args.lint:
        dev_server.check_code_quality()
    else:
        dev_server.start(
            host=args.host, 
            port=args.port, 
            open_browser=not args.no_browser
        )

if __name__ == "__main__":
    main()
