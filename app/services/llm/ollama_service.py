"""
Ollama LLM service for response generation.
"""
import logging
import requests
from typing import List, Dict, Any, Optional
import time

from app.core.config import settings
from app.core.exceptions import LLMException

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Service for interacting with Ollama LLM API.
    
    Ollama provides local LLM inference for models like:
    - llama3 (Meta's Llama 3)
    - mistral (Mistral 7B)
    - codellama (Code Llama)
    - mixtral (Mixtral 8x7B)
    """
    
    def __init__(self):
        """Initialize Ollama service."""
        self.base_url = settings.OLLAMA_BASE_URL
        self.timeout = settings.OLLAMA_TIMEOUT
        logger.info(f"Ollama service initialized (base_url={self.base_url})")
    
    def verify_connection(self) -> bool:
        """
        Verify connection to Ollama server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            logger.info("Ollama connection verified")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models in Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            
            logger.info(f"Available Ollama models: {models}")
            return models
            
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str:
        """
        Generate response using Ollama LLM.
        
        Args:
            query: User query
            context: Context from retrieved documents
            conversation_history: Previous messages (list of {"role": "user/assistant", "content": "..."})
            model: Model name (default from settings)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Stream response (not implemented yet)
            
        Returns:
            Generated response text
            
        Raises:
            LLMException: If generation fails
        """
        model = model or settings.OLLAMA_LLM_MODEL
        conversation_history = conversation_history or []
        
        try:
            # Build messages for chat API
            messages = []
            
            # Add system message with context
            messages.append({
                "role": "system",
                "content": context
            })
            
            # Add conversation history
            for msg in conversation_history[-5:]:  # Last 5 messages only
                messages.append(msg)
            
            # Add current query
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Call Ollama chat API
            logger.info(f"Generating response with {model} (temperature={temperature})")
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract generated text
            if "message" in data:
                generated_text = data["message"]["content"]
            else:
                raise LLMException("Unexpected Ollama response format")
            
            latency = time.time() - start_time
            logger.info(
                f"Response generated in {latency:.2f}s "
                f"(model={model}, tokens={data.get('eval_count', 'N/A')})"
            )
            
            return generated_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            raise LLMException(f"Failed to generate response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {e}", exc_info=True)
            raise LLMException(f"LLM generation error: {str(e)}")
    
    def generate_streaming_response(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Generate streaming response using Ollama LLM.
        
        Args:
            query: User query
            context: Context from retrieved documents
            conversation_history: Previous messages
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Yields:
            Response chunks as they're generated
            
        Raises:
            LLMException: If generation fails
        """
        model = model or settings.OLLAMA_LLM_MODEL
        conversation_history = conversation_history or []
        
        try:
            # Build messages
            messages = []
            messages.append({"role": "system", "content": context})
            
            for msg in conversation_history[-5:]:
                messages.append(msg)
            
            messages.append({"role": "user", "content": query})
            
            # Call Ollama with streaming
            logger.info(f"Generating streaming response with {model}")
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                },
                stream=True,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Stream response chunks
            for line in response.iter_lines():
                if line:
                    try:
                        import json
                        chunk = json.loads(line)
                        
                        if "message" in chunk:
                            content = chunk["message"].get("content", "")
                            if content:
                                yield content
                        
                        # Check if done
                        if chunk.get("done", False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama streaming request failed: {e}")
            raise LLMException(f"Failed to generate streaming response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in streaming generation: {e}", exc_info=True)
            raise LLMException(f"LLM streaming error: {str(e)}")


# Singleton instance
_ollama_service = None


def get_ollama_service() -> OllamaService:
    """Get or create Ollama service singleton."""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
