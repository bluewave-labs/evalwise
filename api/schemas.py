from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid

# Dataset schemas
class DatasetCreate(BaseModel):
    name: str
    tags: List[str] = []
    is_synthetic: bool = False

class DatasetResponse(BaseModel):
    id: uuid.UUID
    name: str
    version_hash: str
    tags: List[str]
    schema_json: Optional[Dict[str, Any]]
    is_synthetic: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Item schemas
class ItemCreate(BaseModel):
    input: Dict[str, Any]
    expected: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}

class ItemResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    input_json: Dict[str, Any]
    expected_json: Optional[Dict[str, Any]]
    metadata_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Scenario schemas
class ScenarioCreate(BaseModel):
    name: str
    type: str
    params: Dict[str, Any] = {}
    tags: List[str] = []

class ScenarioResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    params_json: Dict[str, Any]
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Evaluator schemas
class EvaluatorCreate(BaseModel):
    name: str
    kind: str
    config: Dict[str, Any] = {}

class EvaluatorResponse(BaseModel):
    id: uuid.UUID
    name: str
    kind: str
    config_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Run schemas
class ModelConfig(BaseModel):
    provider: str
    name: str
    params: Dict[str, Any] = {}

class RunCreate(BaseModel):
    name: Optional[str] = None
    dataset_id: uuid.UUID
    scenario_ids: List[uuid.UUID]
    model: ModelConfig
    evaluator_ids: List[uuid.UUID]

class RunResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str]
    dataset_id: uuid.UUID
    dataset_version_hash: str
    scenario_ids: List[uuid.UUID]
    model_provider: str
    model_name: str
    model_params_json: Dict[str, Any]
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    owner: Optional[str]

    class Config:
        from_attributes = True

# Result schemas
class ResultResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    item_id: uuid.UUID
    scenario_id: uuid.UUID
    output_json: Optional[Dict[str, Any]]
    latency_ms: Optional[int]
    token_input: Optional[int]
    token_output: Optional[int]
    cost_usd: Optional[float]
    created_at: datetime
    evaluations: List['EvaluationResponse'] = []

    class Config:
        from_attributes = True

# Evaluation schemas
class EvaluationResponse(BaseModel):
    id: uuid.UUID
    result_id: uuid.UUID
    evaluator_id: uuid.UUID
    score_float: Optional[float]
    pass_bool: Optional[bool]
    notes_text: Optional[str]
    raw_json: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# Playground schemas
class PlaygroundRequest(BaseModel):
    prompt: str
    model: ModelConfig
    evaluator_ids: List[uuid.UUID]
    save_to_dataset: Optional[uuid.UUID] = None

class PlaygroundResponse(BaseModel):
    output: str
    latency_ms: int
    token_input: Optional[int]
    token_output: Optional[int]
    cost_usd: Optional[float]
    evaluations: List[EvaluationResponse]

# Run aggregations
class RunAggregates(BaseModel):
    total_results: int
    pass_rate_overall: float
    pass_rate_by_evaluator: Dict[str, float]
    pass_rate_by_scenario: Dict[str, float]
    mean_score_by_evaluator: Dict[str, float]
    mean_latency_ms: Optional[float]
    total_cost_usd: Optional[float]

# Update forward references
ResultResponse.model_rebuild()