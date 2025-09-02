from typing import Dict, Type, Optional
from .base import BaseModelAdapter
from .openai_adapter import OpenAIAdapter
from .ollama_adapter import OllamaAdapter
import os

class ModelAdapterFactory:
    """Factory for creating model adapters"""
    
    _adapters: Dict[str, Type[BaseModelAdapter]] = {
        "openai": OpenAIAdapter,
        "azure_openai": OpenAIAdapter,
        "local_openai": OpenAIAdapter,
        "ollama": OllamaAdapter,
    }
    
    @classmethod
    def create_adapter(
        self,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> BaseModelAdapter:
        """Create adapter for the specified provider"""
        
        if provider not in self._adapters:
            raise ValueError(f"Unsupported provider: {provider}")
        
        adapter_class = self._adapters[provider]
        
        # Handle provider-specific configurations
        if provider == "openai":
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            base_url = base_url or "https://api.openai.com/v1"
        
        elif provider == "azure_openai":
            api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
            base_url = base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
            if not base_url:
                raise ValueError("AZURE_OPENAI_ENDPOINT environment variable required")
        
        elif provider == "local_openai":
            # Local OpenAI-compatible server (e.g., vLLM, LocalAI)
            api_key = api_key or "dummy-key"  # Many local servers don't require real keys
            base_url = base_url or "http://localhost:8000/v1"
        
        elif provider == "ollama":
            # Ollama local server
            api_key = api_key or "dummy-key"  # Ollama doesn't require API keys
            base_url = base_url or "http://localhost:11434"
        
        # Only require API keys for cloud providers
        if provider in ["openai", "azure_openai"] and not api_key:
            raise ValueError(f"API key required for provider: {provider}")
        
        return adapter_class(api_key=api_key, base_url=base_url)
    
    @classmethod
    def register_adapter(cls, provider: str, adapter_class: Type[BaseModelAdapter]):
        """Register a new adapter"""
        cls._adapters[provider] = adapter_class
    
    @classmethod
    def list_providers(cls) -> list:
        """List all available providers"""
        return list(cls._adapters.keys())