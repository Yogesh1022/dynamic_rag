from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import QdrantClient
import redis.asyncio as aioredis
import time
import uuid
import logging
import json

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    RetrievedDocument,
)
from app.api.deps import get_db, get_qdrant_client, get_redis_client
from app.core.security import verify_api_key
from app.core.config import settings
from app.core.exceptions import LLMException, VectorStoreException
from app.services.retrieval.hybrid_retrieval import get_hybrid_retrieval_service
from app.services.llm.ollama_service import get_ollama_service
from app.services.cache import get_cache
from app.utils.json_logger import performance_logger
from app.models import Conversation, Message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with RAG system",
    description="Send a query and get an AI-generated response with relevant document context",
)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    qdrant: QdrantClient = Depends(get_qdrant_client),
    redis: aioredis.Redis = Depends(get_redis_client),
    api_key: str = Depends(verify_api_key),
) -> ChatResponse:
    """
    RAG Chat Endpoint
    
    This endpoint:
    1. Generates embeddings for the user query
    2. Retrieves relevant document chunks using hybrid search (vector + BM25)
    3. Re-ranks results for relevance
    4. Assembles context and generates response using Ollama LLM
    5. Saves conversation history
    """
    start_time = time.time()
    
    # Generate conversation ID
    conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:8]}"
    
    try:
        # Initialize services
        retrieval_service = get_hybrid_retrieval_service()
        ollama_service = get_ollama_service()
        vector_store = qdrant
        cache = await get_cache()
        
        # Check cache for query results
        cache_key = f"{request.query}|k={request.top_k or settings.RERANK_TOP_K}|hybrid={request.use_hybrid if request.use_hybrid is not None else settings.USE_HYBRID_SEARCH}"
        cached_result = await cache.get_query_result(
            query=request.query,
            top_k=request.top_k or settings.RERANK_TOP_K,
            use_hybrid=request.use_hybrid if request.use_hybrid is not None else settings.USE_HYBRID_SEARCH
        )
        
        if cached_result and not request.conversation_id:
            logger.info(f"✅ Cache HIT for query: {request.query[:50]}...")
            performance_logger.log_operation(
                operation="cache_hit",
                duration_ms=(time.time() - start_time) * 1000,
                success=True,
                metadata={"query": request.query[:50]}
            )
            return ChatResponse(**cached_result)
        
        # 1. Load conversation history
        conversation_history = []
        conversation = None
        
        if request.conversation_id:
            # Try to get from cache first
            cached_conv = await cache.get_conversation(request.conversation_id)
            if cached_conv:
                conversation_history = cached_conv.get("history", [])
                logger.info(f"✅ Loaded conversation from cache: {request.conversation_id}")
            else:
                conversation = await db.get(Conversation, request.conversation_id)
                if conversation:
                    # Load previous messages
                    for msg in conversation.messages:
                        conversation_history.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                    # Cache the conversation
                    await cache.set_conversation(
                        request.conversation_id,
                        {"history": conversation_history}
                    )
        
        # 2. Retrieve relevant documents using hybrid search
        logger.info(f"Processing query: {request.query[:50]}...")
        retrieval_start = time.time()
        
        retrieved_docs = await retrieval_service.retrieve(
            query=request.query,
            db=db,
            vector_store_service=vector_store,
            top_k=request.top_k or settings.RERANK_TOP_K,
            use_hybrid=request.use_hybrid if request.use_hybrid is not None else settings.USE_HYBRID_SEARCH,
            filter_conditions=None,
        )
        
        retrieval_duration = (time.time() - retrieval_start) * 1000
        performance_logger.log_operation(
            operation="retrieval",
            duration_ms=retrieval_duration,
            success=True,
            metadata={
                "query": request.query[:50],
                "docs_retrieved": len(retrieved_docs),
                "top_k": request.top_k or settings.RERANK_TOP_K
            }
        )
        
        logger.info(f"Retrieved {len(retrieved_docs)} relevant documents in {retrieval_duration:.2f}ms")
        
        # 3. Build context from retrieved chunks
        context_parts = []
        sources = []
        
        for i, doc in enumerate(retrieved_docs):
            context_parts.append(
                f"[{i+1}] {doc['content']}\n"
                f"(Source: Document {doc['metadata'].get('document_id', 'unknown')}, "
                f"Page {doc['metadata'].get('page', 'N/A')})"
            )
            
            sources.append(
                RetrievedDocument(
                    chunk_id=doc["chunk_id"],
                    content=doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                    score=doc["score"],
                    metadata={
                        "document_id": doc["metadata"].get("document_id"),
                        "page": doc["metadata"].get("page"),
                        "chunk_index": doc["metadata"].get("chunk_index"),
                    },
                    source=doc["metadata"].get("document_id", "unknown"),
                    page=doc["metadata"].get("page", 0),
                )
            )
        
        context = "\n\n".join(context_parts)
        
        # 4. Build system prompt
        system_prompt = f"""You are a helpful AI assistant that answers questions based on the provided context.

Context from documents:
{context}

Instructions:
- Answer the question based ONLY on the information in the context above
- If the context doesn't contain enough information to answer, say so
- Cite your sources by referring to the numbered references [1], [2], etc.
- Be concise but thorough
- If you're uncertain, express your uncertainty"""
        
        # 5. Generate response using LLM
        logger.info(f"Generating response with model: {request.model or settings.OLLAMA_LLM_MODEL}")
        llm_start = time.time()
        
        response_text = ollama_service.generate_response(
            query=request.query,
            context=system_prompt,
            conversation_history=conversation_history,
            model=request.model or settings.OLLAMA_LLM_MODEL,
            temperature=request.temperature or 0.7,
            max_tokens=4096,
        )
        
        llm_duration = (time.time() - llm_start) * 1000
        performance_logger.log_llm_call(
            model=request.model or settings.OLLAMA_LLM_MODEL,
            prompt_tokens=len(system_prompt.split()),  # Approximate
            completion_tokens=len(response_text.split()),  # Approximate
            duration_ms=llm_duration
        )
        
        # 6. Save conversation to database
        db_start = time.time()
        if not conversation:
            # Create new conversation
            conversation = Conversation(
                title=request.query[:100],  # Use first 100 chars as title
                user_id=None,  # TODO: Add user authentication
            )
            db.add(conversation)
            await db.flush()  # Get conversation ID
        
        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.query,
        )
        db.add(user_message)
        
        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
        )
        db.add(assistant_message)
        
        await db.commit()
        
        db_duration = (time.time() - db_start) * 1000
        performance_logger.log_db_query(
            query_type="save_conversation",
            duration_ms=db_duration,
            row_count=2
        )
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # 7. Build response
        response_data = ChatResponse(
            answer=response_text,
            conversation_id=str(conversation.id),
            retrieved_documents=sources,
            model=request.model or settings.OLLAMA_LLM_MODEL,
            tokens_used=None,  # TODO: Get token count from Ollama response
            latency_ms=latency_ms,
        )
        
        # 8. Cache the result (if not a conversation)
        if not request.conversation_id:
            await cache.set_query_result(
                query=request.query,
                top_k=request.top_k or settings.RERANK_TOP_K,
                use_hybrid=request.use_hybrid if request.use_hybrid is not None else settings.USE_HYBRID_SEARCH,
                results=response_data.dict()
            )
            logger.info(f"✅ Cached query result for: {request.query[:50]}...")
        
        # Log overall performance
        performance_logger.log_operation(
            operation="chat_complete",
            duration_ms=latency_ms,
            success=True,
            metadata={
                "query": request.query[:50],
                "sources": len(sources),
                "model": request.model or settings.OLLAMA_LLM_MODEL
            }
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        performance_logger.log_operation(
            operation="chat_error",
            duration_ms=(time.time() - start_time) * 1000,
            success=False,
            metadata={"error": str(e)}
        )
        raise LLMException(f"Failed to process chat request: {str(e)}")


@router.get(
    "/health",
    summary="Health check",
    description="Check if the chat service is healthy",
)
async def health_check(
    qdrant: QdrantClient = Depends(get_qdrant_client),
    redis: aioredis.Redis = Depends(get_redis_client),
) -> dict:
    """Health check endpoint."""
    try:
        # Check Qdrant
        qdrant.get_collections()
        
        # Check Redis
        await redis.ping()
        
        return {
            "status": "healthy",
            "services": {
                "qdrant": "connected",
                "redis": "connected",
                "ollama": "not_checked",  # Will check in Step 6
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )
