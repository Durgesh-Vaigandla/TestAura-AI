import time
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

from engines.core.execution_contract import ExecutionEngine
from engines.core.execution_context import ExecutionContext
from engines.core.execution_result import ExecutionResultPayload, ScenarioResult, StepResult
from engines.web.playwright.locator_engine import LocatorEngine
from engines.web.playwright.action_mapper import ActionMapper

class PlaywrightRunner(ExecutionEngine):
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def _setup_browser(self, exec_context: ExecutionContext):
        if not self.playwright:
            self.playwright = sync_playwright().start()
            
        if not self.browser:
            self.browser = self.playwright.chromium.launch(
                headless=exec_context.is_headless,
                slow_mo=500 if exec_context.mode.value == "Debug" else 0
            )
            
        if not self.context:
            self.context = self.browser.new_context(
                record_video_dir=exec_context.artifacts_dir if exec_context.capture_video else None
            )
            self.page = self.context.new_page()

    def run(self, scenarios: List[Dict[str, Any]], exec_context: ExecutionContext) -> ExecutionResultPayload:
        self._setup_browser(exec_context)
        
        locator_engine = LocatorEngine()
        action_mapper = ActionMapper(self.page, locator_engine)
        
        payload = ExecutionResultPayload(
            execution_id=exec_context.execution_id,
            status="Completed"
        )
        
        start_time_total = time.time()
        
        for scenario in scenarios:
            scen_res = ScenarioResult(scenario_id=scenario.get('id', 0), status="Passed")
            scen_start = time.time()
            
            steps = scenario.get('steps', [])
            for i, step in enumerate(steps):
                step_res = StepResult(
                    step_index=i,
                    action=step.get('action', ''),
                    target=step.get('target', ''),
                    status="Passed"
                )
                step_start = time.time()
                
                try:
                    action_mapper.execute_step(step)
                except Exception as e:
                    step_res.status = "Failed"
                    step_res.error_message = str(e)
                    scen_res.status = "Failed"
                    
                    if exec_context.capture_screenshots:
                        screenshot_path = f"{exec_context.artifacts_dir}/fail_scen_{scenario.get('id')}_step_{i}.png"
                        self.page.screenshot(path=screenshot_path)
                        scen_res.screenshots.append(screenshot_path)
                        
                    step_res.duration = time.time() - step_start
                    scen_res.steps.append(step_res)
                    break # Stop scenario on first failure
                
                step_res.duration = time.time() - step_start
                scen_res.steps.append(step_res)
                
            scen_res.duration = time.time() - scen_start
            payload.scenario_results.append(scen_res)
            
        payload.total_duration = time.time() - start_time_total
        return payload

    def cleanup(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
