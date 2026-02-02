from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadRequest(BaseModel):
    """Document upload metadata."""
    filename: str = Field(..., description="Original filename")
    description: Optional[str] = Field(None, description="Document description")
    tags: Optional[List[str]] = Field(default=[], description="Document tags")
    metadata: Optional[dict] = Field(default={}, description="Additional metadata")


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    document_id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    status: DocumentStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_abc123",
                "filename": "policy.pdf",
                "file_size": 1024000,
                "status": "processing",
                "message": "Document uploaded successfully, processing in background",
                "uploaded_at": "2026-02-01T10:30:00Z"
            }
        }


class DocumentMetadata(BaseModel):
    """Document metadata stored in database."""
    document_id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Storage path")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File type/extension")
    description: Optional[str] = Field(None, description="Document description")
    tags: List[str] = Field(default=[], description="Document tags")
    status: DocumentStatus = Field(..., description="Processing status")
    total_chunks: Optional[int] = Field(None, description="Total chunks created")
    total_pages: Optional[int] = Field(None, description="Total pages")
    metadata: dict = Field(default={}, description="Additional metadata")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(None, description="Processing completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class DocumentListResponse(BaseModel):
    """Response for document list endpoint."""
    documents: List[DocumentMetadata] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


class DocumentDeleteResponse(BaseModel):
    """Response after document deletion."""
    document_id: str = Field(..., description="Deleted document ID")
    message: str = Field(..., description="Deletion message")
    chunks_deleted: int = Field(..., description="Number of chunks deleted")


class IndexingRequest(BaseModel):
    """Request to reindex documents."""
    document_ids: Optional[List[str]] = Field(None, description="Specific document IDs to reindex")
    force: Optional[bool] = Field(False, description="Force reindexing even if already indexed")


class IndexingResponse(BaseModel):
    """Response after indexing operation."""
    message: str = Field(..., description="Indexing status message")
    documents_queued: int = Field(..., description="Number of documents queued for indexing")
    job_id: Optional[str] = Field(None, description="Background job ID")
