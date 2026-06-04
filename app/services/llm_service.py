import os
import json
from typing import Dict, Any, List
from app.config import Config
from app.services.task_manager import task_manager

try:
    from llama_cpp import Llama
    _HAS_LLAMA = True
except ImportError:
    _HAS_LLAMA = False

class LLMService:
    def __init__(self):
        self.llm = None
        self.model_path = Config.LLM_MODEL_PATH
        self.is_loaded = False
        
    def load_model(self):
        if not _HAS_LLAMA:
            print("llama-cpp-python is not installed. LLM service disabled.")
            return False
            
        if not os.path.exists(self.model_path):
            print(f"Model not found at {self.model_path}. LLM service disabled.")
            return False
            
        if not self.is_loaded:
            print("Loading LLM model (Metal Accelerated)...")
            try:
                self.llm = Llama(
                    model_path=self.model_path,
                    n_gpu_layers=-1, # Use Metal for all layers on Apple Silicon
                    n_ctx=4096,      # Context window
                    verbose=False
                )
                self.is_loaded = True
                print("Model loaded successfully.")
            except Exception as e:
                print(f"Failed to load model: {e}")
                return False
            
        return True
        
    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.5, stop: List[str] = None) -> str:
        """Generic generation method for any prompt."""
        if not self.is_loaded and not self.load_model():
            return ""
            
        try:
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            print(f"LLM Generation Error: {e}")
            return ""

    def refine_scenario_wording(self, scenario: Dict[str, Any]) -> str:
        """
        Uses LLM to improve the wording of a scenario.
        Returns the refined scenario text.
        """
        prompt = f"""
You are an expert QA Engineer. Refine the following BDD scenario to use professional, clear business language.
Do not change the fundamental logic.

Original:
Title: {scenario['title']}
Given {scenario['given']}
When {scenario['when']}
Then {scenario['then']}

Refined (Return ONLY the Gherkin text):
"""
        return self.generate(prompt, max_tokens=256, temperature=0.3, stop=["\n\n"])
        
    def get_quality_feedback(self, requirement: Dict[str, Any]) -> str:
        if not self.is_loaded and not self.load_model():
            return "AI feedback disabled."
            
        prompt = f"""
Review the following software requirement:
Title: {requirement['title']}
Description: {requirement['description']}

Provide exactly 3 concise bullet points on how to improve its clarity and testability.
"""
        try:
            response = self.llm(
                prompt,
                max_tokens=150,
                temperature=0.2
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return f"Error getting feedback: {str(e)}"

    def generate_execution_intent(self, scenario: Dict[str, Any], target_url: str) -> List[Dict[str, str]]:
        """
        Translates a BDD scenario into a deterministic JSON Execution Intent array.
        """
        if not self.is_loaded and not self.load_model():
            # Fallback for when LLM is disabled
            return [{"action": "navigate", "target": target_url}]
            
        prompt = f"""
You are an expert Automation Engineer. Convert the following BDD scenario into a precise JSON array of execution intents.
Target Base URL: {target_url}

Scenario:
Title: {scenario.get('title', '')}
Given {scenario.get('given', '')}
When {scenario.get('when', '')}
Then {scenario.get('then', '')}

Rules:
1. Return ONLY a valid JSON array. No markdown, no explanations.
2. Supported actions: "navigate", "fill", "click", "assert_visible"
3. Use the 'target' field for URLs or click targets. Use the 'field' and 'value' fields for filling inputs.

Format exactly like this example:
[
  {{"action": "navigate", "target": "{target_url}"}},
  {{"action": "fill", "field": "username", "value": "testuser"}},
  {{"action": "click", "target": "login_button"}},
  {{"action": "assert_visible", "target": "dashboard_header"}}
]
"""
        try:
            raw_response = self.generate(prompt, max_tokens=1000, temperature=0.1)
            
            # Clean up markdown code blocks if present
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
                
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
                
            import re
            json_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
            if json_match:
                cleaned_response = json_match.group(0)
                
            intents = json.loads(cleaned_response)
            
            # Ensure navigate is the first step if not present
            if not intents or intents[0].get('action') != 'navigate':
                intents.insert(0, {"action": "navigate", "target": target_url})
                
            return intents
        except Exception as e:
            print(f"Failed to parse Intent JSON: {e}")
            print(f"RAW LLM OUTPUT:\n{raw_response}")
            
            # Enterprise Heuristic Fallback: 
            # If the small 0.5B model fails JSON formatting, we manually parse the raw text for keywords!
            intents = [{"action": "navigate", "target": target_url}]
            lower_text = raw_response.lower() + " " + scenario.get('when', '').lower()
            
            if "fill" in lower_text or "type" in lower_text or "enter" in lower_text:
                if "username" in lower_text or "email" in lower_text:
                    intents.append({"action": "fill", "field": "username", "value": "testuser"})
                if "password" in lower_text:
                    intents.append({"action": "fill", "field": "password", "value": "password123"})
                    
            if "click" in lower_text or "submit" in lower_text or "login" in lower_text:
                intents.append({"action": "click", "target": "login_button"})
                
            return intents

    def generate_adhoc_scenarios(self, prompt_text: str, project_context: str = "") -> List[Dict[str, str]]:
        """
        Parses a conversational prompt into 1-3 strict BDD Scenarios for ad-hoc execution.
        """
        if not self.is_loaded and not self.load_model():
            return [{
                "title": "Fallback Scenario",
                "given": "the user is on the page",
                "when": "they perform the requested action",
                "then": "the expected result occurs",
                "scenario_type": "Happy Path"
            }]
            
        context_block = f"\nPROJECT CONTEXT (Strict Business Rules):\n{project_context}\n" if project_context else ""
            
        prompt = f"""
You are an expert Test Automation Engineer. Convert the following user request into exactly ONE or TWO highly precise BDD Scenarios.
{context_block}
User Request: "{prompt_text}"

Rules:
1. Return ONLY a valid JSON array of scenario objects. No explanations or markdown blocks.
2. The JSON keys must be exactly: "title", "given", "when", "then", "scenario_type".
3. Keep the steps extremely explicit so they can be parsed into browser actions. MUST strictly follow the Project Context rules if provided.

Example format:
[
  {{
    "title": "Valid Login",
    "scenario_type": "Happy Path",
    "given": "user is on the login page",
    "when": "user fills username with dummy1 and fills password with pass1 and clicks login",
    "then": "user should see dashboard"
  }}
]
"""
        try:
            raw_response = self.generate(prompt, max_tokens=1000, temperature=0.2)
            
            # Clean up markdown code blocks if present
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
                
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
                
            import re
            json_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
            if json_match:
                cleaned_response = json_match.group(0)
            else:
                # Might be a single object
                obj_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if obj_match:
                    cleaned_response = f"[{obj_match.group(0)}]"
                    
            parsed_data = json.loads(cleaned_response)
            if isinstance(parsed_data, dict):
                parsed_data = [parsed_data]
            return parsed_data
        except Exception as e:
            print(f"Failed to parse Ad-Hoc Scenarios: {e}")
            print(f"RAW LLM OUTPUT:\n{raw_response}")
            return [{
                "title": "Failed to parse AI output",
                "given": "system error",
                "when": "attempting generation",
                "then": "fallback to default",
                "scenario_type": "Error"
            }]

    def generate_discovery_scenarios(self, dom_summary: str, project_context: str = "") -> List[Dict[str, str]]:
        """
        Takes a JSON dump of the DOM (inputs, buttons) and generates test cases.
        """
        if not self.is_loaded and not self.load_model():
            return [{"title": "Fallback", "given": "UI", "when": "Interact", "then": "Pass", "scenario_type": "Happy Path"}]
            
        context_block = f"\nPROJECT CONTEXT (Strict Business Rules):\n{project_context}\n" if project_context else ""
            
        prompt = f"""
You are an expert QA Automation AI. I have extracted the interactive elements from a target web page.
{context_block}
DOM Elements:
{dom_summary}

Based ONLY on the elements above, generate exactly 2 BDD Scenarios that test this page. 
One should be a "Happy Path" and one should be a "Negative Test" (e.g. testing validation with blank/invalid data).

Rules:
1. Return ONLY a valid JSON array of 2 scenario objects. No markdown formatting.
2. The JSON keys must be exactly: "title", "given", "when", "then", "scenario_type".
3. Use the exact field names (placeholder/id) from the DOM Elements. MUST strictly follow the Project Context rules if provided.
"""
        try:
            raw_response = self.generate(prompt, max_tokens=1500, temperature=0.3)
            
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith('```json'): cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'): cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'): cleaned_response = cleaned_response[:-3]
                
            import re
            json_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
            if json_match:
                cleaned_response = json_match.group(0)
            return json.loads(cleaned_response)
        except Exception as e:
            print(f"Discovery parsing failed: {e}\n{raw_response}")
            return [{
                "title": "Basic Discovery Fallback",
                "scenario_type": "Happy Path",
                "given": "user is on the page",
                "when": "user clicks the primary button",
                "then": "action completes"
            }]

llm_service = LLMService()
