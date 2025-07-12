"""
Configuration module for ResearchMate
Provides backward compatibility with new settings system
"""

import os
from pathlib import Path
from typing import Optional
from ..settings import get_settings

# Get settings instance
settings = get_settings()

class Config:
    """Configuration settings for ResearchMate - Legacy compatibility wrapper"""
    
    # Application settings
    APP_NAME: str = "ResearchMate"
    VERSION: str = "2.0.0"
    DEBUG: bool = settings.server.debug
    HOST: str = settings.server.host
    PORT: int = settings.server.port
    
    # API Keys
    GROQ_API_KEY: Optional[str] = settings.get_groq_api_key()
    
    # Groq Llama 3.3 70B settings
    LLAMA_MODEL: str = settings.ai_model.model_name
    MAX_INPUT_TOKENS: int = settings.ai_model.max_tokens
    MAX_OUTPUT_TOKENS: int = settings.ai_model.max_tokens
    TEMPERATURE: float = settings.ai_model.temperature
    TOP_P: float = settings.ai_model.top_p
    
    # Embeddings and chunking
    EMBEDDING_MODEL: str = settings.database.embedding_model
    CHUNK_SIZE: int = settings.search.chunk_size
    CHUNK_OVERLAP: int = settings.search.chunk_overlap
    
    # Database settings
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    CHROMA_DB_PATH: str = str(BASE_DIR / "chroma_db")
    COLLECTION_NAME: str = settings.database.collection_name
    PERSIST_DIRECTORY: str = str(BASE_DIR / settings.database.chroma_persist_dir.lstrip('./'))  # Make absolute
    
    # Upload settings
    UPLOAD_DIRECTORY: str = settings.get_upload_dir()
    MAX_FILE_SIZE: int = settings.upload.max_file_size
    ALLOWED_EXTENSIONS: set = set(ext.lstrip('.') for ext in settings.upload.allowed_extensions)
    
    # Search settings
    TOP_K_SIMILAR: int = settings.search.max_results
    MAX_PAPER_LENGTH: int = 100000  # Keep existing default
    MAX_SUMMARY_LENGTH: int = 2000  # Keep existing default
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALLOWED_HOSTS: list = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log"))
    
    # External APIs
    ARXIV_API_BASE_URL: str = os.getenv("ARXIV_API_BASE_URL", "http://export.arxiv.org/api/query")
    SEMANTIC_SCHOLAR_API_URL: str = os.getenv("SEMANTIC_SCHOLAR_API_URL", "https://api.semanticscholar.org/graph/v1/paper/search")
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        directories = [
            cls.CHROMA_DB_PATH,
            cls.PERSIST_DIRECTORY,
            cls.UPLOAD_DIRECTORY,
            str(Path(cls.LOG_FILE).parent)
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        if cls.MAX_FILE_SIZE > 50 * 1024 * 1024:  # 50MB limit
            raise ValueError("MAX_FILE_SIZE cannot exceed 50MB")
        
        if cls.CHUNK_SIZE < 100:
            raise ValueError("CHUNK_SIZE must be at least 100 characters")
    
    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary"""
        return {
            "app_name": cls.APP_NAME,
            "version": cls.VERSION,
            "debug": cls.DEBUG,
            "host": cls.HOST,
            "port": cls.PORT,
            "llama_model": cls.LLAMA_MODEL,
            "embedding_model": cls.EMBEDDING_MODEL,
            "chunk_size": cls.CHUNK_SIZE,
            "max_file_size": cls.MAX_FILE_SIZE,
            "rate_limit_enabled": cls.RATE_LIMIT_ENABLED
        }

# Initialize configuration
config = Config()
config.create_directories()

# Validate configuration on import
try:
    config.validate_config()
    print("Configuration validated successfully")
except ValueError as e:
    print(f"Configuration error: {e}")
    if not config.DEBUG:
        raise
