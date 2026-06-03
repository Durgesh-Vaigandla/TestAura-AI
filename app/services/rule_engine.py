from typing import Dict, Any, List

class RuleEngine:
    @staticmethod
    def evaluate(req: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Determines which scenarios to generate based on requirement properties.
        Returns a list of scenario templates.
        """
        templates = []
        
        actor = req.get('actor', 'User')
        action = req.get('action', 'perform action')
        obj = req.get('object', 'the object')
        
        # Always generate Happy Path
        templates.append({
            "type": "Happy Path",
            "title": f"Successful {action} of {obj}",
            "given": f"the {actor} is on the appropriate page",
            "when": f"the {actor} attempts to {action} {obj} with valid data",
            "then": f"the system should successfully complete the {action} operation"
        })
        
        # Negative Path
        templates.append({
            "type": "Negative Path",
            "title": f"Failed {action} of {obj} due to invalid data",
            "given": f"the {actor} is on the appropriate page",
            "when": f"the {actor} attempts to {action} {obj} with invalid data",
            "then": f"the system should reject the operation and show an error"
        })
        
        # Validations
        if req.get("validations"):
            for val in req.get("validations"):
                templates.append({
                    "type": "Validation",
                    "title": f"Validation failure: {val}",
                    "given": f"the {actor} is attempting to {action} {obj}",
                    "when": f"the input violates the rule: {val}",
                    "then": f"the system should enforce the validation and block the action"
                })
                
        # RBAC
        if req.get("roles"):
            for role in req.get("roles"):
                templates.append({
                    "type": "RBAC",
                    "title": f"Access granted for role: {role}",
                    "given": f"a user is logged in with the {role} role",
                    "when": f"the user attempts to {action} {obj}",
                    "then": f"the system should allow the action"
                })
            templates.append({
                "type": "Security",
                "title": f"Access denied for unauthorized roles",
                "given": f"a user is logged in without required roles",
                "when": f"the user attempts to {action} {obj}",
                "then": f"the system should deny access and show an unauthorized error"
            })
            
        return templates

rule_engine = RuleEngine()
