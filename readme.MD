DynamicRAG-Gemini-FastAPI
A modular, extensible Q&A system powered by Gemini LLM, FastAPI, and FAISS for dynamic file-based retrieval-augmented generation (RAG).
Features

Upload PDFs or images for text extraction (PyMuPDF for PDFs, Tesseract OCR for images).
Text chunking, embedding (sentence-transformers), and retrieval (FAISS).
Query answering using Gemini LLM with retrieved context.
Responsive Bootstrap 5 frontend.

Setup

Clone the repository:
git clone <repository_url>
cd DynamicRAG-Gemini-FastAPI


Create a .env file in the root directory:
GEMINI_API_KEY=your_gemini_api_key_here


Install Tesseract OCR:

Ubuntu: sudo apt install tesseract-ocr
Windows: Download from https://github.com/tesseract-ocr/tesseract/wiki
Mac: brew install tesseract


Install Python dependencies:
pip install -r requirements.txt


Run the FastAPI server:
uvicorn app.main:app --reload


Access the app:Open http://localhost:8000 in your browser.


Usage

Upload a PDF or image via the frontend to extract and index text.
Ask a question related to the uploaded content, and the system will retrieve relevant chunks and generate an answer using Gemini LLM.

Notes

The system uses an in-memory FAISS index; for production, consider persisting to disk or a database.
Replace the Gemini API URL and model name in config.py and gemini_client.py with actual values.
Ensure your Gemini API key is valid and has appropriate permissions.

Potential Improvements

Add user session management for multi-user support.
Persist FAISS index to disk or cloud storage.
Implement streaming responses from Gemini LLM.
Deploy to AWS, GCP, or Azure for scalability.

