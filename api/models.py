from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

class Dataset(Base):
    __tablename__ = "dataset"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    version_hash = Column(String, nullable=False)
    tags = Column(ARRAY(String), default=[])
    schema_json = Column(JSON)
    is_synthetic = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    items = relationship("Item", back_populates="dataset")
    runs = relationship("Run", back_populates="dataset")

class Item(Base):
    __tablename__ = "item"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("dataset.id"), nullable=False)
    input_json = Column(JSON, nullable=False)
    expected_json = Column(JSON)
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    dataset = relationship("Dataset", back_populates="items")
    results = relationship("Result", back_populates="item")

class Scenario(Base):
    __tablename__ = "scenario"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # jailbreak_basic, safety_probe, etc.
    params_json = Column(JSON, default={})
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    results = relationship("Result", back_populates="scenario")

class Evaluator(Base):
    __tablename__ = "evaluator"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # llm_judge, rule_based, pii_regex, etc.
    config_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    evaluations = relationship("Evaluation", back_populates="evaluator")

class Run(Base):
    __tablename__ = "run"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("dataset.id"), nullable=False)
    dataset_version_hash = Column(String, nullable=False)
    scenario_ids = Column(ARRAY(UUID), default=[])
    model_provider = Column(String, nullable=False)  # openai, azure_openai, etc.
    model_name = Column(String, nullable=False)
    model_params_json = Column(JSON, default={})
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    status = Column(String, default="pending")  # pending, running, completed, failed
    owner = Column(String)
    
    dataset = relationship("Dataset", back_populates="runs")
    results = relationship("Result", back_populates="run")

class Result(Base):
    __tablename__ = "result"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("run.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("item.id"), nullable=False)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("scenario.id"), nullable=False)
    output_json = Column(JSON)  # model response
    latency_ms = Column(Integer)
    token_input = Column(Integer)
    token_output = Column(Integer)
    cost_usd = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    run = relationship("Run", back_populates="results")
    item = relationship("Item", back_populates="results")
    scenario = relationship("Scenario", back_populates="results")
    evaluations = relationship("Evaluation", back_populates="result")

class Evaluation(Base):
    __tablename__ = "evaluation"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id = Column(UUID(as_uuid=True), ForeignKey("result.id"), nullable=False)
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("evaluator.id"), nullable=False)
    score_float = Column(Float)
    pass_bool = Column(Boolean)
    notes_text = Column(Text)
    raw_json = Column(JSON)
    
    result = relationship("Result", back_populates="evaluations")
    evaluator = relationship("Evaluator", back_populates="evaluations")

# Indexes for performance
Index('idx_run_status', Run.status)
Index('idx_result_run_id', Result.run_id)
Index('idx_dataset_tags', Dataset.tags, postgresql_using='gin')
Index('idx_scenario_tags', Scenario.tags, postgresql_using='gin')
Index('idx_created_at_retention', Result.created_at)  # For retention cleanup