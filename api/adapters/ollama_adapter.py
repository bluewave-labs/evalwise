import httpx
import time
import asyncio
from typing import Dict, Any, Optional
from .base import BaseModelAdapter, ModelResponse
import logging

logger = logging.getLogger(__name__)

class OllamaAdapter(BaseModelAdapter):
    """Adapter for Ollama local LLM server"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or "http://localhost:11434"
        
        # Rate limiting for local server
        self._last_request_time = 0
        self._min_request_interval = 0.05  # 20 requests per second max
        
        # Common Ollama models (no pricing for local models)
        self.supported_models = [
            "llama2", "llama2:7b", "llama2:13b", "llama2:70b",
            "codellama", "codellama:7b", "codellama:13b", "codellama:34b",
            "mistral", "mistral:7b", "mixtral:8x7b",
            "neural-chat", "starling-lm", "openchat",
            "phi", "gemma:2b", "gemma:7b",
        ]
    
    def validate_api_key(self) -> bool:
        """Ollama doesn't require API keys for local deployment"""
        return True
    
    async def _rate_limit(self):
        """Simple rate limiting to avoid overwhelming local server"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    async def check_model_availability(self, model_name: str) -> bool:
        """Check if model is available/downloaded in Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    available_models = [model["name"] for model in data.get("models", [])]
                    return model_name in available_models or any(model_name in model for model in available_models)
                
        except Exception as e:
            logger.warning(f"Could not check Ollama model availability: {e}")
        
        return False
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull/download model if not available"""
        logger.info(f"Pulling Ollama model: {model_name}")
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for model download
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                )
                
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def generate(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> ModelResponse:
        """Generate response using Ollama API"""
        await self._rate_limit()
        start_time = time.time()
        
        # Check if model is available, try to pull if not
        if not await self.check_model_availability(model_name):
            logger.info(f"Model {model_name} not found locally, attempting to pull...")
            if not await self.pull_model(model_name):
                raise Exception(f"Model {model_name} is not available and could not be downloaded")
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs
            }
        }
        
        logger.info(f"Generating response with {model_name} (Ollama), temp={temperature}, max_tokens={max_tokens}")
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minute timeout for generation
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 404:
                    raise Exception(f"Ollama server not found at {self.base_url} - please ensure Ollama is running")
                elif response.status_code != 200:
                    error_text = response.text if response.content else "Unknown error"
                    raise Exception(f"Ollama API error (status {response.status_code}): {error_text}")
                
                data = response.json()
                content = data.get("response", "")
                
                if not content:
                    logger.warning("Empty response content from Ollama")
                    content = ""
                
                # Ollama provides some basic metrics
                eval_count = data.get("eval_count", 0)
                prompt_eval_count = data.get("prompt_eval_count", 0)
                
                # Estimate tokens (Ollama doesn't provide exact token counts)
                input_tokens = prompt_eval_count or self._estimate_tokens(prompt)
                output_tokens = eval_count or self._estimate_tokens(content)
                
                logger.info(f"Generated response: {len(content)} chars, ~{input_tokens} input tokens, ~{output_tokens} output tokens")
                
                return ModelResponse(
                    content=content,
                    latency_ms=self._calculate_latency(start_time),
                    token_input=input_tokens,
                    token_output=output_tokens,
                    cost_usd=0.0,  # Local models are free
                    raw_response=data
                )
                
        except httpx.TimeoutException:
            raise Exception("Request timeout - Ollama took too long to respond (check if model is large/slow)")
        except httpx.ConnectError:
            raise Exception("Could not connect to Ollama server - please ensure Ollama is running on localhost:11434")
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            raise Exception(f"Error calling Ollama API: {str(e)}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count for local models"""
        # Very rough estimate: 1 token per 4 characters on average
        return max(1, len(text) // 4)
    
    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Local models have no cost"""
        return 0.0
    
    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens - rough estimation for local models"""
        return self._estimate_tokens(text)
    
    async def get_available_models(self) -> list:
        """Get list of available models from Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
                
        except Exception as e:
            logger.warning(f"Could not get available models: {e}")
        
        return []