#!/usr/bin/env python3
"""
ResearchMate Management Script
Central management system for ResearchMate operations
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import shutil
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent.parent / 'logs' / 'manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ResearchMateManager:
    """Central management system for ResearchMate"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self.venv_path = self.project_root / "venv"
        self.backup_dir = self.project_root / "backups"
        
    def print_banner(self):
        """Print management banner"""
        banner = """
ResearchMate Management System
==============================
AI Research Assistant - Management Console
"""
        print(banner)
        logger.info("ResearchMate Management System started")
    
    def show_status(self):
        """Show system status"""
        print("\nSystem Status:")
        print("=" * 40)
        
        # Check virtual environment
        python_path = self.get_venv_python()
        venv_status = "Active" if python_path.exists() else "Missing"
        print(f"Virtual Environment: {venv_status}")
        
        # Check configuration
        config_file = self.config_dir / "config.json"
        config_status = "Configured" if config_file.exists() else "Missing"
        print(f"Configuration: {config_status}")
        
        # Check database
        chroma_dir = self.project_root / "chroma_persist"
        db_status = "Ready" if chroma_dir.exists() else "Not initialized"
        print(f"Database: {db_status}")
        
        # Check dependencies
        try:
            result = subprocess.run([
                str(python_path), "-c", "import fastapi, groq, chromadb; print('OK')"
            ], capture_output=True, text=True)
            deps_status = "Installed" if result.returncode == 0 else "Missing"
        except:
            deps_status = "Missing"
        print(f"Dependencies: {deps_status}")
        
        # Check logs
        log_files = list(Path("logs").glob("*.log")) if Path("logs").exists() else []
        print(f"Log Files: {len(log_files)} files")
        
        # Check uploads
        upload_dir = self.project_root / "uploads"
        upload_count = len(list(upload_dir.glob("*"))) if upload_dir.exists() else 0
        print(f"Uploaded Files: {upload_count} files")
    
    def get_venv_python(self) -> Path:
        """Get path to Python executable in virtual environment"""
        # If we're already in a virtual environment, use current Python
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            return Path(sys.executable)
        
        # Otherwise, look for venv in project
        if os.name == 'nt':  # Windows
            # Check both locations
            scripts_python = self.venv_path / "Scripts" / "python.exe"
            direct_python = self.venv_path / "python.exe"
            
            if scripts_python.exists():
                return scripts_python
            elif direct_python.exists():
                return direct_python
            else:
                return scripts_python  # Default fallback
        else:
            return self.venv_path / "bin" / "python"
    
    def install_dependencies(self):
        """Install or update dependencies"""
        try:
            logger.info("Installing dependencies...")
            python_path = self.get_venv_python()
            
            # Install main dependencies
            subprocess.run([
                str(python_path), "-m", "pip", "install", 
                "-r", "requirements.txt", "--upgrade"
            ], check=True)
            
            # Install development dependencies if file exists
            dev_requirements = self.project_root / "requirements-dev.txt"
            if dev_requirements.exists():
                subprocess.run([
                    str(python_path), "-m", "pip", "install", 
                    "-r", str(dev_requirements), "--upgrade"
                ], check=True)
            
            logger.info("Dependencies installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def backup_data(self):
        """Create backup of important data"""
        try:
            logger.info("Creating backup...")
            
            # Create backup directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup directories
            backup_items = [
                ("config", "Configuration files"),
                ("chroma_persist", "Database"),
                ("uploads", "Uploaded files"),
                ("logs", "Log files")
            ]
            
            for item, description in backup_items:
                source = self.project_root / item
                if source.exists():
                    dest = backup_path / item
                    if source.is_dir():
                        shutil.copytree(source, dest)
                    else:
                        shutil.copy2(source, dest)
                    logger.info(f"Backed up: {description}")
            
            # Create backup info file
            backup_info = {
                "timestamp": timestamp,
                "version": "2.0.0",
                "items": [item for item, _ in backup_items]
            }
            
            with open(backup_path / "backup_info.json", 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            logger.info(f"Backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def restore_data(self, backup_name: str):
        """Restore data from backup"""
        try:
            logger.info(f"Restoring from backup: {backup_name}")
            
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_name}")
                return False
            
            # Read backup info
            backup_info_file = backup_path / "backup_info.json"
            if backup_info_file.exists():
                with open(backup_info_file, 'r') as f:
                    backup_info = json.load(f)
                logger.info(f"Restoring backup from: {backup_info['timestamp']}")
            
            # Restore items
            for item in backup_path.iterdir():
                if item.name == "backup_info.json":
                    continue
                    
                dest = self.project_root / item.name
                
                # Remove existing
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                
                # Restore
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
                
                logger.info(f"Restored: {item.name}")
            
            logger.info("Restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self):
        """List available backups"""
        if not self.backup_dir.exists():
            print("No backups found")
            return
        
        backups = [d for d in self.backup_dir.iterdir() if d.is_dir()]
        if not backups:
            print("No backups found")
            return
        
        print("\nAvailable Backups:")
        print("=" * 40)
        
        for backup in sorted(backups):
            backup_info_file = backup / "backup_info.json"
            if backup_info_file.exists():
                with open(backup_info_file, 'r') as f:
                    info = json.load(f)
                timestamp = info.get('timestamp', 'Unknown')
                print(f"- {backup.name} (Created: {timestamp})")
            else:
                print(f"- {backup.name}")
    
    def clean_logs(self):
        """Clean old log files"""
        try:
            logger.info("Cleaning logs...")
            
            logs_dir = self.project_root / "logs"
            if not logs_dir.exists():
                logger.info("No logs directory found")
                return True
            
            # Keep only last 10 log files
            log_files = sorted(logs_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            if len(log_files) > 10:
                for log_file in log_files[10:]:
                    log_file.unlink()
                    logger.info(f"Removed old log: {log_file.name}")
            
            logger.info("Log cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean logs: {e}")
            return False
    
    def reset_database(self):
        """Reset ChromaDB database"""
        try:
            logger.info("Resetting database...")
            
            chroma_dir = self.project_root / "chroma_persist"
            if chroma_dir.exists():
                shutil.rmtree(chroma_dir)
                logger.info("Database reset completed")
            else:
                logger.info("Database directory not found")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            return False
    
    def run_tests(self):
        """Run test suite"""
        try:
            logger.info("Running tests...")
            
            # Check if tests directory exists
            tests_dir = self.project_root / "src" / "tests"
            if not tests_dir.exists():
                logger.info("No tests directory found - skipping test run")
                return True
            
            # Check if any test files exist
            test_files = list(tests_dir.glob("test_*.py"))
            if not test_files:
                logger.info("No test files found - skipping test run")
                return True
            
            logger.info(f"Found {len(test_files)} test files")
            
            # Run tests directly with Python (no pytest required)
            python_path = self.get_venv_python()
            logger.info(f"Using Python executable: {python_path}")
            logger.info(f"Python executable exists: {python_path.exists()}")
            
            all_passed = True
            
            for test_file in test_files:
                logger.info(f"Running: {test_file.name}")
                logger.info(f"Full test path: {test_file}")
                
                result = subprocess.run([
                    str(python_path), str(test_file)
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode == 0:
                    logger.info(f"PASS: {test_file.name}")
                    if result.stdout:
                        logger.info(f"Output:\n{result.stdout}")
                else:
                    logger.error(f"FAIL: {test_file.name}")
                    if result.stdout:
                        logger.error(f"Output:\n{result.stdout}")
                    if result.stderr:
                        logger.error(f"Errors:\n{result.stderr}")
                    all_passed = False
            
            if all_passed:
                logger.info("All tests passed successfully!")
            else:
                logger.error("Some tests failed!")
            
            return all_passed
                
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return False
    
    def start_server(self, mode: str = "production"):
        """Start server in different modes"""
        try:
            if mode == "development":
                logger.info("Starting development server...")
                subprocess.run([
                    sys.executable, "src/scripts/dev_server.py"
                ], cwd=self.project_root)
            else:
                logger.info("Starting production server...")
                subprocess.run([
                    sys.executable, "src/scripts/deploy.py"
                ], cwd=self.project_root)
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")

def main():
    """Main management function"""
    parser = argparse.ArgumentParser(description="ResearchMate Management System")
    parser.add_argument("command", choices=[
        "status", "install", "backup", "restore", "list-backups", 
        "clean-logs", "reset-db", "test", "start", "dev"
    ], help="Management command")
    parser.add_argument("--backup-name", help="Backup name for restore command")
    
    args = parser.parse_args()
    
    manager = ResearchMateManager()
    manager.print_banner()
    
    if args.command == "status":
        manager.show_status()
    elif args.command == "install":
        manager.install_dependencies()
    elif args.command == "backup":
        manager.backup_data()
    elif args.command == "restore":
        if not args.backup_name:
            print("Error: --backup-name required for restore")
            sys.exit(1)
        manager.restore_data(args.backup_name)
    elif args.command == "list-backups":
        manager.list_backups()
    elif args.command == "clean-logs":
        manager.clean_logs()
    elif args.command == "reset-db":
        manager.reset_database()
    elif args.command == "test":
        manager.run_tests()
    elif args.command == "start":
        manager.start_server("production")
    elif args.command == "dev":
        manager.start_server("development")

if __name__ == "__main__":
    main()
