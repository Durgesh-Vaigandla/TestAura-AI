import re
from typing import List, Dict, Any

class EnterpriseRequirementExtractor:
    def __init__(self):
        # Match standard requirement identifiers specifically to avoid Appendix tags
        self.req_id_pattern = re.compile(r'\b(SYR|URS|REQ|FR|NFR|US|CORE|SYS|SW|[A-Z]{2,4}REQ)-\d{1,5}\b', re.IGNORECASE)
        self.shall_pattern = re.compile(r'\b(shall|must|should|will|can|could|needs to|has to|requires|is required|allow|ensures)\b', re.IGNORECASE)

        self.CATEGORIES = {
            "Security": ["encrypt", "hash", "cipher", "security", "attack", "vulnerability", "tls", "ssl"],
            "Authentication": ["login", "authenticate", "password", "session", "mfa", "token", "sso", "credentials"],
            "RBAC": ["role", "permission", "access", "authorize", "admin", "privilege", "authorized users"],
            "Integration": ["api", "webhook", "endpoint", "rest", "soap", "third-party", "external system", "export", "import"],
            "Compliance": ["gdpr", "hipaa", "pci", "compliance", "regulation", "law", "audit", "standard", "iso"],
            "Localization": ["language", "locale", "translate", "timezone", "currency", "i18n", "en-us"],
            "Performance": ["fast", "latency", "throughput", "response time", "concurrent", "scalable", "ms", "seconds", "cpu usage", "memory usage"],
            "Availability": ["uptime", "failover", "redundancy", "disaster recovery", "backup", "99.9%", "restart", "status"],
            "Auditing": ["log", "audit trail", "track", "history", "record", "timestamp", "metrics"],
            "Validation": ["validate", "invalid", "format", "mandatory", "required field", "regex"],
            "User Interface": ["screen", "button", "click", "display", "render", "ui", "ux", "responsive", "view"]
        }

        self.AMBIGUOUS_WORDS = ["fast", "sometimes", "efficiently", "robust", "user-friendly", "as needed", "if possible", "quick", "seamless", "easy"]
        self.SPECIFIC_WORDS = ["seconds", "ms", "bytes", "mb", "gb", "aes", "sha", "tcp", "http", "exactly", "percent", "key-value", "time series"]

    def extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        requirements = []
        lines = text.split('\n')
        
        current_req = None
        req_counter = 1
        
        for line in lines:
            line = line.strip()
            if not line: continue
                
            # Extract section context injected by document_parser
            section = "General"
            section_match = re.search(r'^\[SECTION:\s*(.*?)\]', line)
            if section_match:
                section = section_match.group(1).strip()
                line = line.replace(section_match.group(0), '').strip()
                
            # Skip obvious appendix
            if re.match(r'^(?:\d+\s+)?Appendix', line, re.IGNORECASE):
                continue
                
            req_id_match = self.req_id_pattern.search(line)
            has_keyword = self.shall_pattern.search(line)
            
            is_generic_req = len(line) > 40 and line[0].isdigit() and ('.' in line[:5] or ')' in line[:5])
            
            if req_id_match or has_keyword or is_generic_req:
                if current_req:
                    self._finalize_req(current_req)
                    requirements.append(current_req)
                
                req_id = req_id_match.group(0) if req_id_match else f"GEN-{req_counter:03d}"
                if not req_id_match: req_counter += 1
                
                description = line
                title = line
                parent_reqs = []
                req_type_override = None
                
                # Intelligent Table Parsing
                if '|' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    
                    if req_id_match and len(parts) > 1:
                        # Attempt to find the description (longest part)
                        desc_part = parts[1] if len(parts[1]) > 15 else max(parts, key=len)
                        description = desc_part
                        title = description
                        
                        # Attempt to find parent requirements in other columns
                        for p in parts:
                            parents = self.req_id_pattern.findall(p)
                            for pr in parents:
                                if pr != req_id and pr not in parent_reqs:
                                    parent_reqs.append(pr)
                                    
                        # Attempt to find type like "Core" or "Normal"
                        for p in parts:
                            if p.lower() in ['core', 'normal', 'critical', 'optional']:
                                req_type_override = p.capitalize()
                
                if len(title) > 100:
                    title = title[:97] + "..."
                
                current_req = {
                    "req_id": req_id.upper(),
                    "title": title,
                    "description": description,
                    "source_section": section,
                    "source_subsection": "",
                    "page_number": "",
                    "parent_reqs": parent_reqs,
                    "req_type": req_type_override,
                    "actor": "",
                    "action": "",
                    "object": "",
                    "constraints": [],
                    "roles": [],
                    "validations": [],
                    "business_rules": [],
                    "security_rules": [],
                    "compliance_rules": [],
                    "dependencies": [],
                    "integration_points": [],
                    "risk_indicators": [],
                    "smart_tags": [],
                    "health_metrics": {},
                    "priority": "Medium",
                    "section": section
                }
                
                # Perform NLP extraction
                self._extract_entities(current_req)
                
            elif current_req and len(line) > 10:
                append_text = line.replace(' | ', ' ')
                current_req["description"] += f" {append_text}"
                
        if current_req:
            self._finalize_req(current_req)
            requirements.append(current_req)
            
        return requirements
        
    def _extract_entities(self, req: Dict[str, Any]):
        desc = req["description"]
        lower_desc = desc.lower()
        
        # Actor Extraction
        actor_match = re.search(r'([A-Za-z0-9\s]+)\s+(?:shall|must|should|will|can|needs to)', desc, re.IGNORECASE)
        if actor_match:
            actor = actor_match.group(1).strip()
            words = actor.split()
            req["actor"] = " ".join(words[-3:]) if len(words) > 3 else actor
        else:
            req["actor"] = "System"
            
        # Action Extraction
        action_match = re.search(r'(?:shall|must|should|will|can|needs to)\s+([A-Za-z\s]+)', desc, re.IGNORECASE)
        if action_match:
            req["action"] = action_match.group(1).strip().split(' ')[0]
            
        # Object Extraction
        obj_match = re.search(r'(?:shall|must|should|will|can|needs to)\s+[A-Za-z]+\s+(.*)', desc, re.IGNORECASE)
        if obj_match:
            obj = obj_match.group(1).strip()
            req["object"] = obj.split('.')[0][:50] if '.' in obj else obj[:50]
            
        # Classify Type
        if not req["req_type"]:
            matched_categories = []
            for category, keywords in self.CATEGORIES.items():
                if any(kw in lower_desc for kw in keywords):
                    matched_categories.append(category)
            req["req_type"] = matched_categories[0] if matched_categories else "Functional"
            
        # Smart Tags & Specific Rules
        for kw in self.CATEGORIES["Security"]:
            if kw in lower_desc: req["security_rules"].append(f"Requires secure implementation involving: {kw}")
        for kw in self.CATEGORIES["Integration"]:
            if kw in lower_desc: req["integration_points"].append(f"External integration identified: {kw}")
        for kw in self.CATEGORIES["RBAC"]:
            if kw in lower_desc: req["roles"].append("Authorized Role Required")
            
        if "timeout" in lower_desc or "expire" in lower_desc:
            req["constraints"].append("Time-based constraint detected")
        if "format" in lower_desc or "validate" in lower_desc:
            req["validations"].append("Strict formatting validation required")
            
        req["smart_tags"] = list(set([kw for cat in self.CATEGORIES.values() for kw in cat if kw in lower_desc]))

    def _finalize_req(self, req: Dict[str, Any]):
        desc = req["description"].strip()
        req["description"] = desc
        
        # Calculate Health Score
        clarity_score = 100
        ambiguity_penalties = 0
        specific_bonuses = 0
        
        lower_desc = desc.lower()
        for word in self.AMBIGUOUS_WORDS:
            if word in lower_desc: ambiguity_penalties += 15
        for word in self.SPECIFIC_WORDS:
            if word in lower_desc: specific_bonuses += 10
            
        length_penalty = 0
        if len(desc) > 300: length_penalty = 10 # Too long, might be complex
        if len(desc) < 30: length_penalty = 20 # Too short, incomplete
        
        final_score = min(100, max(0, clarity_score - ambiguity_penalties + specific_bonuses - length_penalty))
        
        req["health_score"] = final_score
        req["health_metrics"] = {
            "clarity": 100 - ambiguity_penalties,
            "completeness": 100 - length_penalty,
            "testability": min(100, 70 + specific_bonuses - ambiguity_penalties),
            "ambiguous_terms_found": ambiguity_penalties // 15
        }
        
        # Determine priority
        if any(w in lower_desc for w in ['must', 'critical', 'essential', 'core']):
            req["priority"] = "High"
        elif any(w in lower_desc for w in ['should', 'recommended', 'normal']):
            req["priority"] = "Medium"
        else:
            req["priority"] = "Low"

requirement_extractor = EnterpriseRequirementExtractor()
