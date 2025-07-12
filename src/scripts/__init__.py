"""
ResearchMate Scripts Package
Contains all management and deployment scripts for ResearchMate
"""

__version__ = "2.0.0"
__author__ = "ResearchMate Team"
__description__ = "AI Research Assistant Scripts"

from .deploy import ResearchMateDeployer
from .setup import ResearchMateSetup
from .manager import ResearchMateManager
from .dev_server import ResearchMateDevServer

__all__ = [
    'ResearchMateDeployer',
    'ResearchMateSetup', 
    'ResearchMateManager',
    'ResearchMateDevServer'
]
