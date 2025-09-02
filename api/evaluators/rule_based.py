import re
from typing import Dict, Any, Optional, List
from .base import BaseEvaluator, EvaluationResult

class RuleBasedEvaluator(BaseEvaluator):
    """Rule-based evaluator using regex patterns and blocklists"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.denylist = config.get("denylist", [])
        self.allowlist = config.get("allowlist", [])
        self.case_sensitive = config.get("case_sensitive", False)
        self.match_mode = config.get("match_mode", "contains")  # "contains", "exact", "regex"
        
        # Compile regex patterns if needed
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        flags = 0 if self.case_sensitive else re.IGNORECASE
        
        if self.match_mode == "regex":
            self.compiled_denylist = [re.compile(pattern, flags) for pattern in self.denylist]
            self.compiled_allowlist = [re.compile(pattern, flags) for pattern in self.allowlist]
        else:
            self.compiled_denylist = []
            self.compiled_allowlist = []
    
    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """Evaluate using rule-based patterns"""
        
        # Prepare text for matching
        text_to_check = output_text
        if not self.case_sensitive:
            text_to_check = text_to_check.lower()
            
        issues = []
        violations = 0
        total_checks = 0
        
        # Check denylist
        for item in self.denylist:
            total_checks += 1
            if self._matches(text_to_check, item):
                violations += 1
                issues.append(f"Denied pattern found: '{item}'")
        
        # Check allowlist (if specified, text must contain at least one allowed pattern)
        if self.allowlist:
            total_checks += 1
            allowed_found = False
            for item in self.allowlist:
                if self._matches(text_to_check, item):
                    allowed_found = True
                    break
            
            if not allowed_found:
                violations += 1
                issues.append("No allowed patterns found in output")
        
        # Calculate score and pass/fail
        if total_checks == 0:
            score = 1.0  # No rules to check
            pass_result = True
        else:
            score = max(0.0, (total_checks - violations) / total_checks)
            pass_result = violations == 0
        
        notes = f"Found {violations} violations out of {total_checks} checks"
        if issues:
            notes += f": {'; '.join(issues)}"
        
        return EvaluationResult(
            score=score,
            pass_fail=pass_result,
            notes=notes,
            raw_data={
                "violations": violations,
                "total_checks": total_checks,
                "issues": issues,
                "denylist_matches": [item for item in self.denylist if self._matches(text_to_check, item)],
                "allowlist_matches": [item for item in self.allowlist if self._matches(text_to_check, item)] if self.allowlist else []
            }
        )
    
    def _matches(self, text: str, pattern: str) -> bool:
        """Check if pattern matches text based on match mode"""
        if self.match_mode == "regex":
            # Use precompiled regex
            compiled_pattern = next(
                (p for p in self.compiled_denylist + self.compiled_allowlist 
                 if p.pattern == pattern), None
            )
            if compiled_pattern:
                return bool(compiled_pattern.search(text))
            else:
                # Fallback to compiling on the fly
                flags = 0 if self.case_sensitive else re.IGNORECASE
                return bool(re.search(pattern, text, flags))
        
        elif self.match_mode == "exact":
            compare_pattern = pattern if self.case_sensitive else pattern.lower()
            return text == compare_pattern
        
        else:  # contains
            compare_pattern = pattern if self.case_sensitive else pattern.lower()
            return compare_pattern in text
    
    @property
    def name(self) -> str:
        return f"Rule-based ({self.match_mode})"
    
    @property
    def kind(self) -> str:
        return "rule_based"