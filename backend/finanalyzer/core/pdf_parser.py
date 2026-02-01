"""
PDF Parser module for extracting text, tables, and structure from financial reports.
Supports both digital PDFs and scanned documents (OCR).
"""

# Standard library
import gc
import io
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..config import config

# Third-party
import camelot
import pdfplumber
import pytesseract
from loguru import logger
from PIL import Image
from PyPDF2 import PdfReader

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False
    logger.warning("pdf2image not found. OCR capabilities will be limited.")

# Note: tabula-py requires Java runtime
try:
    import tabula
    HAS_TABULA = True
except ImportError:
    HAS_TABULA = False


class PDFParser:
    """
    PDF Parser for financial reports.
    Handles both digital and scanned PDFs with OCR support.
    """
    
    def __init__(self, pdf_path: Union[str, Path], use_ocr: bool = False):
        """
        Initialize PDF Parser.
        
        Args:
            pdf_path: Path to PDF file
            use_ocr: Force OCR even for digital PDFs
        """
        self.pdf_path = Path(pdf_path)
        self.use_ocr = use_ocr
        self.metadata = {}
        self.pages_text = []
        self.tables = []
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Initialized PDFParser for: {self.pdf_path}")
    
    def extract(self) -> Dict:
        """
        Main extraction method.
        
        Returns:
            Dictionary containing extracted data:
            - metadata: PDF metadata
            - text: Full text content
            - pages: List of page texts
            - tables: Extracted tables
            - structure: Document structure
        """
        logger.info("Starting PDF extraction...")
        
        # Extract metadata
        self.metadata = self._extract_metadata()
        
        # Determine if OCR is needed
        needs_ocr = self.use_ocr or self._is_scanned_pdf()
        
        if needs_ocr:
            logger.info("Using OCR for text extraction")
            self.pages_text = self._extract_text_ocr()
        else:
            logger.info("Using digital text extraction")
            self.pages_text = self._extract_text_digital()
        
        # Extract tables
        self.tables = self._extract_tables()
        
        # Analyze structure
        structure = self._analyze_structure()
        
        result = {
            'metadata': self.metadata,
            'text': '\n\n'.join(self.pages_text),
            'pages': self.pages_text,
            'tables': self.tables,
            'structure': structure,
            'total_pages': len(self.pages_text)
        }
        
        logger.info(f"Extraction complete: {len(self.pages_text)} pages, {len(self.tables)} tables")
        return result
    
    def _extract_metadata(self) -> Dict:
        """Extract PDF metadata."""
        try:
            reader = PdfReader(str(self.pdf_path))
            metadata = reader.metadata
            
            return {
                'title': metadata.get('/Title', ''),
                'author': metadata.get('/Author', ''),
                'subject': metadata.get('/Subject', ''),
                'creator': metadata.get('/Creator', ''),
                'producer': metadata.get('/Producer', ''),
                'creation_date': metadata.get('/CreationDate', ''),
                'modification_date': metadata.get('/ModDate', ''),
                'num_pages': len(reader.pages)
            }
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return {}
    
    def _is_scanned_pdf(self) -> bool:
        """
        Detect if PDF is scanned (image-based) or digital.
        
        Returns:
            True if scanned, False if digital
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Check first few pages
                for page in pdf.pages[:3]:
                    text = page.extract_text()
                    if text and len(text.strip()) > 100:
                        return False  # Digital PDF with extractable text
            return True  # Likely scanned
        except Exception as e:
            logger.warning(f"Error detecting PDF type: {e}")
            return True  # Default to OCR if uncertain
    
    def _extract_text_digital(self) -> List[str]:
        """Extract text from digital PDF."""
        pages = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    pages.append(text)
                    logger.debug(f"Extracted page {i+1}: {len(text)} chars")
        except Exception as e:
            logger.error(f"Error extracting digital text: {e}")
            # Fallback to OCR
            pages = self._extract_text_ocr()
        
        return pages
    
    def _extract_text_ocr(self) -> List[str]:
        """Extract text using OCR (for scanned PDFs)."""
        pages = []
        
        try:
            # Convert PDF to images
            images = convert_from_path(str(self.pdf_path), dpi=config.pdf.OCR_DPI)
            
            for i, image in enumerate(images):
                # Perform OCR
                text = pytesseract.image_to_string(image, lang='eng')
                pages.append(text)
                logger.debug(f"OCR page {i+1}: {len(text)} chars")
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            raise
        
        return pages
    
    def _extract_tables(self) -> List[Dict]:
        """
        Extract tables from PDF using targeted and lightweight methods.
        Uses identified structure to target heavy extraction only on relevant pages.
        """
        all_tables = []
        target_pages = []
        
        # 1. Determine target pages from structure
        structure = self._analyze_structure()
        for section in structure.values():
            if section.get('found') and section.get('page'):
                target_pages.append(section['page'])
        
        # Add surrounding pages just in case
        extra_pages = []
        for p in target_pages:
            extra_pages.extend([p+1, p+2])
        target_pages = sorted(list(set(target_pages + extra_pages)))

        logger.info(f"Targeting table extraction on pages: {target_pages or 'default'}")

        # Method 1: pdfplumber (Fastest & Lightest - Use for ALL pages)
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Only check first 20 pages or target pages to save memory on huge PDFs
                    if page_num > config.pdf.MAX_PAGES_FOR_TABLES and (page_num + 1) not in target_pages:
                        continue
                        
                    tables = page.extract_tables()
                    for i, table in enumerate(tables):
                        if table:
                            all_tables.append({
                                'method': 'pdfplumber',
                                'table_id': len(all_tables),
                                'page': page_num + 1,
                                'data': table
                            })
        except Exception as e:
            logger.warning(f"pdfplumber table extraction failed: {e}")

        # Method 2: Camelot (Optimized for Low RAM)
        # We process pages sequentially with garbage collection to avoid OOM on Streamlit Cloud.
        if target_pages:
            import gc
            logger.info(f"Attempting Camelot extraction on {len(target_pages)} pages (sequential)...")
            
            for p in target_pages:
                try:
                    # Read ONE page at a time
                    tables_camelot = camelot.read_pdf(
                        str(self.pdf_path),
                        pages=str(p),
                        flavor='stream', 
                        suppress_stdout=True
                    )
                    
                    for table in tables_camelot:
                        all_tables.append({
                            'method': 'camelot',
                            'table_id': len(all_tables),
                            'page': table.page,
                            'data': table.df.to_dict('records'),
                            'dataframe': table.df
                        })
                    
                    # Cleanup immediately to free RAM
                    del tables_camelot
                    gc.collect()
                    
                except Exception as e:
                    logger.warning(f"Camelot extraction skipped for page {p}: {e}")

        logger.info(f"Total tables extracted: {len(all_tables)}")
        return all_tables
    
    def _analyze_structure(self) -> Dict:
        """
        Analyze document structure to identify sections.
        
        Returns:
            Dictionary with identified sections and their page ranges
        """
        full_text = '\n'.join(self.pages_text)
        
        # Common section patterns in financial reports
        section_patterns = {
            'income_statement': [
                r'(?i)consolidated\s+statements?\s+of\s+(operations|income)',
                r'(?i)income\s+statement',
                r'(?i)profit\s+and\s+loss',
                r'(?i)statement\s+of\s+comprehensive\s+income'
            ],
            'balance_sheet': [
                r'(?i)consolidated\s+balance\s+sheets?',
                r'(?i)statements?\s+of\s+financial\s+position',
                r'(?i)balance\s+sheet'
            ],
            'cash_flow': [
                r'(?i)consolidated\s+statements?\s+of\s+cash\s+flows?',
                r'(?i)cash\s+flow\s+statement',
                r'(?i)statement\s+of\s+cash\s+flows?'
            ],
            'notes': [
                r'(?i)notes\s+to\s+(consolidated\s+)?financial\s+statements',
                r'(?i)notes\s+to\s+the\s+accounts'
            ],
            'accounting_policies': [
                r'(?i)significant\s+accounting\s+policies',
                r'(?i)summary\s+of\s+accounting\s+policies',
                r'(?i)basis\s+of\s+preparation'
            ]
        }
        
        structure = {}
        
        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, full_text))
                if matches:
                    # Find page number for first match
                    match_pos = matches[0].start()
                    page_num = self._get_page_number(match_pos)
                    
                    structure[section_name] = {
                        'found': True,
                        'page': page_num,
                        'pattern_matched': pattern,
                        'total_matches': len(matches)
                    }
                    logger.debug(f"Found {section_name} on page {page_num}")
                    break
            else:
                structure[section_name] = {'found': False}
        
        return structure
    
    def _get_page_number(self, char_position: int) -> int:
        """
        Get page number from character position in full text.
        
        Args:
            char_position: Character position in concatenated text
            
        Returns:
            Page number (1-indexed)
        """
        current_pos = 0
        for i, page_text in enumerate(self.pages_text):
            current_pos += len(page_text) + 2  # +2 for '\n\n'
            if current_pos > char_position:
                return i + 1
        return len(self.pages_text)
    
    def extract_page_range(self, start_page: int, end_page: int) -> str:
        """
        Extract text from specific page range.
        
        Args:
            start_page: Starting page (1-indexed)
            end_page: Ending page (1-indexed)
            
        Returns:
            Concatenated text from page range
        """
        if start_page < 1 or end_page > len(self.pages_text):
            raise ValueError(f"Invalid page range: {start_page}-{end_page}")
        
        return '\n\n'.join(self.pages_text[start_page-1:end_page])
    
    def search_text(self, pattern: str, case_sensitive: bool = False) -> List[Dict]:
        """
        Search for text pattern across all pages.
        
        Args:
            pattern: Regex pattern to search
            case_sensitive: Whether search is case-sensitive
            
        Returns:
            List of matches with page numbers and context
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        matches = []
        
        for page_num, page_text in enumerate(self.pages_text, 1):
            for match in re.finditer(pattern, page_text, flags):
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(page_text), match.end() + 50)
                context = page_text[start:end]
                
                matches.append({
                    'page': page_num,
                    'match': match.group(),
                    'context': context,
                    'position': match.start()
                })
        
        return matches


# Example usage
if __name__ == "__main__":
    # Configure logging
    logger.add("pdf_parser.log", rotation="10 MB")
    
    # Example: Parse a financial report
    parser = PDFParser("data/sample_reports/apple_10k_2023.pdf")
    data = parser.extract()
    
    print(f"Extracted {data['total_pages']} pages")
    print(f"Found {len(data['tables'])} tables")
    print(f"Structure: {data['structure']}")
