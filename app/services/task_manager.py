from concurrent.futures import ThreadPoolExecutor
import threading
import uuid
from typing import Callable, Dict, Any

class TaskManager:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        
        with self.lock:
            self.tasks[task_id] = {
                'status': 'PENDING',
                'result': None,
                'error': None
            }
            
        future = self.executor.submit(self._run_task, task_id, func, *args, **kwargs)
        return task_id

    def _run_task(self, task_id: str, func: Callable, *args, **kwargs):
        with self.lock:
            self.tasks[task_id]['status'] = 'RUNNING'
            
        try:
            result = func(*args, **kwargs)
            with self.lock:
                self.tasks[task_id]['status'] = 'COMPLETED'
                self.tasks[task_id]['result'] = result
        except Exception as e:
            with self.lock:
                self.tasks[task_id]['status'] = 'FAILED'
                self.tasks[task_id]['error'] = str(e)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        with self.lock:
            return self.tasks.get(task_id, {'status': 'NOT_FOUND'})

# Global instance for the application
task_manager = TaskManager()
