import httpx
import tiktoken
import time
import asyncio
from typing import Dict, Any, Optional
from .base import BaseModelAdapter, ModelResponse
import logging

logger = logging.getLogger(__name__)

class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI and OpenAI-compatible APIs"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or "https://api.openai.com/v1"
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 10 requests per second max
        
        # Token pricing per 1K tokens (USD) - updated pricing
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
        }
    
    def validate_api_key(self) -> bool:
        """Validate that API key is present and properly formatted"""
        if not self.api_key:
            return False
        
        # OpenAI API keys start with 'sk-'
        if not self.api_key.startswith('sk-'):
            logger.warning("OpenAI API key should start with 'sk-'")
            return False
        
        return len(self.api_key) > 20  # Basic length check
    
    async def _rate_limit(self):
        """Simple rate limiting to avoid hitting API limits"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    async def generate(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> ModelResponse:
        """Generate response using OpenAI-compatible API"""
        if not self.validate_api_key():
            raise Exception("Invalid or missing OpenAI API key")
        
        await self._rate_limit()
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "EvalWise/1.0"
        }
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        logger.info(f"Generating response with {model_name}, temp={temperature}, max_tokens={max_tokens}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                
                # Handle specific HTTP errors
                if response.status_code == 401:
                    raise Exception("Invalid API key - please check your OpenAI API key")
                elif response.status_code == 429:
                    raise Exception("Rate limit exceeded - please try again later")
                elif response.status_code == 400:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get("message", "Bad request")
                    raise Exception(f"API request error: {error_msg}")
                
                response.raise_for_status()
                data = response.json()
                
                # Extract response content
                if not data.get("choices") or len(data["choices"]) == 0:
                    raise Exception("No response choices returned from API")
                
                content = data["choices"][0]["message"]["content"]
                if not content:
                    logger.warning("Empty response content from API")
                    content = ""
                
                # Extract token usage if available
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                
                # Calculate cost
                cost = None
                if input_tokens and output_tokens:
                    cost = self.estimate_cost(model_name, input_tokens, output_tokens)
                
                logger.info(f"Generated response: {len(content)} chars, {input_tokens} input tokens, {output_tokens} output tokens")
                
                return ModelResponse(
                    content=content,
                    latency_ms=self._calculate_latency(start_time),
                    token_input=input_tokens,
                    token_output=output_tokens,
                    cost_usd=cost,
                    raw_response=data
                )
                
        except httpx.TimeoutException:
            raise Exception("Request timeout - the API took too long to respond")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling OpenAI API: {str(e)}")
            raise Exception(f"HTTP error calling OpenAI API: {str(e)}")
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise Exception(f"Error calling OpenAI API: {str(e)}")
    
    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on token usage"""
        if model_name not in self.pricing:
            # Default to GPT-4 pricing for unknown models
            pricing = self.pricing["gpt-4"]
        else:
            pricing = self.pricing[model_name]
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens using tiktoken"""
        try:
            # Map model names to tiktoken encodings
            if "gpt-4" in model_name:
                encoding_name = "cl100k_base"
            elif "gpt-3.5" in model_name:
                encoding_name = "cl100k_base"
            else:
                encoding_name = "cl100k_base"  # Default
            
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            # Fallback: rough estimate of 1 token per 4 characters
            return len(text) // 4