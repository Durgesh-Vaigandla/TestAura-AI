import os
from datetime import datetime

class ArtifactManager:
    """
    Manages the storage and retrieval of execution artifacts (Screenshots, Videos, Logs).
    """
    def __init__(self, base_dir="data/artifacts"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def create_execution_dir(self, execution_id: int) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exec_dir = os.path.join(self.base_dir, f"exec_{execution_id}_{timestamp}")
        if not os.path.exists(exec_dir):
            os.makedirs(exec_dir)
        return exec_dir
