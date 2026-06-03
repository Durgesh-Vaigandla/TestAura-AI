from typing import Dict, Any, List

class RequirementAnalyzer:
    def __init__(self):
        self.ambiguous_words = ['some', 'few', 'many', 'often', 'probably', 'might', 'could', 'user-friendly', 'easy', 'simple', 'fast', 'quick']
        self.weak_words = ['support', 'allow', 'enable', 'manage', 'handle']

    def analyze(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a requirement and returns health score and quality issues.
        Calculates score based on Completeness, Clarity, Testability, Coverage, Validation Readiness.
        """
        issues = []
        score = 100
        
        description = req.get("description", "").lower()
        
        # 1. Completeness
        if not req.get("actor") or req.get("actor") == "System":
            issues.append("Missing explicit actor role.")
            score -= 10
            
        if not req.get("action") or req.get("action") == "perform action":
            issues.append("Missing explicit action.")
            score -= 15
            
        # 2. Clarity (Ambiguous words)
        found_ambiguous = [word for word in self.ambiguous_words if word in description.split()]
        if found_ambiguous:
            issues.append(f"Ambiguous wording detected: {', '.join(found_ambiguous)}.")
            score -= 5 * len(found_ambiguous)
            
        # 3. Testability
        if "fast" in description or "quick" in description or "user-friendly" in description:
            issues.append("Untestable requirement: quantify subjective terms.")
            score -= 15
            
        # 4. Validation Readiness
        if not req.get("validations"):
            issues.append("Missing validation rules.")
            score -= 10
            
        # 5. Role definitions
        if not req.get("roles") and req.get("req_type") != "System":
            issues.append("Missing role definitions.")
            score -= 10
            
        # Finalize score
        score = max(0, min(100, score))
        
        return {
            "health_score": score,
            "issues": issues
        }

requirement_analyzer = RequirementAnalyzer()
