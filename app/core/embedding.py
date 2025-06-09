from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> np.ndarray:
    try:
        embeddings = model.encode([text])
        return embeddings[0]
    except Exception as e:
        raise Exception(f"Embedding generation failed: {str(e)}")