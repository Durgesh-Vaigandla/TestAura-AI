import json
import re
from typing import Dict, Any, List
from app.services.llm_service import llm_service
from app.services.rule_engine import rule_engine

class ScenarioBuilder:
    def build_from_requirement(self, req: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Builds scenarios for a requirement using the local SLM via LLMService.
        Falls back to rule_engine if LLM fails or is unavailable.
        """
        prompt = f"""
You are an expert QA Engineer writing comprehensive enterprise BDD test scenarios.
Generate comprehensive testing scenarios for the following software requirement.
Include Smoke Tests, Happy Paths, Negative Tests, Validations, and RBAC (Role-Based Access Control) tests.

Requirement Details:
Title: {req.get('title', '')}
Description: {req.get('description', '')}
Actor: {req.get('actor', '')}
Action: {req.get('action', '')}
Roles required: {', '.join(req.get('roles', []))}
Security Rules: {', '.join(req.get('security_rules', []))}
Integrations: {', '.join(req.get('integration_points', []))}

Return ONLY a valid JSON array of objects. Do not include any markdown formatting, explanation, or extra text.
Format strictly as:
[
  {{
    "title": "Scenario description",
    "type": "Smoke Test | Happy Path | Negative Test | Validation | RBAC",
    "given": "initial context",
    "when": "action performed",
    "then": "expected outcome"
  }}
]
"""
        raw_response = llm_service.generate(prompt, max_tokens=1500, temperature=0.3)
        
        if raw_response:
            try:
                # Attempt to extract JSON if the LLM wrapped it in markdown
                json_match = re.search(r'\[.*\]', raw_response, re.DOTALL)
                if json_match:
                    raw_response = json_match.group(0)
                    
                scenarios_data = json.loads(raw_response)
                
                # Format into the expected structure
                scenarios = []
                for tpl in scenarios_data:
                    scenario = {
                        "title": tpl.get("title", "Generated Scenario"),
                        "scenario_type": tpl.get("type", "General"),
                        "given": tpl.get("given", ""),
                        "when": tpl.get("when", ""),
                        "then": tpl.get("then", ""),
                        "status": "Generated"
                    }
                    scenarios.append(scenario)
                    
                if scenarios:
                    return scenarios
            except Exception as e:
                print(f"Failed to parse SLM JSON: {e}. Raw response: {raw_response}")
                
        # Fallback to rule engine if LLM fails, hallucinates, or is not loaded
        print("Falling back to deterministic rule engine...")
        templates = rule_engine.evaluate(req)
        scenarios = []
        for tpl in templates:
            scenario = {
                "title": tpl["title"],
                "scenario_type": tpl["type"],
                "given": tpl["given"],
                "when": tpl["when"],
                "then": tpl["then"],
                "status": "Generated"
            }
            scenarios.append(scenario)
            
        return scenarios

scenario_builder = ScenarioBuilder()
