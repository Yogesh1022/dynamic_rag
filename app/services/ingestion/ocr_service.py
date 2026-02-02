import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
import io
import logging
from typing import List, Union
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import OCRException

logger = logging.getLogger(__name__)


class OCRService:
    """Service for extracting text from images and scanned PDFs using OCR."""
    
    def __init__(self):
        """Initialize OCR service with Tesseract configuration."""
        # Set Tesseract command path if specified
        if settings.TESSERACT_CMD and settings.TESSERACT_CMD != "tesseract":
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        
        self.lang = settings.TESSERACT_LANG
        self.dpi = settings.OCR_DPI
    
    def extract_text_from_image(self, image_path: Union[str, Path]) -> str:
        """
        Extract text from an image file using Tesseract OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text content
            
        Raises:
            OCRException: If OCR processing fails
        """
        try:
            logger.info(f"Starting OCR extraction from image: {image_path}")
            
            # Open image
            image = Image.open(image_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                image,
                lang=self.lang,
                config='--psm 1'  # Automatic page segmentation with OSD
            )
            
            logger.info(f"OCR extraction completed. Extracted {len(text)} characters")
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
            raise OCRException(
                f"Failed to extract text from image: {str(e)}",
                details={"image_path": str(image_path)}
            )
    
    def extract_text_from_pdf_images(
        self,
        pdf_path: Union[str, Path],
        first_page: int = None,
        last_page: int = None
    ) -> List[str]:
        """
        Convert PDF pages to images and extract text using OCR.
        
        This is used for scanned PDFs that don't have selectable text.
        
        Args:
            pdf_path: Path to the PDF file
            first_page: First page to process (1-indexed)
            last_page: Last page to process (1-indexed)
            
        Returns:
            List of extracted text per page
            
        Raises:
            OCRException: If OCR processing fails
        """
        try:
            logger.info(f"Converting PDF to images for OCR: {pdf_path}")
            
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=first_page,
                last_page=last_page,
                fmt='jpeg',
                thread_count=2,
            )
            
            logger.info(f"Converted {len(images)} pages to images")
            
            # Extract text from each page
            page_texts = []
            for i, image in enumerate(images, start=1):
                logger.debug(f"Processing page {i}/{len(images)}")
                
                text = pytesseract.image_to_string(
                    image,
                    lang=self.lang,
                    config='--psm 1'
                )
                
                page_texts.append(text.strip())
            
            logger.info(f"OCR extraction completed for {len(page_texts)} pages")
            return page_texts
            
        except Exception as e:
            logger.error(f"OCR extraction failed for PDF {pdf_path}: {str(e)}")
            raise OCRException(
                f"Failed to extract text from PDF images: {str(e)}",
                details={"pdf_path": str(pdf_path)}
            )
    
    def extract_text_from_pdf_bytes(
        self,
        pdf_bytes: bytes,
        first_page: int = None,
        last_page: int = None
    ) -> List[str]:
        """
        Convert PDF bytes to images and extract text using OCR.
        
        Args:
            pdf_bytes: PDF file content as bytes
            first_page: First page to process (1-indexed)
            last_page: Last page to process (1-indexed)
            
        Returns:
            List of extracted text per page
            
        Raises:
            OCRException: If OCR processing fails
        """
        try:
            logger.info("Converting PDF bytes to images for OCR")
            
            # Convert PDF bytes to images
            images = convert_from_bytes(
                pdf_bytes,
                dpi=self.dpi,
                first_page=first_page,
                last_page=last_page,
                fmt='jpeg',
                thread_count=2,
            )
            
            logger.info(f"Converted {len(images)} pages to images")
            
            # Extract text from each page
            page_texts = []
            for i, image in enumerate(images, start=1):
                logger.debug(f"Processing page {i}/{len(images)}")
                
                text = pytesseract.image_to_string(
                    image,
                    lang=self.lang,
                    config='--psm 1'
                )
                
                page_texts.append(text.strip())
            
            logger.info(f"OCR extraction completed for {len(page_texts)} pages")
            return page_texts
            
        except Exception as e:
            logger.error(f"OCR extraction failed for PDF bytes: {str(e)}")
            raise OCRException(
                f"Failed to extract text from PDF bytes: {str(e)}"
            )
    
    def is_text_meaningful(self, text: str, min_length: int = 50) -> bool:
        """
        Check if extracted text is meaningful (not just noise/garbage).
        
        Args:
            text: Extracted text to validate
            min_length: Minimum length to consider meaningful
            
        Returns:
            True if text appears meaningful, False otherwise
        """
        if not text or len(text.strip()) < min_length:
            return False
        
        # Check if text has reasonable word-to-character ratio
        words = text.split()
        if len(words) < 5:
            return False
        
        # Check average word length (garbage text often has very long "words")
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len > 15:  # Suspiciously long average
            return False
        
        return True


# Singleton instance
_ocr_service = None


def get_ocr_service() -> OCRService:
    """Get or create OCR service singleton."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
