import faiss
import numpy as np
from typing import List, Tuple

class Retriever:
    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatIP(embedding_dim)  # Cosine similarity with normalized vectors
        self.text_chunks = []

    def add_documents(self, chunks: List[str], embeddings: List[np.ndarray]):
        try:
            # Normalize embeddings
            normalized_emb = [emb / np.linalg.norm(emb) for emb in embeddings if np.linalg.norm(emb) != 0]
            if not normalized_emb:
                raise ValueError("No valid embeddings provided.")
            emb_matrix = np.array(normalized_emb).astype('float32')
            self.index.add(emb_matrix)
            self.text_chunks.extend(chunks)
        except Exception as e:
            raise Exception(f"Failed to add documents to retriever: {str(e)}")

    def retrieve(self, query_embedding: np.ndarray, top_k: int = 3) -> List[Tuple[str, float]]:
        try:
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            D, I = self.index.search(np.array([query_norm]).astype('float32'), top_k)
            results = []
            for idx, score in zip(I[0], D[0]):
                if idx == -1 or idx >= len(self.text_chunks):
                    continue
                results.append((self.text_chunks[idx], float(score)))
            return results
        except Exception as e:
            raise Exception(f"Retrieval failed: {str(e)}")