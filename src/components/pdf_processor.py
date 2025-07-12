"""
PDF Processor Component
Processes PDF files to extract text and metadata
"""

import os
import re
import warnings
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

# PDF processing libraries
import pypdf
try:
    import pdfplumber
    import fitz  # PyMuPDF
    PDF_ENHANCED = True
except ImportError:
    PDF_ENHANCED = False

warnings.filterwarnings('ignore')


class PDFProcessor:
    """
    Processes PDF files to extract text, metadata, and structure
    Supports multiple PDF processing libraries for better compatibility
    """
    
    def __init__(self, config=None):
        # Import Config only when needed to avoid dependency issues
        if config is None:
            try:
                from .config import Config
                self.config = Config()
            except ImportError:
                # Fallback to None if Config cannot be imported
                self.config = None
        else:
            self.config = config
        self.supported_formats = ['.pdf']
        
        # Check available libraries
        self.libraries = {
            'pypdf': True,
            'pdfplumber': PDF_ENHANCED,
            'PyMuPDF': PDF_ENHANCED
        }
        
        print(f"PDF Processor initialized with libraries: {[k for k, v in self.libraries.items() if v]}")
    
    def extract_text_from_file(self, file_path: str, method: str = 'auto') -> Dict[str, Any]:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            method: Extraction method ('auto', 'pypdf', 'pdfplumber', 'pymupdf')
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if not os.path.exists(file_path):
            return {'error': f"File not found: {file_path}"}
        
        if not file_path.lower().endswith('.pdf'):
            return {'error': f"Not a PDF file: {file_path}"}
        
        try:
            print(f"Processing PDF: {os.path.basename(file_path)}")
            
            # Try different methods based on preference
            if method == 'auto':
                # Try methods in order of preference
                methods = ['pdfplumber', 'pymupdf', 'pypdf']
                for m in methods:
                    if self.libraries.get(m.replace('pymupdf', 'PyMuPDF').replace('pdfplumber', 'pdfplumber').replace('pypdf', 'pypdf')):
                        result = self._extract_with_method(file_path, m)
                        if result and not result.get('error'):
                            return result
                
                # If all methods fail, return error
                return {'error': 'All extraction methods failed'}
            
            else:
                return self._extract_with_method(file_path, method)
            
        except Exception as e:
            return {'error': f"Error processing PDF: {str(e)}"}
    
    def _extract_with_method(self, file_path: str, method: str) -> Dict[str, Any]:
        """
        Extract text using a specific method
        
        Args:
            file_path: Path to PDF file
            method: Extraction method
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            if method == 'pdfplumber' and self.libraries['pdfplumber']:
                return self._extract_with_pdfplumber(file_path)
            elif method == 'pymupdf' and self.libraries['PyMuPDF']:
                return self._extract_with_pymupdf(file_path)
            elif method == 'pypdf' and self.libraries['pypdf']:
                return self._extract_with_pypdf(file_path)
            else:
                return {'error': f"Method {method} not available"}
                
        except Exception as e:
            return {'error': f"Error with method {method}: {str(e)}"}
    
    def _extract_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        """Extract text using pdfplumber (best for tables and layout)"""
        import pdfplumber
        
        text_content = []
        metadata = {
            'method': 'pdfplumber',
            'pages': 0,
            'tables': 0,
            'images': 0
        }
        
        with pdfplumber.open(file_path) as pdf:
            metadata['pages'] = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                
                # Count tables
                tables = page.extract_tables()
                if tables:
                    metadata['tables'] += len(tables)
                    # Add table content
                    for table in tables:
                        table_text = self._format_table(table)
                        text_content.append(f"--- Table on Page {page_num + 1} ---\n{table_text}")
                
                # Count images
                if hasattr(page, 'images'):
                    metadata['images'] += len(page.images)
        
        full_text = '\n\n'.join(text_content)
        
        return {
            'text': full_text,
            'metadata': metadata,
            'word_count': len(full_text.split()),
            'char_count': len(full_text),
            'extracted_at': datetime.now().isoformat(),
            'file_path': file_path
        }
    
    def _extract_with_pymupdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text using PyMuPDF (fast and accurate)"""
        import fitz
        
        doc = fitz.open(file_path)
        text_content = []
        metadata = {
            'method': 'pymupdf',
            'pages': len(doc),
            'images': 0,
            'links': 0
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text
            page_text = page.get_text()
            if page_text.strip():
                text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
            
            # Count images
            images = page.get_images()
            metadata['images'] += len(images)
            
            # Count links
            links = page.get_links()
            metadata['links'] += len(links)
        
        doc.close()
        
        full_text = '\n\n'.join(text_content)
        
        return {
            'text': full_text,
            'metadata': metadata,
            'word_count': len(full_text.split()),
            'char_count': len(full_text),
            'extracted_at': datetime.now().isoformat(),
            'file_path': file_path
        }
    
    def _extract_with_pypdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text using pypdf (basic but reliable)"""
        text_content = []
        metadata = {
            'method': 'pypdf',
            'pages': 0
        }
        
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            metadata['pages'] = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
        
        full_text = '\n\n'.join(text_content)
        
        return {
            'text': full_text,
            'metadata': metadata,
            'word_count': len(full_text.split()),
            'char_count': len(full_text),
            'extracted_at': datetime.now().isoformat(),
            'file_path': file_path
        }
    
    def _format_table(self, table: List[List[str]]) -> str:
        """Format a table for text output"""
        if not table:
            return ""
        
        formatted_rows = []
        for row in table:
            if row:  # Skip empty rows
                formatted_row = ' | '.join(str(cell) if cell else '' for cell in row)
                formatted_rows.append(formatted_row)
        
        return '\n'.join(formatted_rows)
    
    def extract_text_from_bytes(self, pdf_bytes: bytes, filename: str = "uploaded.pdf") -> Dict[str, Any]:
        """
        Extract text from PDF bytes (for uploaded files)
        
        Args:
            pdf_bytes: PDF file bytes
            filename: Original filename
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Save bytes to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_path = tmp_file.name
            
            # Extract text
            result = self.extract_text_from_file(tmp_path)
            
            # Clean up
            os.unlink(tmp_path)
            
            # Update metadata
            if 'metadata' in result:
                result['metadata']['original_filename'] = filename
                result['metadata']['file_size'] = len(pdf_bytes)
            
            return result
            
        except Exception as e:
            return {'error': f"Error processing PDF bytes: {str(e)}"}
    
    def validate_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Validate PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Validation result
        """
        try:
            if not os.path.exists(file_path):
                return {'valid': False, 'error': 'File not found'}
            
            if not file_path.lower().endswith('.pdf'):
                return {'valid': False, 'error': 'Not a PDF file'}
            
            # Try to open with pypdf
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                # Check if encrypted
                is_encrypted = pdf_reader.is_encrypted
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                return {
                    'valid': True,
                    'pages': page_count,
                    'encrypted': is_encrypted,
                    'file_size': file_size,
                    'file_path': file_path
                }
                
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def get_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            PDF metadata
        """
        try:
            metadata = {}
            
            # Try pypdf first
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    if pdf_reader.metadata:
                        metadata.update({
                            'title': pdf_reader.metadata.get('/Title', ''),
                            'author': pdf_reader.metadata.get('/Author', ''),
                            'subject': pdf_reader.metadata.get('/Subject', ''),
                            'creator': pdf_reader.metadata.get('/Creator', ''),
                            'producer': pdf_reader.metadata.get('/Producer', ''),
                            'creation_date': pdf_reader.metadata.get('/CreationDate', ''),
                            'modification_date': pdf_reader.metadata.get('/ModDate', '')
                        })
            except Exception:
                pass
            
            # Try PyMuPDF for additional metadata
            if self.libraries['PyMuPDF']:
                try:
                    import fitz
                    doc = fitz.open(file_path)
                    doc_metadata = doc.metadata
                    doc.close()
                    
                    if doc_metadata:
                        metadata.update({
                            'format': doc_metadata.get('format', ''),
                            'encryption': doc_metadata.get('encryption', ''),
                            'keywords': doc_metadata.get('keywords', '')
                        })
                except Exception:
                    pass
            
            # Add file system metadata
            stat = os.stat(file_path)
            metadata.update({
                'file_size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat.st_atime).isoformat()
            })
            
            return metadata
            
        except Exception as e:
            return {'error': f"Error extracting metadata: {str(e)}"}
    
    def split_pdf_text(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
        """
        Split PDF text into chunks for processing
        
        Args:
            text: Extracted text
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Use provided values or defaults if config is None
        if chunk_size is None:
            chunk_size = self.config.CHUNK_SIZE if self.config else 1000
        if chunk_overlap is None:
            chunk_overlap = self.config.CHUNK_OVERLAP if self.config else 200
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for paragraph break
                    para_end = text.rfind('\n\n', start, end)
                    if para_end > start:
                        end = para_end + 2
                    else:
                        # Look for any line break
                        line_end = text.rfind('\n', start, end)
                        if line_end > start:
                            end = line_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - chunk_overlap
        
        return chunks
    
    def clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers (basic)
        text = re.sub(r'Page \d+', '', text)
        
        # Remove email addresses (optional)
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove URLs (optional)
        text = re.sub(r'https?://\S+', '', text)
        
        # Fix common OCR errors
        text = text.replace('ﬁ', 'fi')
        text = text.replace('ﬂ', 'fl')
        text = text.replace('ﬀ', 'ff')
        text = text.replace('ﬃ', 'ffi')
        text = text.replace('ﬄ', 'ffl')
        
        return text.strip()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get PDF processing statistics
        
        Returns:
            Processing statistics
        """
        return {
            'available_libraries': self.libraries,
            'supported_formats': self.supported_formats,
            'enhanced_features': PDF_ENHANCED,
            'config': {
                'chunk_size': self.config.CHUNK_SIZE if self.config else 1000,
                'chunk_overlap': self.config.CHUNK_OVERLAP if self.config else 200
            }
        }
