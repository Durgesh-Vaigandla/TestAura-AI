from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class StepResult:
    step_index: int
    action: str
    target: str
    status: str # Passed, Failed, Skipped
    error_message: Optional[str] = None
    duration: float = 0.0

@dataclass
class ScenarioResult:
    scenario_id: int
    status: str # Passed, Failed
    duration: float = 0.0
    error_message: Optional[str] = None
    steps: List[StepResult] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)

@dataclass
class ExecutionResultPayload:
    execution_id: int
    status: str # Completed, Failed
    total_duration: float = 0.0
    scenario_results: List[ScenarioResult] = field(default_factory=list)
