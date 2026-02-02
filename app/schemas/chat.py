from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str = Field(..., description="User query", min_length=1, max_length=5000)
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    chat_history: Optional[List[ChatMessage]] = Field(default=[], description="Chat history")
    use_hybrid_search: Optional[bool] = Field(True, description="Use hybrid search")
    top_k: Optional[int] = Field(5, description="Number of documents to retrieve", ge=1, le=20)
    stream: Optional[bool] = Field(False, description="Stream response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the refund policy?",
                "conversation_id": "conv_123",
                "chat_history": [],
                "use_hybrid_search": True,
                "top_k": 5,
                "stream": False
            }
        }


class RetrievedDocument(BaseModel):
    """Retrieved document chunk."""
    chunk_id: str = Field(..., description="Chunk ID")
    content: str = Field(..., description="Chunk content")
    score: float = Field(..., description="Relevance score")
    metadata: dict = Field(default={}, description="Document metadata")
    source: Optional[str] = Field(None, description="Source document")
    page: Optional[int] = Field(None, description="Page number")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str = Field(..., description="Generated answer")
    conversation_id: str = Field(..., description="Conversation ID")
    retrieved_documents: List[RetrievedDocument] = Field(default=[], description="Retrieved documents")
    model: str = Field(..., description="Model used")
    tokens_used: Optional[int] = Field(None, description="Tokens used")
    latency_ms: float = Field(..., description="Response latency in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The refund policy allows returns within 30 days of purchase.",
                "conversation_id": "conv_123",
                "retrieved_documents": [
                    {
                        "chunk_id": "doc1_chunk0",
                        "content": "Our refund policy...",
                        "score": 0.95,
                        "metadata": {"source": "policy.pdf", "page": 1},
                        "source": "policy.pdf",
                        "page": 1
                    }
                ],
                "model": "llama3",
                "tokens_used": 250,
                "latency_ms": 1523.4
            }
        }


class ChatStreamChunk(BaseModel):
    """Streaming response chunk."""
    chunk: str = Field(..., description="Text chunk")
    conversation_id: str = Field(..., description="Conversation ID")
    done: bool = Field(False, description="Stream complete")
