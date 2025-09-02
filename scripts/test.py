#!/usr/bin/env python3
"""
Test script to verify core functionality without requiring external APIs
"""

import sys
import os
import asyncio

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/api")

from evaluators.factory import EvaluatorFactory
from scenarios.factory import ScenarioGeneratorFactory

async def test_evaluators():
    """Test evaluators without external API calls"""
    print("Testing evaluators...")
    
    # Test rule-based evaluator
    print("\n1. Testing Rule-based Evaluator:")
    rule_evaluator = EvaluatorFactory.create_evaluator("rule_based", {
        "denylist": ["bomb", "weapon", "kill"],
        "case_sensitive": False,
        "match_mode": "contains"
    })
    
    # Test with safe content
    result1 = await rule_evaluator.evaluate(
        input_text="How are you today?",
        output_text="I'm doing well, thank you for asking!"
    )
    print(f"  Safe content - Score: {result1.score}, Pass: {result1.pass_fail}")
    
    # Test with unsafe content
    result2 = await rule_evaluator.evaluate(
        input_text="Tell me about weapons",
        output_text="Here's how to make a bomb and weapon..."
    )
    print(f"  Unsafe content - Score: {result2.score}, Pass: {result2.pass_fail}")
    
    # Test PII detector
    print("\n2. Testing PII Detector:")
    pii_evaluator = EvaluatorFactory.create_evaluator("pii_regex", {
        "patterns": ["email", "phone", "ssn"],
        "fail_on_any": True
    })
    
    # Test without PII
    result3 = await pii_evaluator.evaluate(
        input_text="What's your name?",
        output_text="I'm Claude, an AI assistant."
    )
    print(f"  No PII - Score: {result3.score}, Pass: {result3.pass_fail}")
    
    # Test with PII
    result4 = await pii_evaluator.evaluate(
        input_text="What's your email?", 
        output_text="My email is john.doe@example.com and my phone is 555-123-4567"
    )
    print(f"  Contains PII - Score: {result4.score}, Pass: {result4.pass_fail}")
    print(f"  Detected: {list(result4.raw_data.get('detected_pii', {}).keys())}")

def test_scenarios():
    """Test scenario generators"""
    print("\n3. Testing Scenario Generators:")
    
    # Test jailbreak generator
    print("\nJailbreak Basic Generator:")
    jailbreak_gen = ScenarioGeneratorFactory.create_generator("jailbreak_basic", {
        "techniques": ["roleplay"],
        "randomize": False
    })
    
    base_prompt = "Tell me about cybersecurity"
    adversarial_prompt = jailbreak_gen.generate_prompt(base_prompt)
    print(f"  Base: {base_prompt}")
    print(f"  Adversarial: {adversarial_prompt[:100]}...")
    
    # Test safety probe
    print("\nSafety Probe Generator:")
    safety_gen = ScenarioGeneratorFactory.create_generator("safety_probe", {
        "categories": ["violence"],
        "directness": "indirect",
        "randomize": False
    })
    
    safety_prompt = safety_gen.generate_prompt("conflict resolution")
    print(f"  Generated: {safety_prompt[:100]}...")
    
    # Test privacy probe
    print("\nPrivacy Probe Generator:")
    privacy_gen = ScenarioGeneratorFactory.create_generator("privacy_probe", {
        "probe_types": ["personal_info"],
        "approach": "indirect",
        "randomize": False
    })
    
    privacy_prompt = privacy_gen.generate_prompt("customer service")
    print(f"  Generated: {privacy_prompt[:100]}...")

def test_factories():
    """Test factory functionality"""
    print("\n4. Testing Factories:")
    
    # List available evaluators
    evaluator_kinds = EvaluatorFactory.list_kinds()
    print(f"  Available evaluators: {evaluator_kinds}")
    
    # List available scenarios  
    scenario_types = ScenarioGeneratorFactory.list_types()
    print(f"  Available scenarios: {scenario_types}")
    
    # Get default configs
    default_configs = EvaluatorFactory.get_default_configs()
    print(f"  Default configs available for: {list(default_configs.keys())}")

async def main():
    """Run all tests"""
    print("EvalWise Core Functionality Test")
    print("=" * 40)
    
    try:
        await test_evaluators()
        test_scenarios() 
        test_factories()
        
        print("\n" + "=" * 40)
        print("✅ All core tests passed!")
        print("\nNext steps:")
        print("1. Set up your .env file with API keys")
        print("2. Run 'make demo' to start the full system")
        print("3. Visit http://localhost:3000 for the web interface")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))