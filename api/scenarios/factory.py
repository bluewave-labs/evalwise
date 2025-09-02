from typing import Dict, Type, Any
from .base import BaseScenarioGenerator
from .jailbreak_basic import JailbreakBasicGenerator
from .safety_probe import SafetyProbeGenerator
from .privacy_probe import PrivacyProbeGenerator

class ScenarioGeneratorFactory:
    """Factory for creating scenario generators"""
    
    _generators: Dict[str, Type[BaseScenarioGenerator]] = {
        "jailbreak_basic": JailbreakBasicGenerator,
        "safety_probe": SafetyProbeGenerator,
        "privacy_probe": PrivacyProbeGenerator,
    }
    
    @classmethod
    def create_generator(cls, scenario_type: str, params: Dict[str, Any]) -> BaseScenarioGenerator:
        """Create scenario generator of the specified type"""
        
        if scenario_type not in cls._generators:
            raise ValueError(f"Unsupported scenario type: {scenario_type}")
        
        generator_class = cls._generators[scenario_type]
        return generator_class(params)
    
    @classmethod
    def register_generator(cls, scenario_type: str, generator_class: Type[BaseScenarioGenerator]):
        """Register a new scenario generator"""
        cls._generators[scenario_type] = generator_class
    
    @classmethod
    def list_types(cls) -> list:
        """List all available scenario types"""
        return list(cls._generators.keys())
    
    @classmethod
    def get_default_params(cls) -> Dict[str, Dict[str, Any]]:
        """Get default parameters for each scenario type"""
        return {
            "jailbreak_basic": {
                "techniques": ["dan", "roleplay", "hypothetical"],
                "randomize": True
            },
            "safety_probe": {
                "categories": ["violence", "self_harm", "hate_speech"],
                "directness": "indirect",
                "randomize": True
            },
            "privacy_probe": {
                "probe_types": ["personal_info", "system_prompt"],
                "approach": "indirect",
                "randomize": True
            }
        }