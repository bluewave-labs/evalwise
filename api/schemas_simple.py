from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uuid

class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Dataset name")
    tags: List[str] = Field(default=[], max_items=20, description="Dataset tags")
    is_synthetic: bool = Field(default=False, description="Whether dataset is synthetically generated")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Remove empty tags and duplicates
            cleaned_tags = list(set(tag.strip() for tag in v if tag and tag.strip()))
            return cleaned_tags
        return []

class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Scenario name")
    type: str = Field(..., min_length=1, max_length=50, description="Scenario type")
    params: Dict[str, Any] = Field(default={}, description="Scenario parameters")
    tags: List[str] = Field(default=[], max_items=20, description="Scenario tags")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('type')
    def validate_type(cls, v):
        if not v or not v.strip():
            raise ValueError('Type cannot be empty')
        allowed_types = ['jailbreak', 'prompt_injection', 'toxicity', 'bias', 'custom']
        if v.strip().lower() not in allowed_types:
            raise ValueError(f'Type must be one of: {", ".join(allowed_types)}')
        return v.strip().lower()
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            cleaned_tags = list(set(tag.strip() for tag in v if tag and tag.strip()))
            return cleaned_tags
        return []

class EvaluatorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Evaluator name")
    kind: str = Field(..., min_length=1, max_length=50, description="Evaluator kind")
    config: Dict[str, Any] = Field(default={}, description="Evaluator configuration")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('kind')
    def validate_kind(cls, v):
        if not v or not v.strip():
            raise ValueError('Kind cannot be empty')
        allowed_kinds = ['llm_judge', 'rule_based', 'pii_regex', 'toxicity', 'similarity', 'bias', 'factuality', 'custom']
        if v.strip().lower() not in allowed_kinds:
            raise ValueError(f'Kind must be one of: {", ".join(allowed_kinds)}')
        return v.strip().lower()

class RunCreate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Run name")
    dataset_id: str = Field(..., description="Dataset UUID")
    scenario_ids: List[str] = Field(default=[], max_items=10, description="Scenario UUIDs")
    model_provider: str = Field(default="openai", min_length=1, max_length=50, description="Model provider")
    model_name: str = Field(default="gpt-3.5-turbo", min_length=1, max_length=100, description="Model name")
    model_params: Dict[str, Any] = Field(default={}, description="Model parameters")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Name cannot be empty string')
        return v.strip() if v else None
    
    @validator('dataset_id')
    def validate_dataset_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Dataset ID must be a valid UUID')
        return v
    
    @validator('scenario_ids')
    def validate_scenario_ids(cls, v):
        if v:
            for sid in v:
                try:
                    uuid.UUID(sid)
                except ValueError:
                    raise ValueError(f'Scenario ID must be a valid UUID: {sid}')
        return v
    
    @validator('model_provider')
    def validate_model_provider(cls, v):
        if not v or not v.strip():
            raise ValueError('Model provider cannot be empty')
        allowed_providers = ['openai', 'anthropic', 'huggingface', 'ollama', 'custom']
        if v.strip().lower() not in allowed_providers:
            raise ValueError(f'Model provider must be one of: {", ".join(allowed_providers)}')
        return v.strip().lower()
    
    @validator('model_name')
    def validate_model_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Model name cannot be empty')
        return v.strip()

class PlaygroundRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000, description="Prompt text to test")
    model_provider: str = Field(default="openai", min_length=1, max_length=50, description="Model provider")
    model_name: str = Field(default="gpt-3.5-turbo", min_length=1, max_length=100, description="Model name")
    evaluator_ids: List[str] = Field(default=[], max_items=5, description="Evaluator UUIDs")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v.strip()
    
    @validator('model_provider')
    def validate_model_provider(cls, v):
        if not v or not v.strip():
            raise ValueError('Model provider cannot be empty')
        allowed_providers = ['openai', 'anthropic', 'huggingface', 'ollama', 'custom']
        if v.strip().lower() not in allowed_providers:
            raise ValueError(f'Model provider must be one of: {", ".join(allowed_providers)}')
        return v.strip().lower()
    
    @validator('model_name')
    def validate_model_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Model name cannot be empty')
        return v.strip()
    
    @validator('evaluator_ids')
    def validate_evaluator_ids(cls, v):
        if v:
            for eid in v:
                try:
                    uuid.UUID(eid)
                except ValueError:
                    raise ValueError(f'Evaluator ID must be a valid UUID: {eid}')
        return v