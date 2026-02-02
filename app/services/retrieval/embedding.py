import logging
from typing import List, Union
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import EmbeddingException

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Ollama."""
    
    def __init__(
        self,
        model_name: str = None,
        base_url: str = None,
    ):
        """
        Initialize embedding service.
        
        Args:
            model_name: Ollama embedding model name (default from settings)
            base_url: Ollama base URL (default from settings)
        """
        self.model_name = model_name or settings.OLLAMA_EMBEDDING_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        
        # Initialize Ollama client
        self.client = ollama.Client(host=self.base_url)
        
        logger.info(
            f"Embedding service initialized: model={self.model_name}, "
            f"url={self.base_url}"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            EmbeddingException: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingException("Cannot generate embedding for empty text")
        
        try:
            logger.debug(f"Generating embedding for text ({len(text)} chars)")
            
            # Call Ollama embedding API
            response = self.client.embeddings(
                model=self.model_name,
                prompt=text,
            )
            
            # Extract embedding vector
            embedding = response.get("embedding")
            
            if not embedding:
                raise EmbeddingException("No embedding returned from Ollama")
            
            logger.debug(f"Generated embedding: dimension={len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise EmbeddingException(
                f"Failed to generate embedding: {str(e)}",
                details={"model": self.model_name, "text_length": len(text)}
            )
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing (default from settings)
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingException: If embedding generation fails
        """
        if not texts:
            return []
        
        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        
        logger.info(
            f"Generating embeddings for {len(texts)} texts "
            f"(batch_size={batch_size})"
        )
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            logger.debug(f"Processing batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}")
            
            for text in batch:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model.
        
        Returns:
            Embedding dimension
        """
        try:
            # Generate a test embedding to get dimension
            test_embedding = self.generate_embedding("test")
            return len(test_embedding)
        except Exception as e:
            logger.warning(f"Could not determine embedding dimension: {e}")
            return settings.EMBEDDING_DIMENSION
    
    def verify_connection(self) -> bool:
        """
        Verify connection to Ollama server.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to generate a test embedding
            self.generate_embedding("test connection")
            logger.info("Ollama connection verified")
            return True
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
