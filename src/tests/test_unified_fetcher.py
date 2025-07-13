"""
Test unified paper fetcher functionality
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_unified_fetcher_import():
    """Test that unified fetcher can be imported"""
    try:
        # Import the module directly without going through __init__.py
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "unified_fetcher", 
            str(Path(__file__).parent.parent / "components" / "unified_fetcher.py")
        )
        unified_fetcher_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(unified_fetcher_module)
        
        PaperFetcher = unified_fetcher_module.PaperFetcher
        assert PaperFetcher is not None
        print("PASS: Unified fetcher import test passed")
        return True
    except Exception as e:
        print(f"FAIL: Unified fetcher import test failed: {e}")
        return False

def test_unified_fetcher_creation():
    """Test that unified fetcher can be created"""
    try:
        # Import the module directly without going through __init__.py
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "unified_fetcher", 
            str(Path(__file__).parent.parent / "components" / "unified_fetcher.py")
        )
        unified_fetcher_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(unified_fetcher_module)
        
        PaperFetcher = unified_fetcher_module.PaperFetcher
        fetcher = PaperFetcher()
        assert fetcher is not None
        print("PASS: Unified fetcher creation test passed")
        return True
    except Exception as e:
        print(f"FAIL: Unified fetcher creation test failed: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with ArxivFetcher"""
    try:
        # Import the module directly without going through __init__.py
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "unified_fetcher", 
            str(Path(__file__).parent.parent / "components" / "unified_fetcher.py")
        )
        unified_fetcher_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(unified_fetcher_module)
        
        ArxivFetcher = unified_fetcher_module.ArxivFetcher
        fetcher = ArxivFetcher()
        assert fetcher is not None
        print("PASS: Backward compatibility test passed")
        return True
    except Exception as e:
        print(f"FAIL: Backward compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running unified fetcher tests...")
    
    tests = [
        test_unified_fetcher_import,
        test_unified_fetcher_creation,
        test_backward_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)
