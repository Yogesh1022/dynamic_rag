import re
import logging
from typing import List, Tuple, Optional
from pathlib import Path
from PyPDF2 import PdfReader
from PIL import Image

from app.services.ingestion.ocr_service import get_ocr_service
from app.core.exceptions import OCRException

logger = logging.getLogger(__name__)


class DocumentParser:
    """Service for parsing and extracting text from various document formats."""
    
    def __init__(self):
        """Initialize document parser."""
        self.ocr_service = get_ocr_service()
    
    def parse_pdf(self, file_path: str) -> Tuple[str, int, bool]:
        """
        Parse PDF and extract text.
        
        Strategy:
        1. Try to extract text directly (for text-selectable PDFs) - FAST
        2. If no meaningful text found, use OCR (for scanned PDFs) - SLOW
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, num_pages, used_ocr)
            
        Raises:
            OCRException: If parsing fails
        """
        try:
            logger.info(f"Parsing PDF: {file_path}")
            
            # First, try direct text extraction
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            
            logger.info(f"PDF has {num_pages} pages")
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            combined_text = "\n\n".join(text_parts)
            
            # Check if extracted text is meaningful
            if self.ocr_service.is_text_meaningful(combined_text):
                logger.info(f"Successfully extracted text directly ({len(combined_text)} chars)")
                cleaned_text = self.clean_text(combined_text)
                return cleaned_text, num_pages, False
            
            # Fallback to OCR for scanned PDFs
            logger.info("No meaningful text found, falling back to OCR")
            page_texts = self.ocr_service.extract_text_from_pdf_images(file_path)
            
            combined_text = "\n\n".join(page_texts)
            cleaned_text = self.clean_text(combined_text)
            
            logger.info(f"OCR extraction completed ({len(cleaned_text)} chars)")
            return cleaned_text, num_pages, True
            
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {str(e)}")
            raise OCRException(
                f"Failed to parse PDF: {str(e)}",
                details={"file_path": file_path}
            )
    
    def parse_image(self, file_path: str) -> str:
        """
        Parse image and extract text using OCR.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted and cleaned text
            
        Raises:
            OCRException: If parsing fails
        """
        try:
            logger.info(f"Parsing image: {file_path}")
            
            # Extract text using OCR
            text = self.ocr_service.extract_text_from_image(file_path)
            
            # Clean text
            cleaned_text = self.clean_text(text)
            
            logger.info(f"Image parsing completed ({len(cleaned_text)} chars)")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Failed to parse image {file_path}: {str(e)}")
            raise OCRException(
                f"Failed to parse image: {str(e)}",
                details={"file_path": file_path}
            )
    
    def parse_document(self, file_path: str) -> Tuple[str, dict]:
        """
        Parse any supported document type and extract text.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Tuple of (extracted_text, metadata_dict)
            
        Raises:
            OCRException: If file type not supported or parsing fails
        """
        path = Path(file_path)
        file_ext = path.suffix.lower()
        
        metadata = {
            "filename": path.name,
            "file_type": file_ext,
            "used_ocr": False,
            "num_pages": 1,
        }
        
        if file_ext == ".pdf":
            text, num_pages, used_ocr = self.parse_pdf(file_path)
            metadata["num_pages"] = num_pages
            metadata["used_ocr"] = used_ocr
            return text, metadata
        
        elif file_ext in [".png", ".jpg", ".jpeg", ".tiff", ".tif"]:
            text = self.parse_image(file_path)
            metadata["used_ocr"] = True
            return text, metadata
        
        else:
            raise OCRException(
                f"Unsupported file type: {file_ext}",
                details={"file_path": file_path, "file_type": file_ext}
            )
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Operations:
        - Remove excessive whitespace
        - Normalize line breaks
        - Remove special characters (but keep punctuation)
        - Strip leading/trailing whitespace
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline (paragraph separation)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # Remove weird Unicode characters but keep common punctuation
        text = re.sub(r'[^\x00-\x7F\u0080-\uFFFF]+', '', text)
        
        # Remove lines with only whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        
        text = '\n'.join(lines)
        
        # Final strip
        return text.strip()
    
    def extract_metadata_from_pdf(self, file_path: str) -> dict:
        """
        Extract metadata from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            reader = PdfReader(file_path)
            metadata = reader.metadata or {}
            
            return {
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
                "creator": metadata.get("/Creator", ""),
                "producer": metadata.get("/Producer", ""),
                "creation_date": str(metadata.get("/CreationDate", "")),
                "num_pages": len(reader.pages),
            }
        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {str(e)}")
            return {}


# Singleton instance
_parser_service = None


def get_parser_service() -> DocumentParser:
    """Get or create document parser singleton."""
    global _parser_service
    if _parser_service is None:
        _parser_service = DocumentParser()
    return _parser_service
