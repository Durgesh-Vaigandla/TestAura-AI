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

llm_service = LLMService()
