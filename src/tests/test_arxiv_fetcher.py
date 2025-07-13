"""
Test ArXiv fetcher functionality
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_arxiv_fetcher_import():
    """Test that ArXiv fetcher can be imported"""
    # Import the module directly without going through __init__.py
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "arxiv_fetcher", 
        str(Path(__file__).parent.parent / "components" / "arxiv_fetcher.py")
    )
    arxiv_fetcher_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arxiv_fetcher_module)
    
    ArxivFetcher = arxiv_fetcher_module.ArxivFetcher
    assert ArxivFetcher is not None
    print("PASS: ArXiv fetcher import test passed")

def test_arxiv_fetcher_creation():
    """Test that ArXiv fetcher can be created"""
    # Import the module directly without going through __init__.py
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "arxiv_fetcher", 
        str(Path(__file__).parent.parent / "components" / "arxiv_fetcher.py")
    )
    arxiv_fetcher_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arxiv_fetcher_module)
    
    ArxivFetcher = arxiv_fetcher_module.ArxivFetcher
    fetcher = ArxivFetcher()
    assert fetcher is not None
    print("PASS: ArXiv fetcher creation test passed")

if __name__ == "__main__":
    success = True
    success &= test_arxiv_fetcher_import()
    success &= test_arxiv_fetcher_creation()
    
    if success:
        print("All ArXiv fetcher tests passed!")
    else:
        print("Some tests failed!")
        sys.exit(1)
