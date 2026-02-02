from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid
import os
import shutil
from datetime import datetime
import logging

from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
    DocumentStatus,
    DocumentMetadata,
    IndexingRequest,
    IndexingResponse,
)
from app.models import Document, Chunk
from app.api.deps import get_db, get_qdrant_client
from app.core.security import verify_api_key
from app.core.config import settings
from app.core.exceptions import FileUploadException, DocumentNotFoundException
from app.services.ingestion.parser import get_parser_service
from app.services.ingestion.chunker import get_chunker_service
from app.services.retrieval.embedding import get_embedding_service
from app.services.retrieval.vector_store import get_vector_store_service

logger = logging.getLogger(__name__)

router = APIRouter()


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file extension
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise FileUploadException(
            f"File type .{file_ext} not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # File size check will be done during upload


async def process_document_background(
    document_id: str,
    file_path: str,
    filename: str,
):
    """
    Background task to process uploaded document.
    
    Steps:
    1. Parse document (OCR if needed)
    2. Chunk text
    3. Generate embeddings
    4. Store in vector database
    5. Store chunks in SQL database
    6. Update document status
    """
    from app.api.deps import AsyncSessionLocal, get_qdrant_client
    
    logger.info(f"Background processing started for document: {document_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get document from DB
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                logger.error(f"Document not found: {document_id}")
                return
            
            # Update status to processing
            document.status = DocumentStatus.PROCESSING.value
            await db.commit()
            
            # 1. Parse document
            parser = get_parser_service()
            text, parse_metadata = parser.parse_document(file_path)
            
            logger.info(
                f"Parsed document {document_id}: "
                f"{len(text)} chars, {parse_metadata.get('num_pages', 1)} pages"
            )
            
            # 2. Chunk text
            chunker = get_chunker_service()
            chunks = chunker.chunk_text(
                text,
                metadata={
                    "document_id": document_id,
                    "filename": filename,
                    **parse_metadata,
                }
            )
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            
            # 3. Generate embeddings
            embedding_service = get_embedding_service()
            chunk_texts = [chunk["content"] for chunk in chunks]
            
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # 4. Store in vector database
            qdrant_client = get_qdrant_client()
            vector_store = get_vector_store_service(qdrant_client)
            
            # Ensure collection exists
            embedding_dim = len(embeddings[0]) if embeddings else settings.EMBEDDING_DIMENSION
            vector_store.ensure_collection_exists(dimension=embedding_dim)
            
            # Prepare payloads and IDs
            vector_ids = []
            payloads = []
            
            for i, chunk in enumerate(chunks):
                vector_id = f"{document_id}_chunk_{i}"
                vector_ids.append(vector_id)
                
                payload = {
                    "document_id": document_id,
                    "chunk_id": vector_id,
                    "chunk_index": i,
                    "content": chunk["content"],
                    "filename": filename,
                    "page": chunk.get("metadata", {}).get("page"),
                    **chunk.get("metadata", {}),
                }
                payloads.append(payload)
            
            # Upsert vectors
            logger.info(f"Storing {len(embeddings)} vectors in Qdrant...")
            vector_store.upsert_vectors(
                vectors=embeddings,
                payloads=payloads,
                ids=vector_ids,
            )
            
            logger.info(f"Vectors stored successfully")
            
            # 5. Store chunks in database
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                
                db_chunk = Chunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=chunk["content"],
                    chunk_index=chunk["chunk_index"],
                    chunk_size=chunk["chunk_size"],
                    page_number=chunk.get("metadata", {}).get("page"),
                    vector_id=vector_ids[i],
                    embedding_model=settings.OLLAMA_EMBEDDING_MODEL,
                    doc_metadata=chunk.get("metadata", {}),
                )
                db.add(db_chunk)
            
            # 6. Update document metadata
            document.status = DocumentStatus.COMPLETED.value
            document.total_chunks = len(chunks)
            document.total_pages = parse_metadata.get("num_pages", 1)
            document.total_characters = len(text)
            document.used_ocr = parse_metadata.get("used_ocr", False)
            document.processed_at = datetime.utcnow()
            document.doc_metadata = parse_metadata
            
            await db.commit()
            
            logger.info(
                f"Document processing completed: {document_id} "
                f"({len(chunks)} chunks, {len(embeddings)} vectors)"
            )
            
        except Exception as e:
            logger.error(f"Document processing failed for {document_id}: {str(e)}")
            
            # Update document status to failed
            if document:
                document.status = DocumentStatus.FAILED.value
                document.error_message = str(e)
                document.retry_count += 1
                await db.commit()
            
            raise


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload document",
    description="Upload a PDF or image file for indexing",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file (PDF, PNG, JPG, JPEG, TIFF)"),
    description: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> DocumentUploadResponse:
    """
    Upload a document for processing and indexing.
    
    The document will be:
    1. Saved to disk
    2. Queued for background processing (OCR, chunking, embedding)
    3. Indexed in the vector store
    """
    try:
        # Validate file
        validate_file(file)
        
        # Generate unique document ID
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # Create upload directory if not exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        file_ext = file.filename.split(".")[-1].lower()
        file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.{file_ext}")
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Check file size
        max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            os.remove(file_path)
            raise FileUploadException(
                f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum "
                f"allowed size ({settings.MAX_UPLOAD_SIZE_MB} MB)"
            )
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Create document in database
        document = Document(
            id=document_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_ext,
            description=description,
            tags=tag_list,
            status=DocumentStatus.UPLOADED.value,
        )
        
        db.add(document)
        await db.commit()
        
        logger.info(
            f"Document uploaded: {document_id} | "
            f"File: {file.filename} | "
            f"Size: {file_size / 1024:.2f} KB"
        )
        
        # Queue background processing
        background_tasks.add_task(
            process_document_background,
            document_id,
            file_path,
            file.filename,
        )
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            status=DocumentStatus.PROCESSING,
            message="Document uploaded successfully, processing in background",
            uploaded_at=datetime.utcnow(),
        )
    
    except FileUploadException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise FileUploadException(f"Failed to upload document: {str(e)}")


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List documents",
    description="Get a paginated list of all uploaded documents",
)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> DocumentListResponse:
    """Get list of all documents with pagination."""
    
    # Build query
    query = select(Document)
    
    # Apply status filter
    if status_filter:
        query = query.where(Document.status == status_filter.value)
    
    # Order by upload date (newest first)
    query = query.order_by(Document.uploaded_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(Document)
    if status_filter:
        count_query = count_query.where(Document.status == status_filter.value)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Convert to response model
    doc_list = [
        DocumentMetadata(
            document_id=doc.id,
            filename=doc.filename,
            file_path=doc.file_path,
            file_size=doc.file_size,
            file_type=doc.file_type,
            description=doc.description,
            tags=doc.tags or [],
            status=DocumentStatus(doc.status),
            total_chunks=doc.total_chunks,
            total_pages=doc.total_pages,
            metadata=doc.doc_metadata or {},
            uploaded_at=doc.uploaded_at,
            processed_at=doc.processed_at,
            error_message=doc.error_message,
        )
        for doc in documents
    ]
    
    return DocumentListResponse(
        documents=doc_list,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete(
    "/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete document",
    description="Delete a document and all its associated chunks",
)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> DocumentDeleteResponse:
    """Delete a document and its vector embeddings."""
    
    # Get document from database
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise DocumentNotFoundException(document_id)
    
    # Delete chunks from database
    chunks_result = await db.execute(
        select(Chunk).where(Chunk.document_id == document_id)
    )
    chunks = chunks_result.scalars().all()
    chunks_count = len(chunks)
    
    # Delete vectors from Qdrant
    try:
        qdrant_client = get_qdrant_client()
        vector_store = get_vector_store_service(qdrant_client)
        
        # Delete by document_id filter
        vector_store.delete_vectors(
            filter_conditions={"document_id": document_id}
        )
        
        logger.info(f"Deleted vectors for document {document_id} from Qdrant")
    except Exception as e:
        logger.warning(f"Failed to delete vectors from Qdrant: {e}")
    
    # Delete chunks from database
    for chunk in chunks:
        await db.delete(chunk)
    
    # Delete file from disk
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        logger.warning(f"Failed to delete file {document.file_path}: {e}")
    
    # Delete document from database
    await db.delete(document)
    await db.commit()
    
    logger.info(f"Document deleted: {document_id} ({chunks_count} chunks)")
    
    return DocumentDeleteResponse(
        document_id=document_id,
        message="Document deleted successfully",
        chunks_deleted=chunks_count,
    )


@router.post(
    "/index",
    response_model=IndexingResponse,
    summary="Reindex documents",
    description="Manually trigger reindexing of documents",
)
async def reindex_documents(
    request: IndexingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> IndexingResponse:
    """Manually trigger document reindexing."""
    
    # TODO: Step 3 implementation
    # Queue reindexing jobs
    
    return IndexingResponse(
        message="Reindexing queued",
        documents_queued=0,
        job_id=f"job_{uuid.uuid4().hex[:8]}",
    )
