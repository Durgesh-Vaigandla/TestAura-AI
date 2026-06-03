from app.models.domain import Document, Requirement, Scenario

class TraceabilityService:
    @staticmethod
    def get_document_traceability(document_id: int):
        doc = Document.query.get_or_404(document_id)
        
        trace = {
            "document": {"id": doc.id, "filename": doc.filename},
            "requirements": []
        }
        
        for req in doc.requirements:
            req_data = {
                "id": req.id,
                "req_id": req.req_id,
                "title": req.title,
                "health_score": req.health_score,
                "scenarios": []
            }
            for sc in req.scenarios:
                req_data["scenarios"].append({
                    "id": sc.id,
                    "title": sc.title,
                    "type": sc.scenario_type,
                    "status": sc.status
                })
            trace["requirements"].append(req_data)
            
        return trace

traceability_service = TraceabilityService()
