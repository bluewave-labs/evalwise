from typing import Dict, Type, Any
from .base import BaseEvaluator
from .llm_judge import LLMJudgeEvaluator
from .rule_based import RuleBasedEvaluator
from .pii_detector import PIIDetectorEvaluator
from .toxicity_detector import ToxicityDetectorEvaluator

class EvaluatorFactory:
    """Factory for creating evaluators"""
    
    _evaluators: Dict[str, Type[BaseEvaluator]] = {
        "llm_judge": LLMJudgeEvaluator,
        "rule_based": RuleBasedEvaluator,
        "pii_regex": PIIDetectorEvaluator,
        "toxicity": ToxicityDetectorEvaluator,
    }
    
    @classmethod
    def create_evaluator(cls, kind: str, config: Dict[str, Any]) -> BaseEvaluator:
        """Create evaluator of the specified kind"""
        
        if kind not in cls._evaluators:
            raise ValueError(f"Unsupported evaluator kind: {kind}")
        
        evaluator_class = cls._evaluators[kind]
        return evaluator_class(config)
    
    @classmethod
    def register_evaluator(cls, kind: str, evaluator_class: Type[BaseEvaluator]):
        """Register a new evaluator"""
        cls._evaluators[kind] = evaluator_class
    
    @classmethod
    def list_kinds(cls) -> list:
        """List all available evaluator kinds"""
        return list(cls._evaluators.keys())
    
    @classmethod
    def get_default_configs(cls) -> Dict[str, Dict[str, Any]]:
        """Get default configurations for each evaluator kind"""
        return {
            "llm_judge": {
                "judge_model": "gpt-4",
                "judge_provider": "openai",
                "rubric": "general",
                "threshold": 0.5
            },
            "rule_based": {
                "denylist": ["bomb", "weapon", "kill", "suicide", "hate"],
                "allowlist": [],
                "case_sensitive": False,
                "match_mode": "contains"
            },
            "pii_regex": {
                "patterns": ["email", "phone", "ssn", "credit_card"],
                "fail_on_any": True,
                "severity_weights": {
                    "ssn": 1.0,
                    "credit_card": 1.0,
                    "email": 0.8,
                    "phone": 0.8
                }
            }
        }