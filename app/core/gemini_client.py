
import httpx
import logging
import os

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b-latest:generateContent"
        self.client = httpx.AsyncClient()

    async def generate_answer(self, context: str, question: str) -> str:
        """
        Generate an answer using Gemini API given a context and question.
        
        Args:
            context: The context text from retrieved documents.
            question: The user's question.
        
        Returns:
            Generated answer as a string.
        """
        try:
            prompt = f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            logger.debug("Sending request to Gemini API: %s", self.base_url)
            response = await self.client.post(
                self.base_url,
                params={"key": self.api_key},
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            return answer
        except httpx.HTTPStatusError as e:
            logger.error("Gemini API request failed: %s", str(e))
            raise Exception(f"Gemini API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error("Unexpected error in Gemini API call: %s", str(e))
            raise
        finally:
            await self.client.aclose()
