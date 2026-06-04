from playwright.sync_api import sync_playwright

class WebScout:
    """
    Autonomous scout that navigates to a URL and extracts a semantic
    understanding of the UI (buttons, forms, inputs) for the AI to analyze.
    """
    @staticmethod
    def extract_dom_summary(url: str) -> str:
        summary = {"inputs": [], "buttons": [], "links": []}
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)
                page.wait_for_load_state("load", timeout=15000)
                
                # Execute JS to extract semantic elements
                js_script = """
                () => {
                    const inputs = Array.from(document.querySelectorAll('input, textarea')).map(el => {
                        return {
                            type: el.type || 'text',
                            id: el.id || '',
                            name: el.name || '',
                            placeholder: el.placeholder || '',
                            aria_label: el.getAttribute('aria-label') || ''
                        };
                    }).filter(i => i.type !== 'hidden');
                    
                    const buttons = Array.from(document.querySelectorAll('button, input[type="submit"]')).map(el => {
                        return {
                            text: el.innerText || el.value || '',
                            id: el.id || '',
                            type: el.type || 'button'
                        };
                    });
                    
                    return { inputs, buttons };
                }
                """
                dom_data = page.evaluate(js_script)
                browser.close()
                
                import json
                return json.dumps(dom_data, indent=2)
                
        except Exception as e:
            print(f"Scout Error: {e}")
            return "{\"error\": \"Failed to extract DOM. Ensure the URL is reachable.\"}"

scout = WebScout()
