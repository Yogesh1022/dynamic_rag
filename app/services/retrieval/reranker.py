import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RankedResult:
    """Result with re-ranking score."""
    id: str
    content: str
    original_score: float
    rerank_score: float
    final_score: float
    metadata: Dict[str, Any]


class RerankerService:
    """
    Service for re-ranking retrieved documents.
    
    Uses a simple but effective scoring approach:
    - Combines vector similarity with text-based features
    - Considers query-document overlap
    - Applies decay for longer documents
    """
    
    def __init__(self):
        """Initialize reranker service."""
        logger.info("Reranker service initialized")
    
    def calculate_query_overlap(self, query: str, document: str) -> float:
        """
        Calculate how much of the query terms appear in the document.
        
        Args:
            query: User query
            document: Document text
            
        Returns:
            Overlap score (0.0 to 1.0)
        """
        query_terms = set(query.lower().split())
        doc_terms = set(document.lower().split())
        
        if not query_terms:
            return 0.0
        
        # Calculate term overlap
        overlap = len(query_terms.intersection(doc_terms))
        overlap_ratio = overlap / len(query_terms)
        
        return overlap_ratio
    
    def calculate_length_penalty(self, document: str, optimal_length: int = 500) -> float:
        """
        Apply penalty for documents that are too short or too long.
        
        Args:
            document: Document text
            optimal_length: Optimal document length
            
        Returns:
            Length score (0.0 to 1.0)
        """
        doc_length = len(document.split())
        
        # Very short documents get penalized
        if doc_length < 50:
            return 0.5
        
        # Documents near optimal length get higher scores
        length_ratio = min(doc_length, optimal_length) / optimal_length
        
        # Penalty for very long documents
        if doc_length > optimal_length * 2:
            length_ratio *= 0.8
        
        return min(length_ratio, 1.0)
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5,
        vector_weight: float = 0.7,
        overlap_weight: float = 0.2,
        length_weight: float = 0.1,
    ) -> List[RankedResult]:
        """
        Re-rank search results using multiple signals.
        
        Args:
            query: User query
            results: Initial search results from vector search
            top_k: Number of top results to return
            vector_weight: Weight for vector similarity score
            overlap_weight: Weight for query overlap score
            length_weight: Weight for length score
            
        Returns:
            Re-ranked results
        """
        if not results:
            return []
        
        logger.info(f"Re-ranking {len(results)} results for query: {query[:50]}...")
        
        ranked_results = []
        
        for result in results:
            content = result.get("payload", {}).get("content", "")
            original_score = result.get("score", 0.0)
            
            # Calculate additional scores
            overlap_score = self.calculate_query_overlap(query, content)
            length_score = self.calculate_length_penalty(content)
            
            # Weighted combination
            final_score = (
                vector_weight * original_score +
                overlap_weight * overlap_score +
                length_weight * length_score
            )
            
            ranked_result = RankedResult(
                id=result.get("id", ""),
                content=content,
                original_score=original_score,
                rerank_score=overlap_score,
                final_score=final_score,
                metadata=result.get("payload", {}),
            )
            
            ranked_results.append(ranked_result)
        
        # Sort by final score (descending)
        ranked_results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Return top K
        top_results = ranked_results[:top_k]
        
        logger.info(
            f"Re-ranking complete. Top score: {top_results[0].final_score:.4f} "
            f"(vector: {top_results[0].original_score:.4f}, "
            f"overlap: {top_results[0].rerank_score:.4f})"
        )
        
        return top_results
    
    def rerank_simple(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Simple re-ranking that just returns top K by original score.
        
        Args:
            query: User query (unused in simple mode)
            results: Search results
            top_k: Number of results to return
            
        Returns:
            Top K results
        """
        # Sort by score (descending)
        sorted_results = sorted(
            results,
            key=lambda x: x.get("score", 0.0),
            reverse=True
        )
        
        return sorted_results[:top_k]


# Singleton instance
_reranker_service = None


def get_reranker_service() -> RerankerService:
    """Get or create reranker service singleton."""
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService()
    return _reranker_service
