import logging
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentChunker:
    """
    Service for chunking documents into smaller pieces for embedding.
    
    Uses RecursiveCharacterTextSplitter for semantic chunking that:
    - Respects natural text boundaries (paragraphs, sentences, words)
    - Maintains context with overlapping chunks
    - Handles different text structures intelligently
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        """
        Initialize document chunker.
        
        Args:
            chunk_size: Maximum size of each chunk (default from settings)
            chunk_overlap: Overlap between chunks to preserve context (default from settings)
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # Initialize splitter with hierarchical separators
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # Paragraph breaks (highest priority)
                "\n",    # Line breaks
                ". ",    # Sentence endings
                "? ",    # Questions
                "! ",    # Exclamations
                "; ",    # Semicolons
                ", ",    # Commas
                " ",     # Words
                "",      # Characters (last resort)
            ],
            keep_separator=True,
        )
        
        logger.info(
            f"Chunker initialized: size={self.chunk_size}, "
            f"overlap={self.chunk_overlap}"
        )
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces with metadata.
        
        Args:
            text: Text content to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or not text.strip():
            logger.warning("Received empty text for chunking")
            return []
        
        try:
            # Split text into chunks
            chunks = self.splitter.split_text(text)
            
            logger.info(
                f"Chunked {len(text)} characters into {len(chunks)} chunks "
                f"(avg {len(text) // len(chunks) if chunks else 0} chars/chunk)"
            )
            
            # Create chunk objects with metadata
            chunk_objects = []
            for i, chunk_text in enumerate(chunks):
                chunk_obj = {
                    "content": chunk_text,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk_text),
                    "metadata": metadata or {},
                }
                chunk_objects.append(chunk_obj)
            
            return chunk_objects
            
        except Exception as e:
            logger.error(f"Chunking failed: {str(e)}")
            raise
    
    def chunk_document_with_pages(
        self,
        page_texts: List[str],
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk a multi-page document while preserving page numbers.
        
        This is useful for PDFs where we want to track which page each chunk came from.
        
        Args:
            page_texts: List of text content per page
            metadata: Base metadata to attach to all chunks
            
        Returns:
            List of chunk dictionaries with page-specific metadata
        """
        all_chunks = []
        
        for page_num, page_text in enumerate(page_texts, start=1):
            if not page_text.strip():
                continue
            
            # Create page-specific metadata
            page_metadata = {
                **(metadata or {}),
                "page": page_num,
                "total_pages": len(page_texts),
            }
            
            # Chunk this page
            page_chunks = self.chunk_text(page_text, page_metadata)
            
            # Update global chunk index
            for chunk in page_chunks:
                chunk["global_chunk_index"] = len(all_chunks)
                all_chunks.append(chunk)
        
        # Update total chunks count
        for chunk in all_chunks:
            chunk["total_chunks"] = len(all_chunks)
        
        logger.info(
            f"Chunked {len(page_texts)} pages into {len(all_chunks)} total chunks"
        )
        
        return all_chunks
    
    def chunk_long_document(
        self,
        text: str,
        metadata: Dict[str, Any] = None,
        max_chunks: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Chunk a very long document with safety limits.
        
        For extremely long documents, we may want to limit the number of chunks
        to avoid memory issues or excessive storage.
        
        Args:
            text: Text content to chunk
            metadata: Optional metadata
            max_chunks: Maximum number of chunks to generate
            
        Returns:
            List of chunk dictionaries
        """
        chunks = self.chunk_text(text, metadata)
        
        if len(chunks) > max_chunks:
            logger.warning(
                f"Document generated {len(chunks)} chunks, "
                f"limiting to {max_chunks}"
            )
            chunks = chunks[:max_chunks]
        
        return chunks
    
    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics about the chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_characters": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
            }
        
        sizes = [chunk["chunk_size"] for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_characters": sum(sizes),
            "avg_chunk_size": sum(sizes) // len(sizes),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes),
        }


# Singleton instance
_chunker_service = None


def get_chunker_service() -> DocumentChunker:
    """Get or create document chunker singleton."""
    global _chunker_service
    if _chunker_service is None:
        _chunker_service = DocumentChunker()
    return _chunker_service
