import logging
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Chunk
from app.services.retrieval.embedding import get_embedding_service
from app.services.retrieval.vector_store import get_vector_store_service
from app.services.retrieval.reranker import get_reranker_service, RankedResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class HybridRetrievalService:
    """
    Hybrid retrieval combining vector search and BM25 keyword search.
    
    Strategy:
    1. Vector search: Find semantically similar chunks
    2. BM25 search: Find keyword matches
    3. Combine and re-rank results
    """
    
    def __init__(self):
        """Initialize hybrid retrieval service."""
        self.embedding_service = get_embedding_service()
        self.reranker_service = get_reranker_service()
        logger.info("Hybrid retrieval service initialized")
    
    async def retrieve(
        self,
        query: str,
        db: AsyncSession,
        vector_store_service,
        top_k: int = None,
        use_hybrid: bool = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using hybrid search.
        
        Args:
            query: User query
            db: Database session
            vector_store_service: Vector store service instance
            top_k: Number of results to return (default from settings)
            use_hybrid: Use hybrid search (default from settings)
            filter_conditions: Optional filters (e.g., {"document_id": "doc_123"})
            
        Returns:
            List of retrieved documents with metadata
        """
        top_k = top_k or settings.RERANK_TOP_K
        use_hybrid = use_hybrid if use_hybrid is not None else settings.USE_HYBRID_SEARCH
        
        logger.info(
            f"Retrieving documents for query: '{query[:50]}...' "
            f"(top_k={top_k}, hybrid={use_hybrid})"
        )
        
        if use_hybrid:
            return await self._hybrid_retrieve(
                query, db, vector_store_service, top_k, filter_conditions
            )
        else:
            return await self._vector_retrieve(
                query, vector_store_service, top_k, filter_conditions
            )
    
    async def _vector_retrieve(
        self,
        query: str,
        vector_store_service,
        top_k: int,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve using vector search only.
        
        Args:
            query: User query
            vector_store_service: Vector store service
            top_k: Number of results
            filter_conditions: Optional filters
            
        Returns:
            Retrieved documents
        """
        logger.info("Performing vector search...")
        
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # Search in vector store
        results = vector_store_service.search_vectors(
            query_vector=query_embedding,
            top_k=settings.RETRIEVAL_TOP_K,  # Get more for re-ranking
            filter_conditions=filter_conditions,
            score_threshold=0.0,
        )
        
        logger.info(f"Vector search returned {len(results)} results")
        
        # Re-rank results
        ranked_results = self.reranker_service.rerank(
            query=query,
            results=results,
            top_k=top_k,
        )
        
        # Convert to output format
        return self._format_results(ranked_results)
    
    async def _hybrid_retrieve(
        self,
        query: str,
        db: AsyncSession,
        vector_store_service,
        top_k: int,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve using hybrid search (vector + BM25).
        
        Args:
            query: User query
            db: Database session
            vector_store_service: Vector store service
            top_k: Number of results
            filter_conditions: Optional filters
            
        Returns:
            Retrieved documents
        """
        logger.info("Performing hybrid search (vector + BM25)...")
        
        # 1. Vector search
        query_embedding = self.embedding_service.generate_embedding(query)
        
        vector_results = vector_store_service.search_vectors(
            query_vector=query_embedding,
            top_k=settings.RETRIEVAL_TOP_K,
            filter_conditions=filter_conditions,
            score_threshold=0.0,
        )
        
        logger.info(f"Vector search returned {len(vector_results)} results")
        
        # 2. BM25 keyword search
        bm25_results = await self._bm25_search(
            query, db, top_k=settings.RETRIEVAL_TOP_K, filter_conditions=filter_conditions
        )
        
        logger.info(f"BM25 search returned {len(bm25_results)} results")
        
        # 3. Combine results
        combined_results = self._combine_results(
            vector_results,
            bm25_results,
            vector_weight=settings.VECTOR_WEIGHT,
            bm25_weight=settings.BM25_WEIGHT,
        )
        
        logger.info(f"Combined {len(combined_results)} unique results")
        
        # 4. Re-rank
        ranked_results = self.reranker_service.rerank(
            query=query,
            results=combined_results,
            top_k=top_k,
        )
        
        return self._format_results(ranked_results)
    
    async def _bm25_search(
        self,
        query: str,
        db: AsyncSession,
        top_k: int = 20,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search on chunks.
        
        Args:
            query: User query
            db: Database session
            top_k: Number of results
            filter_conditions: Optional filters
            
        Returns:
            BM25 search results
        """
        try:
            # Get all chunks from database
            query_stmt = select(Chunk)
            
            # Apply filters if provided
            if filter_conditions:
                for key, value in filter_conditions.items():
                    if key == "document_id":
                        query_stmt = query_stmt.where(Chunk.document_id == value)
            
            result = await db.execute(query_stmt)
            chunks = result.scalars().all()
            
            if not chunks:
                logger.warning("No chunks found for BM25 search")
                return []
            
            # Prepare corpus for BM25
            corpus = [chunk.content for chunk in chunks]
            tokenized_corpus = [doc.lower().split() for doc in corpus]
            
            # Initialize BM25
            bm25 = BM25Okapi(tokenized_corpus)
            
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            scores = bm25.get_scores(tokenized_query)
            
            # Create results with scores
            results = []
            for i, (chunk, score) in enumerate(zip(chunks, scores)):
                if score > 0:  # Only include non-zero scores
                    results.append({
                        "id": chunk.id,
                        "score": float(score),
                        "payload": {
                            "chunk_id": chunk.id,
                            "content": chunk.content,
                            "document_id": chunk.document_id,
                            "chunk_index": chunk.chunk_index,
                            "page": chunk.page_number,
                        }
                    })
            
            # Sort by score and return top K
            results.sort(key=lambda x: x["score"], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Combine vector and BM25 results using weighted scores.
        
        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            vector_weight: Weight for vector scores
            bm25_weight: Weight for BM25 scores
            
        Returns:
            Combined results
        """
        # Normalize scores to 0-1 range
        def normalize_scores(results):
            if not results:
                return results
            
            max_score = max(r["score"] for r in results)
            if max_score == 0:
                return results
            
            for r in results:
                r["normalized_score"] = r["score"] / max_score
            
            return results
        
        vector_results = normalize_scores(vector_results)
        bm25_results = normalize_scores(bm25_results)
        
        # Combine by ID
        combined = {}
        
        for result in vector_results:
            result_id = result["id"]
            combined[result_id] = {
                "id": result_id,
                "score": vector_weight * result.get("normalized_score", result["score"]),
                "payload": result["payload"],
            }
        
        for result in bm25_results:
            result_id = result["id"]
            if result_id in combined:
                # Add BM25 score to existing vector score
                combined[result_id]["score"] += bm25_weight * result.get("normalized_score", result["score"])
            else:
                # New result from BM25 only
                combined[result_id] = {
                    "id": result_id,
                    "score": bm25_weight * result.get("normalized_score", result["score"]),
                    "payload": result["payload"],
                }
        
        return list(combined.values())
    
    def _format_results(self, ranked_results: List[RankedResult]) -> List[Dict[str, Any]]:
        """
        Format ranked results for output.
        
        Args:
            ranked_results: Re-ranked results
            
        Returns:
            Formatted results
        """
        return [
            {
                "chunk_id": result.id,
                "content": result.content,
                "score": result.final_score,
                "original_score": result.original_score,
                "metadata": result.metadata,
            }
            for result in ranked_results
        ]


# Singleton instance
_hybrid_retrieval_service = None


def get_hybrid_retrieval_service() -> HybridRetrievalService:
    """Get or create hybrid retrieval service singleton."""
    global _hybrid_retrieval_service
    if _hybrid_retrieval_service is None:
        _hybrid_retrieval_service = HybridRetrievalService()
    return _hybrid_retrieval_service
