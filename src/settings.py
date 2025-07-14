#!/usr/bin/env python3
"""
ResearchMate Settings
Centralized configuration management for ResearchMate
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ServerConfig:
    """Server configuration settings"""
    host: str = "0.0.0.0"
    port: int = int(os.environ.get('PORT', 80))
    debug: bool = False
    reload: bool = False
    workers: int = 1
    log_level: str = "info"

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    chroma_persist_dir: str = "./chroma_persist"
    collection_name: str = "research_documents"
    similarity_threshold: float = 0.7
    max_results: int = 10
    embedding_model: str = "all-MiniLM-L6-v2"

@dataclass
class AIModelConfig:
    """AI model configuration settings"""
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30

@dataclass
class UploadConfig:
    """File upload configuration settings"""
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: List[str] = None
    upload_directory: str = "./uploads"
    temp_directory: str = "./tmp"
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = [".pdf", ".txt", ".md", ".docx", ".doc"]

@dataclass
class SearchConfig:
    """Search configuration settings"""
    max_results: int = 10
    similarity_threshold: float = 0.7
    enable_reranking: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 200

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    cors_origins: List[str] = None
    cors_methods: List[str] = None
    cors_headers: List[str] = None
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]
        if self.cors_methods is None:
            self.cors_methods = ["*"]
        if self.cors_headers is None:
            self.cors_headers = ["*"]

@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "./logs/app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_enabled: bool = True

class Settings:
    """Main settings class for ResearchMate"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_file()
        self.project_root = Path(__file__).parent.parent
        
        # Initialize configuration objects
        self.server = ServerConfig()
        self.database = DatabaseConfig()
        self.ai_model = AIModelConfig()
        self.upload = UploadConfig()
        self.search = SearchConfig()
        self.security = SecurityConfig()
        self.logging = LoggingConfig()
        
        # Load configuration
        self._load_config()
        self._validate_config()
    
    def _get_default_config_file(self) -> str:
        """Get default configuration file path"""
        return str(Path(__file__).parent.parent / "config" / "settings.json")
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Load from file if exists
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                self._apply_config_data(config_data)
            except Exception as e:
                logging.warning(f"Failed to load config file: {e}")
        
        # Override with environment variables
        self._load_from_env()
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to settings objects"""
        for section, data in config_data.items():
            if hasattr(self, section):
                section_obj = getattr(self, section)
                for key, value in data.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Server configuration
        self.server.host = os.getenv("HOST", self.server.host)
        self.server.port = int(os.getenv("PORT", self.server.port))
        self.server.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.server.reload = os.getenv("RELOAD", "false").lower() == "true"
        self.server.workers = int(os.getenv("WORKERS", self.server.workers))
        self.server.log_level = os.getenv("LOG_LEVEL", self.server.log_level)
        
        # Database configuration
        self.database.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", self.database.chroma_persist_dir)
        self.database.collection_name = os.getenv("COLLECTION_NAME", self.database.collection_name)
        self.database.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", self.database.similarity_threshold))
        self.database.max_results = int(os.getenv("MAX_RESULTS", self.database.max_results))
        
        # AI model configuration
        self.ai_model.model_name = os.getenv("MODEL_NAME", self.ai_model.model_name)
        self.ai_model.temperature = float(os.getenv("TEMPERATURE", self.ai_model.temperature))
        self.ai_model.max_tokens = int(os.getenv("MAX_TOKENS", self.ai_model.max_tokens))
        self.ai_model.timeout = int(os.getenv("MODEL_TIMEOUT", self.ai_model.timeout))
        
        # Upload configuration
        self.upload.max_file_size = int(os.getenv("MAX_FILE_SIZE", self.upload.max_file_size))
        self.upload.upload_directory = os.getenv("UPLOAD_DIRECTORY", self.upload.upload_directory)
        
        # Logging configuration
        self.logging.level = os.getenv("LOG_LEVEL", self.logging.level)
        self.logging.file_path = os.getenv("LOG_FILE", self.logging.file_path)
    
    def _validate_config(self):
        """Validate configuration settings"""
        # Validate required environment variables
        required_env_vars = ["GROQ_API_KEY"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate server configuration
        if not (1 <= self.server.port <= 65535):
            raise ValueError(f"Invalid port number: {self.server.port}")
        
        # Validate AI model configuration
        if not (0.0 <= self.ai_model.temperature <= 2.0):
            raise ValueError(f"Invalid temperature: {self.ai_model.temperature}")
        
        if not (1 <= self.ai_model.max_tokens <= 32768):
            raise ValueError(f"Invalid max_tokens: {self.ai_model.max_tokens}")
        
        # Validate database configuration
        if not (0.0 <= self.database.similarity_threshold <= 1.0):
            raise ValueError(f"Invalid similarity_threshold: {self.database.similarity_threshold}")
        
        # Create directories if they don't exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.database.chroma_persist_dir,
            self.upload.upload_directory,
            self.upload.temp_directory,
            Path(self.logging.file_path).parent,
            Path(self.config_file).parent
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            "server": asdict(self.server),
            "database": asdict(self.database),
            "ai_model": asdict(self.ai_model),
            "upload": asdict(self.upload),
            "search": asdict(self.search),
            "security": asdict(self.security),
            "logging": asdict(self.logging)
        }
        
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get_groq_api_key(self) -> str:
        """Get Groq API key from environment"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        return api_key
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        return f"sqlite:///{self.database.chroma_persist_dir}/chroma.db"
    
    def get_static_url(self) -> str:
        """Get static files URL"""
        return "/static"
    
    def get_templates_dir(self) -> str:
        """Get templates directory"""
        return str(self.project_root / "src" / "templates")
    
    def get_static_dir(self) -> str:
        """Get static files directory"""
        return str(self.project_root / "src" / "static")
    
    def get_upload_dir(self) -> str:
        """Get upload directory"""
        return str(self.project_root / self.upload.upload_directory)
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return os.getenv("ENVIRONMENT", "production").lower() == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.is_development()
    
    def __str__(self) -> str:
        """String representation of settings"""
        return f"ResearchMate Settings (Config: {self.config_file})"
    
    def __repr__(self) -> str:
        """Detailed representation of settings"""
        return f"Settings(config_file='{self.config_file}')"

# Global settings instance
settings = Settings()

# Convenience functions
def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings

def reload_settings():
    """Reload settings from configuration file"""
    global settings
    settings = Settings(settings.config_file)

def create_default_config():
    """Create a default configuration file"""
    default_settings = Settings()
    default_settings.save_config()
    return default_settings.config_file

if __name__ == "__main__":
    # Test the settings
    print("ResearchMate Settings Test")
    print("=" * 40)
    
    try:
        settings = get_settings()
        print(f"Settings loaded successfully")
        print(f"Config file: {settings.config_file}")
        print(f"Server: {settings.server.host}:{settings.server.port}")
        print(f"AI Model: {settings.ai_model.model_name}")
        print(f"Database: {settings.database.chroma_persist_dir}")
        print(f"Upload dir: {settings.get_upload_dir()}")
        print(f"Groq API Key: {'Set' if settings.get_groq_api_key() else 'Not set'}")
        print(f"Environment: {'Development' if settings.is_development() else 'Production'}")
        
        # Save configuration
        settings.save_config()
        print(f"Configuration saved to: {settings.config_file}")
        
    except Exception as e:
        print(f"Error: {e}")
