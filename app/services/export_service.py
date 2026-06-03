import csv
import io
import pandas as pd
from typing import List
from app.models.domain import Requirement, Scenario, Document

class ExportService:
    @staticmethod
    def export_to_feature_file(document_id: int) -> str:
        reqs = Requirement.query.filter_by(document_id=document_id).all()
        doc = Document.query.get(document_id)
        
        lines = []
        lines.append(f"Feature: Scenarios for {doc.filename if doc else 'Document'}\n")
        
        for req in reqs:
            if not req.scenarios:
                continue
                
            lines.append(f"  # Requirement: {req.req_id} - {req.title}")
            
            for sc in req.scenarios:
                lines.append(f"  Scenario: {sc.title}")
                if sc.given:
                    lines.append(f"    Given {sc.given}")
                if sc.when:
                    lines.append(f"    When {sc.when}")
                if sc.then:
                    lines.append(f"    Then {sc.then}")
                lines.append("")
                
        return "\n".join(lines)
        
    @staticmethod
    def export_to_csv(document_id: int) -> str:
        reqs = Requirement.query.filter_by(document_id=document_id).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Req ID", "Requirement Title", "Scenario Title", "Type", "Given", "When", "Then"])
        
        for req in reqs:
            for sc in req.scenarios:
                writer.writerow([
                    req.req_id,
                    req.title,
                    sc.title,
                    sc.scenario_type,
                    sc.given,
                    sc.when,
                    sc.then
                ])
                
        return output.getvalue()
        
    @staticmethod
    def export_to_excel(document_id: int, filepath: str):
        reqs = Requirement.query.filter_by(document_id=document_id).all()
        
        data = []
        for req in reqs:
            for sc in req.scenarios:
                data.append({
                    "Req ID": req.req_id,
                    "Requirement Title": req.title,
                    "Requirement Health": req.health_score,
                    "Scenario Title": sc.title,
                    "Type": sc.scenario_type,
                    "Given": sc.given,
                    "When": sc.when,
                    "Then": sc.then,
                    "Status": sc.status
                })
                
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False)

export_service = ExportService()
