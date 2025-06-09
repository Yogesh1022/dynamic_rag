import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in .env file")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://gemini.googleapis.com/v1/")  # Replace with actual Gemini API URL

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OCR_LANG = "eng"

MAX_CHUNK_SIZE = 500  # Characters for text chunking
TOP_K = 5 # Number of chunks to retrieve