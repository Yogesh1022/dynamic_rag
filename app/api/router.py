
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.schemas.schemas import UploadResponse, QueryRequest, QueryResponse
from app.core.extractor import extract_text_from_pdf, extract_text_from_image
from app.core.embedding import embed_text
from app.core.retriever import Retriever
from app.core.gemini_client import GeminiClient
from app.core.config import MAX_CHUNK_SIZE, TOP_K
import re
import logging
import os
import shutil

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")
retriever = Retriever(embedding_dim=384)
gemini_client = GeminiClient()
all_chunks = []

def chunk_text(text: str, max_chunk_size: int) -> list:
    logger.debug("Chunking text: %s", text[:100])
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ""
    for s in sentences:
        if len(current_chunk) + len(s) < max_chunk_size:
            current_chunk += s + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = s + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    logger.debug("Chunks created: %d", len(chunks))
    return chunks

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    logger.info("Step 1: Received upload request for file: %s, content_type: %s", file.filename, file.content_type)
    content_type = file.content_type
    try:
        # Step 2: Check file size
        logger.info("Step 2: Checking file size")
        file.file.seek(0, 2)
        file_size = file.file.tell()
        await file.seek(0)
        logger.debug("File size: %d bytes", file_size)
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            logger.error("File too large: %d bytes", file_size)
            raise HTTPException(status_code=400, detail="File too large, max 10MB")

        # Step 3: Save file to disk
        logger.info("Step 3: Saving file to disk")
        upload_dir = os.path.join(os.getcwd(), "uploads")
        logger.debug("Current working directory: %s", os.getcwd())
        logger.debug("Upload directory: %s", upload_dir)
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        logger.debug("Saving file to: %s", file_path)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info("File saved successfully to: %s", file_path)
        except Exception as save_err:
            logger.error("Failed to save file: %s", str(save_err))
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(save_err)}")
        file.file.seek(0)  # Reset file pointer

        # Step 4: Read file for processing
        logger.info("Step 4: Reading file for processing")
        file_bytes = await file.read()
        logger.debug("File read, size: %d bytes", len(file_bytes))

        # Step 5: Text extraction
        logger.info("Step 5: Extracting text")
        text = ""
        if content_type == "application/pdf":
            logger.debug("Processing PDF")
            try:
                text = extract_text_from_pdf(file_bytes)
            except Exception as pdf_err:
                logger.error("PDF text extraction failed: %s", str(pdf_err))
                return UploadResponse(message=f"File saved to {file_path}, but PDF text extraction failed: {str(pdf_err)}")
        elif content_type.startswith("image/"):
            logger.debug("Processing image")
            try:
                text = extract_text_from_image(file_bytes)
            except Exception as img_err:
                logger.error("Image text extraction failed: %s", str(img_err))
                return UploadResponse(message=f"File saved to {file_path}, but image text extraction failed: {str(img_err)}")
        else:
            logger.error("Unsupported file type: %s", content_type)
            raise HTTPException(status_code=400, detail="Unsupported file type. Upload PDF or image.")

        logger.debug("Extracted text: %s", text[:100] if text else "No text")
        if not text.strip():
            logger.warning("No text extracted from file")
            return UploadResponse(message=f"File saved to {file_path}, but no text extracted for indexing")

        # Step 6: Process text
        logger.info("Step 6: Chunking and embedding text")
        chunks = chunk_text(text, max_chunk_size=MAX_CHUNK_SIZE)
        if not chunks:
            logger.warning("No chunks created from text")
            return UploadResponse(message=f"File saved to {file_path}, but no chunks created for indexing")

        embeddings = [embed_text(c) for c in chunks]
        logger.debug("Generated %d embeddings", len(embeddings))
        retriever.add_documents(chunks, embeddings)
        all_chunks.extend(chunks)
        logger.debug("Processed and indexed %d chunks", len(chunks))

        logger.info("Upload completed successfully")
        return UploadResponse(message=f"File processed, indexed with {len(chunks)} chunks, and saved to {file_path}")
    except Exception as e:
        logger.error("Upload failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def query_answer(query: QueryRequest):
    logger.debug("Received query: %s", query.question)
    if not all_chunks:
        logger.warning("No documents loaded for querying")
        return QueryResponse(answer="No documents have been uploaded with extractable text. Please upload a file with readable text.")

    try:
        query_embedding = embed_text(query.question)
        retrieved = retriever.retrieve(query_embedding, top_k=TOP_K)
        if not retrieved:
            logger.warning("No relevant documents found for query")
            return QueryResponse(answer="No relevant information found in the uploaded documents.")

        context = "\n\n".join([chunk for chunk, _ in retrieved])
        answer = await gemini_client.generate_answer(context=context, question=query.question)
        logger.debug("Generated answer: %s", answer[:100])
        return QueryResponse(answer=answer)
    except Exception as e:
        logger.error("Query processing failed: %s", str(e))
        return QueryResponse(answer=f"Failed to generate answer due to an error: {str(e)}")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logger.debug("Serving home page")
    return templates.TemplateResponse("index.html", {"request": request})
