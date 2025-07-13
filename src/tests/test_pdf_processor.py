"""
Test PDF processor functionality
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

"""
Test PDF processor functionality
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_pdf_processor_import():
    """Test that PDF processor can be imported"""
    try:
        # Import the module directly without going through __init__.py
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pdf_processor", 
            str(Path(__file__).parent.parent / "components" / "pdf_processor.py")
        )
        pdf_processor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdf_processor_module)
        
        PDFProcessor = pdf_processor_module.PDFProcessor
        print("PASS: PDF processor import test passed")
        return True
    except Exception as e:
        print(f"FAIL: PDF processor import failed: {e}")
        return False

def test_pdf_processor_creation():
    """Test that PDF processor can be created"""
    try:
        # Import the module directly without going through __init__.py
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pdf_processor", 
            str(Path(__file__).parent.parent / "components" / "pdf_processor.py")
        )
        pdf_processor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdf_processor_module)
        
        PDFProcessor = pdf_processor_module.PDFProcessor
        processor = PDFProcessor()
        assert processor is not None
        print("PASS: PDF processor creation test passed")
        return True
    except Exception as e:
        print(f"FAIL: PDF processor creation failed: {e}")
        return False

if __name__ == "__main__":
    success = True
    success &= test_pdf_processor_import()
    success &= test_pdf_processor_creation()
    
    if success:
        print("All PDF processor tests passed!")
    else:
        print("Some tests failed!")
        sys.exit(1)
