from typing import Dict, Type, Optional
from .base import BaseModelAdapter
from .openai_adapter import OpenAIAdapter
from .ollama_adapter import OllamaAdapter
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from database import get_db

class ModelAdapterFactory:
    """Factory for creating model adapters"""
    
    _adapters: Dict[str, Type[BaseModelAdapter]] = {
        "openai": OpenAIAdapter,
        "azure_openai": OpenAIAdapter,
        "local_openai": OpenAIAdapter,
        "ollama": OllamaAdapter,
    }
    
    @classmethod
    def get_organization_api_key(cls, provider: str, organization_id: str, db: Session) -> Optional[str]:
        """Retrieve and decrypt API key for provider from organization's stored keys"""
        try:
            from auth.models import EncryptedApiKey
            from utils.encryption import encryption
            
            # Find the API key for this provider and organization
            encrypted_key_record = db.query(EncryptedApiKey).filter(
                EncryptedApiKey.provider == provider,
                EncryptedApiKey.organization_id == organization_id,
                EncryptedApiKey.is_active == True
            ).first()
            
            if not encrypted_key_record:
                return None
            
            # Decrypt the API key
            return encryption.decrypt_api_key(encrypted_key_record.encrypted_key)
            
        except Exception as e:
            print(f"Failed to retrieve API key for {provider}: {str(e)}")
            return None
    
    @classmethod
    def create_adapter(
        cls,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        organization_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> BaseModelAdapter:
        """Create adapter for the specified provider"""
        
        if provider not in cls._adapters:
            raise ValueError(f"Unsupported provider: {provider}")
        
        adapter_class = cls._adapters[provider]
        
        # Try to get API key from organization's stored keys first
        if not api_key and organization_id and db:
            stored_api_key = cls.get_organization_api_key(provider, organization_id, db)
            if stored_api_key:
                api_key = stored_api_key
                print(f"Using stored API key for {provider} from organization {organization_id}")
        
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