
import io
import logging
from PIL import Image
import pytesseract
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF file provided as bytes.
    
    Args:
        pdf_bytes: Bytes of the PDF file.
    
    Returns:
        Extracted text as a string.
    """
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text += page.get_text()
        pdf_document.close()
        logger.debug("Extracted text from PDF: %s", text[:100])
        return text
    except Exception as e:
        logger.error("Failed to extract text from PDF: %s", str(e))
        raise

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from an image file provided as bytes using OCR.
    
    Args:
        image_bytes: Bytes of the image file.
    
    Returns:
        Extracted text as a string.
    """
    try:
        logger.debug("Opening image for OCR")
        image = Image.open(io.BytesIO(image_bytes))
        logger.debug("Image opened successfully, format: %s, size: %s", image.format, image.size)
        
        logger.debug("Running Tesseract OCR with language 'eng'")
        text = pytesseract.image_to_string(image, lang='eng')
        if not text.strip():
            logger.warning("No text extracted from image")
        else:
            logger.debug("Extracted text from image: %s", text[:100])
        return text
    except pytesseract.TesseractNotFoundError as e:
        logger.error("Tesseract executable not found: %s", str(e))
        raise Exception("Tesseract is not installed or not in PATH")
    except pytesseract.TesseractError as e:
        logger.error("Tesseract OCR failed: %s", str(e))
        raise Exception(f"Tesseract OCR error: {str(e)}")
    except Exception as e:
        logger.error("Failed to process image for OCR: %s", str(e))
        raise
