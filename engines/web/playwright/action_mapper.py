from playwright.sync_api import Page
import time

class ActionMapper:
    """
    Deterministically maps JSON Intent Actions to Playwright execution.
    """
    def __init__(self, page: Page, locator_engine):
        self.page = page
        self.locator_engine = locator_engine

    def execute_step(self, step: dict):
        action = step.get('action')
        target = step.get('target')
        field = step.get('field')
        value = step.get('value', 'TestValue123') # Default generic test value if none provided

        if action == "navigate":
            self.page.goto(target)
            self.page.wait_for_load_state("load")
            
        elif action == "click":
            locator = self.locator_engine.resolve(target)
            if locator:
                self.page.locator(locator).click()
            else:
                raise Exception(f"Locator engine failed to resolve target: {target}")
                
        elif action == "fill":
            locator = self.locator_engine.resolve(field)
            if locator:
                self.page.locator(locator).fill(value)
            else:
                raise Exception(f"Locator engine failed to resolve field: {field}")
                
        elif action == "assert_visible":
            locator = self.locator_engine.resolve(target)
            if locator:
                self.page.locator(locator).wait_for(state="visible", timeout=5000)
            else:
                raise Exception(f"Locator engine failed to resolve target for assertion: {target}")
                
        else:
            raise NotImplementedError(f"Action '{action}' is not supported yet.")
