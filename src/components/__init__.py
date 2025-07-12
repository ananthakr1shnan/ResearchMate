"""
ResearchMate Components Package
Modular Python components for the AI research assistant
"""

from .config import Config
from .groq_processor import GroqProcessor, GroqLlamaLLM
from .rag_system import RAGSystem
from .unified_fetcher import ArxivFetcher, PaperFetcher, UnifiedFetcher
from .pdf_processor import PDFProcessor
from .research_assistant import SimpleResearchAssistant, ResearchMate

__all__ = [
    'Config',
    'GroqProcessor',
    'GroqLlamaLLM',
    'RAGSystem',
    'ArxivFetcher',
    'PaperFetcher',
    'UnifiedFetcher',
    'PDFProcessor',
    'SimpleResearchAssistant',
    'ResearchMate'
]

__version__ = "2.0.0"
