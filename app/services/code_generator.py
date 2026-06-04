import os
import re
from app.services.llm_service import llm_service
from app.utils.file_system import ensure_test_folder_ignored

class CodeGenerator:
    def generate_playwright_spec(self, project, scenario) -> str:
        """
        Generates Playwright TypeScript code using the LLM and writes it to the target project.
        Returns the absolute path of the generated file.
        """
        if not project.target_directory:
            raise ValueError("Project target_directory is not set. Please configure it in Project Settings.")
            
        test_dir = os.path.join(project.target_directory, project.test_folder)
        os.makedirs(test_dir, exist_ok=True)
        ensure_test_folder_ignored(project.target_directory, project.test_folder)
        
        # Craft the generation prompt
        context_block = f"\nPROJECT RULES:\n{project.global_context}\n" if project.global_context else ""
        
        prompt = f"""
You are an expert Playwright Automation Engineer writing an Enterprise-grade TypeScript test.
{context_block}

SCENARIO TO AUTOMATE:
Title: {scenario.title}
Given {scenario.given}
When {scenario.when}
Then {scenario.then}

Task: Write a complete Playwright test file (.spec.ts) for this scenario.
Rules:
1. Output ONLY valid TypeScript code wrapped in a ```typescript code block.
2. Use standard Playwright structure: `import {{ test, expect }} from '@playwright/test';`
3. Include comments explaining the steps.
4. Strictly adhere to the PROJECT RULES provided above (e.g. roles, tabs, element IDs).
"""

        raw_response = llm_service.generate(prompt, max_tokens=1500, temperature=0.2)
        
        # Extract code from markdown block
        code = self._extract_typescript(raw_response)
        if not code:
            code = raw_response # Fallback
            
        # Write file
        filename = re.sub(r'[^a-zA-Z0-9_-]', '_', scenario.title).lower() + '.spec.ts'
        filepath = os.path.join(test_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(code)
            
        return filepath
        
    def _extract_typescript(self, text: str) -> str:
        import re
        match = re.search(r'```(?:typescript|ts)\n(.*?)\n```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r'```\n(.*?)\n```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

code_generator = CodeGenerator()
