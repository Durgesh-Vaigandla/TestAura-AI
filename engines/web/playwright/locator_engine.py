class LocatorEngine:
    """
    Intelligent element targeting based on strict priority.
    In a fully advanced version, this would check the page DOM to see which locator exists.
    For now, it acts as a heuristic generator that Playwright tries.
    Priority: data-testid > id > name > role > label > placeholder > text
    """
    
    def resolve(self, semantic_target: str) -> str:
        """
        Converts a semantic string like "login_button" or "username" into a CSS/Playwright locator.
        """
        # Clean the target
        target = semantic_target.lower().replace(" ", "_")
        
        # A simple heuristic fallback chain for Playwright's locator generator.
        # Playwright supports "id=", "data-testid=", "text=", etc.
        # We will return a composite CSS selector or text selector that covers common patterns.
        
        # In a real DOM-aware version, we would inject a JS script to find the best match.
        # For our offline test engine, we'll build a smart heuristic selector:
        
        # Semantic bridging for common enterprise forms
        synonyms = {
            "username": ["username", "email", "login", "user", "userid"],
            "password": ["password", "pass", "pwd"],
            "login_button": ["login", "sign in", "submit", "continue", "log in"],
            "submit": ["submit", "save", "continue", "next", "confirm"]
        }
        
        # Check if the target is a known semantic concept
        search_terms = [target]
        for key, syn_list in synonyms.items():
            if key in target or target in key:
                search_terms.extend(syn_list)
        search_terms = list(set(search_terms)) # deduplicate
        
        selectors = []
        for term in search_terms:
            clean_term = term.replace("_", " ")
            # CSS standard fallbacks
            selectors.append(f"[data-testid*='{term}' i]")
            selectors.append(f"[id*='{term}' i]")
            selectors.append(f"[name*='{term}' i]")
            
            # Smart inputs
            if any(k in target for k in ["input", "field", "username", "password", "email"]):
                selectors.append(f"input[placeholder*='{clean_term}' i]")
                selectors.append(f"input[aria-label*='{clean_term}' i]")
                selectors.append(f"input[type='{term}']")
                
            # Smart buttons
            if any(k in target for k in ["button", "submit", "login", "click"]):
                selectors.append(f"button:has-text('{clean_term}')")
                selectors.append(f"a:has-text('{clean_term}')")
                selectors.append(f"input[type='submit'][value*='{clean_term}' i]")
                
            # Ultimate fallback
            selectors.append(f"text='{clean_term}'")
            
        return ", ".join(selectors)
