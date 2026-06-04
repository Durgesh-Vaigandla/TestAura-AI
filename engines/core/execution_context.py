from dataclasses import dataclass
from enum import Enum

class ExecutionMode(Enum):
    FAST = "Fast"
    DEBUG = "Debug"
    EVIDENCE = "Evidence"

@dataclass
class ExecutionContext:
    execution_id: int
    target_url: str
    mode: ExecutionMode
    engine_name: str
    artifacts_dir: str
    
    @property
    def is_headless(self) -> bool:
        return self.mode in [ExecutionMode.FAST, ExecutionMode.EVIDENCE]
    
    @property
    def capture_video(self) -> bool:
        return self.mode == ExecutionMode.EVIDENCE
        
    @property
    def capture_screenshots(self) -> bool:
        return self.mode == ExecutionMode.EVIDENCE
