from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time

@dataclass
class ModelResponse:
    """Standardized model response across all providers"""
    content: str
    latency_ms: int
    token_input: Optional[int] = None
    token_output: Optional[int] = None
    cost_usd: Optional[float] = None
    raw_response: Optional[Dict[str, Any]] = None

class BaseModelAdapter(ABC):
    """Base class for all model adapters"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model_name: str,
        **kwargs
    ) -> ModelResponse:
        """Generate response from the model"""
        pass
    
    @abstractmethod
    def estimate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost in USD for the request"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens in text for the given model"""
        pass
    
    def _calculate_latency(self, start_time: float) -> int:
        """Calculate latency in milliseconds"""
        return int((time.time() - start_time) * 1000)