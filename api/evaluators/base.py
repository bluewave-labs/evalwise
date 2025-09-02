from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class EvaluationResult:
    """Standardized evaluation result"""
    score: Optional[float]  # 0.0 to 1.0
    pass_fail: Optional[bool]
    notes: Optional[str]
    raw_data: Optional[Dict[str, Any]] = None

class BaseEvaluator(ABC):
    """Base class for all evaluators"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """Evaluate the model output"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return evaluator name"""
        pass
    
    @property
    @abstractmethod
    def kind(self) -> str:
        """Return evaluator kind/type"""
        pass