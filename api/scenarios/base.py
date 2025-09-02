from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseScenarioGenerator(ABC):
    """Base class for scenario generators"""
    
    def __init__(self, params: Dict[str, Any]):
        self.params = params
    
    @abstractmethod
    def generate_prompt(self, base_input: str, metadata: Dict[str, Any] = None) -> str:
        """Generate adversarial prompt from base input"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return scenario name"""
        pass
    
    @property
    @abstractmethod
    def type(self) -> str:
        """Return scenario type"""
        pass
    
    @property
    def description(self) -> str:
        """Return scenario description"""
        return f"{self.name} scenario generator"
    
    def validate_params(self) -> bool:
        """Validate scenario parameters"""
        return True