from app.models.domain import Requirement, Scenario

class CoverageService:
    @staticmethod
    def get_coverage_metrics(document_id: int):
        reqs = Requirement.query.filter_by(document_id=document_id).all()
        total_reqs = len(reqs)
        
        if total_reqs == 0:
            return {"total_requirements": 0, "coverage_percent": 0}
            
        covered_reqs = 0
        total_scenarios = 0
        missing_validations = 0
        missing_negatives = 0
        
        for req in reqs:
            scenarios = req.scenarios
            total_scenarios += len(scenarios)
            if len(scenarios) > 0:
                covered_reqs += 1
                
            has_val_scenario = any(s.scenario_type == "Validation" for s in scenarios)
            has_neg_scenario = any(s.scenario_type == "Negative Test" for s in scenarios)
            
            if req.validations and not has_val_scenario:
                missing_validations += 1
            
            if not has_neg_scenario:
                missing_negatives += 1
                
        coverage_percent = (covered_reqs / total_reqs) * 100 if total_reqs > 0 else 0
        
        # Scenario Type Breakdown
        scenario_types = {}
        for req in reqs:
            for s in req.scenarios:
                if s.status != 'Generating':
                    scenario_types[s.scenario_type] = scenario_types.get(s.scenario_type, 0) + 1
                    
        from app.models.domain import ExecutionResult, Execution
        # Per-Requirement Coverage Details
        requirement_stats = []
        for req in reqs:
            sc_count = len([s for s in req.scenarios if s.status != 'Generating'])
            
            # Calculate Execution Stats
            scenario_ids = [s.id for s in req.scenarios]
            exec_results = ExecutionResult.query.filter(ExecutionResult.scenario_id.in_(scenario_ids)).all()
            
            total_execs = len(exec_results)
            passed_execs = len([r for r in exec_results if r.status == 'Passed'])
            pass_rate = (passed_execs / total_execs * 100) if total_execs > 0 else 0
            
            last_exec = Execution.query.join(ExecutionResult).filter(ExecutionResult.scenario_id.in_(scenario_ids)).order_by(Execution.created_at.desc()).first()
            last_exec_time = last_exec.created_at.strftime('%Y-%m-%d %H:%M:%S') if last_exec else "Not executed"
            
            requirement_stats.append({
                "req_id": req.req_id,
                "title": req.title,
                "scenario_count": sc_count,
                "covered": sc_count > 0,
                "missing_validations": req.validations and not any(s.scenario_type == "Validation" for s in req.scenarios),
                "missing_negatives": not any(s.scenario_type == "Negative Test" for s in req.scenarios),
                "pass_rate": round(pass_rate, 1),
                "total_execs": total_execs,
                "last_exec_time": last_exec_time
            })
        
        return {
            "total_requirements": total_reqs,
            "covered_requirements": covered_reqs,
            "uncovered_requirements": total_reqs - covered_reqs,
            "coverage_percent": round(coverage_percent, 2),
            "total_scenarios": total_scenarios,
            "missing_validations": missing_validations,
            "missing_negatives": missing_negatives,
            "scenario_types": scenario_types,
            "requirement_stats": requirement_stats
        }

coverage_service = CoverageService()
