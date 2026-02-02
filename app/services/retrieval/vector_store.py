import logging
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
)
import uuid

from app.core.config import settings
from app.core.exceptions import VectorStoreException

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vectors in Qdrant."""
    
    def __init__(
        self,
        client: QdrantClient = None,
        collection_name: str = None,
    ):
        """
        Initialize vector store service.
        
        Args:
            client: Qdrant client instance (if None, will be injected via dependency)
            collection_name: Collection name (default from settings)
        """
        self.client = client
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        
        logger.info(f"Vector store service initialized: collection={self.collection_name}")
    
    def set_client(self, client: QdrantClient):
        """Set Qdrant client (for dependency injection)."""
        self.client = client
    
    def ensure_collection_exists(self, dimension: int = None):
        """
        Ensure collection exists, create if not.
        
        Args:
            dimension: Vector dimension (default from settings)
        """
        if not self.client:
            raise VectorStoreException("Qdrant client not initialized")
        
        dimension = dimension or settings.EMBEDDING_DIMENSION
        
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=dimension,
                        distance=Distance.COSINE,
                    ),
                )
                
                logger.info(f"Collection created: {self.collection_name}")
            else:
                logger.debug(f"Collection already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise VectorStoreException(f"Collection operation failed: {str(e)}")
    
    def upsert_vectors(
        self,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Insert or update vectors in the collection.
        
        Args:
            vectors: List of embedding vectors
            payloads: List of metadata dictionaries (one per vector)
            ids: Optional list of vector IDs (will generate UUIDs if not provided)
            
        Returns:
            List of vector IDs
            
        Raises:
            VectorStoreException: If upsert fails
        """
        if not self.client:
            raise VectorStoreException("Qdrant client not initialized")
        
        if len(vectors) != len(payloads):
            raise VectorStoreException("Vectors and payloads must have same length")
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in vectors]
        
        if len(ids) != len(vectors):
            raise VectorStoreException("IDs, vectors, and payloads must have same length")
        
        try:
            logger.info(f"Upserting {len(vectors)} vectors to {self.collection_name}")
            
            # Create points
            points = [
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
                for point_id, vector, payload in zip(ids, vectors, payloads)
            ]
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            
            logger.info(f"Successfully upserted {len(points)} vectors")
            
            return ids
            
        except Exception as e:
            logger.error(f"Vector upsert failed: {e}")
            raise VectorStoreException(
                f"Failed to upsert vectors: {str(e)}",
                details={"count": len(vectors)}
            )
    
    def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_conditions: Optional metadata filters (e.g., {"document_id": "doc_123"})
            score_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of search results with scores and payloads
            
        Raises:
            VectorStoreException: If search fails
        """
        if not self.client:
            raise VectorStoreException("Qdrant client not initialized")
        
        try:
            logger.debug(f"Searching vectors: top_k={top_k}, filters={filter_conditions}")
            
            # Build filter if provided
            query_filter = None
            if filter_conditions:
                field_conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                    for key, value in filter_conditions.items()
                ]
                query_filter = Filter(must=field_conditions)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False,
            )
            
            # Format results
            formatted_results = [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]
            
            logger.info(f"Found {len(formatted_results)} results")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise VectorStoreException(
                f"Failed to search vectors: {str(e)}",
                details={"top_k": top_k}
            )
    
    def delete_vectors(
        self,
        vector_ids: Optional[List[str]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Delete vectors by IDs or filter conditions.
        
        Args:
            vector_ids: List of vector IDs to delete
            filter_conditions: Delete by metadata filter (e.g., {"document_id": "doc_123"})
            
        Returns:
            Number of vectors deleted
            
        Raises:
            VectorStoreException: If deletion fails
        """
        if not self.client:
            raise VectorStoreException("Qdrant client not initialized")
        
        if not vector_ids and not filter_conditions:
            raise VectorStoreException("Must provide either vector_ids or filter_conditions")
        
        try:
            if vector_ids:
                logger.info(f"Deleting {len(vector_ids)} vectors by ID")
                
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=vector_ids,
                )
                
                return len(vector_ids)
            
            elif filter_conditions:
                logger.info(f"Deleting vectors by filter: {filter_conditions}")
                
                # Build filter
                field_conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                    for key, value in filter_conditions.items()
                ]
                query_filter = Filter(must=field_conditions)
                
                # Delete by filter
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=query_filter,
                )
                
                # Note: Qdrant doesn't return count for filter-based deletion
                logger.info("Vectors deleted by filter")
                return 0  # Unknown count
            
        except Exception as e:
            logger.error(f"Vector deletion failed: {e}")
            raise VectorStoreException(
                f"Failed to delete vectors: {str(e)}"
            )
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.
        
        Returns:
            Collection info including vector count, size, etc.
        """
        if not self.client:
            raise VectorStoreException("Qdrant client not initialized")
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "name": collection_info.config.params.vectors.size if hasattr(collection_info.config.params, 'vectors') else None,
                "vectors_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status,
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise VectorStoreException(f"Failed to get collection info: {str(e)}")


# Singleton instance
_vector_store_service = None


def get_vector_store_service(client: QdrantClient = None) -> VectorStoreService:
    """Get or create vector store service singleton."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService(client=client)
    elif client and not _vector_store_service.client:
        _vector_store_service.set_client(client)
    return _vector_store_service
