from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.sql import func
from datetime import datetime

from app.api.deps import Base


class Document(Base):
    """Document model for storing document metadata."""
    
    __tablename__ = "documents"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # File information
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    
    # Content information
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    
    # Processing information
    status = Column(String, nullable=False, default="uploaded")  # uploaded, processing, completed, failed
    total_chunks = Column(Integer, nullable=True)
    total_pages = Column(Integer, nullable=True)
    total_characters = Column(Integer, nullable=True)
    used_ocr = Column(Boolean, default=False)
    
    # Additional metadata
    doc_metadata = Column(JSON, default=dict)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class Chunk(Base):
    """Chunk model for storing document chunks."""
    
    __tablename__ = "chunks"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign key to document
    document_id = Column(String, nullable=False, index=True)
    
    # Chunk information
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    
    # Page information (for PDFs)
    page_number = Column(Integer, nullable=True)
    
    # Vector information
    vector_id = Column(String, nullable=True, index=True)  # ID in Qdrant
    embedding_model = Column(String, nullable=True)
    
    # Metadata
    doc_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class Conversation(Base):
    """Conversation model for storing chat history."""
    
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Conversation metadata
    title = Column(String, nullable=True)
    user_id = Column(String, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Statistics
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"


class Message(Base):
    """Message model for storing individual chat messages."""
    
    __tablename__ = "messages"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign key to conversation
    conversation_id = Column(String, nullable=False, index=True)
    
    # Message content
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Model information (for assistant messages)
    model = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Retrieved documents (for assistant messages)
    retrieved_docs = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Performance metrics
    latency_ms = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"
