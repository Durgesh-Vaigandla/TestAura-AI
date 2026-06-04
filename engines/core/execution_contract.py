from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ExecutionEngine(ABC):
    """
    Base contract that all Execution Engines (Playwright, Appium, API) must implement.
    """
    
    @abstractmethod
    def run(self, scenarios: List[Dict[str, Any]], context: 'ExecutionContext') -> 'ExecutionResult':
        """
        Executes a list of scenarios against a target context.
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Releases any locked resources (e.g. Browser context, Appium session).
        """
        pass
