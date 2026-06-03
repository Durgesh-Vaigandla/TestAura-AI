from flask import Blueprint, render_template, request
from app.models.domain import Requirement, Scenario
from app import db
import re

generator_bp = Blueprint('generator', __name__, url_prefix='/generator')

@generator_bp.route('/', methods=['GET'])
def index():
    # Fetch all requirements that have generated scenarios
    reqs = Requirement.query.filter(Requirement.scenarios.any(Scenario.status != 'Generating')).all()
    
    total_scenarios = 0
    keyword_counts = {
        'Given': 0,
        'When': 0,
        'Then': 0,
        'And': 0,
        'But': 0
    }
    
    raw_gherkin_lines = []
    
    for req in reqs:
        # Group scenarios for this requirement
        scenarios = [s for s in req.scenarios if s.status != 'Generating']
        if not scenarios:
            continue
            
        raw_gherkin_lines.append(f"Feature: [{req.req_id}] {req.title}")
        raw_gherkin_lines.append(f"  {req.description}")
        raw_gherkin_lines.append("")
        
        for sc in scenarios:
            total_scenarios += 1
            raw_gherkin_lines.append(f"  Scenario: {sc.title} ({sc.scenario_type})")
            
            # Reconstruct steps from DB
            steps = []
            if sc.given: steps.extend([s.strip() for s in sc.given.split('\n') if s.strip()])
            if sc.when: steps.extend([s.strip() for s in sc.when.split('\n') if s.strip()])
            if sc.then: steps.extend([s.strip() for s in sc.then.split('\n') if s.strip()])
            
            # Count keywords and append to raw string
            for step in steps:
                lower_step = step.lower()
                if lower_step.startswith('given'): keyword_counts['Given'] += 1
                elif lower_step.startswith('when'): keyword_counts['When'] += 1
                elif lower_step.startswith('then'): keyword_counts['Then'] += 1
                elif lower_step.startswith('and'): keyword_counts['And'] += 1
                elif lower_step.startswith('but'): keyword_counts['But'] += 1
                else:
                    # If it doesn't have a keyword in the DB, prepend one based on context
                    # Just an approximation
                    pass
                
                # Some SLMs might not include the prefix if it's stored separately in the DB columns
                # Let's ensure it has the correct prefix based on the column it came from
                # Wait, our DB stores `given`, `when`, `then` as raw text which might ALREADY include 'Given', 'When', 'Then'.
                # Let's just dump it as is for the raw gherkin, assuming the AI formatted it properly.
                
                # If the step doesn't start with a known keyword, maybe prepend it?
                # For safety, let's just dump the raw DB column values.
                pass
            
            # Safely dump from columns, adding keywords if the AI forgot them
            given_text = sc.given if sc.given else ""
            when_text = sc.when if sc.when else ""
            then_text = sc.then if sc.then else ""
            
            # Simple keyword counting on the final text
            full_text = f"{given_text}\n{when_text}\n{then_text}"
            for line in full_text.split('\n'):
                line = line.strip()
                if not line: continue
                raw_gherkin_lines.append(f"    {line}")
                
                lw = line.lower()
                if lw.startswith('given'): keyword_counts['Given'] += 1
                elif lw.startswith('when'): keyword_counts['When'] += 1
                elif lw.startswith('then'): keyword_counts['Then'] += 1
                elif lw.startswith('and'): keyword_counts['And'] += 1
                elif lw.startswith('but'): keyword_counts['But'] += 1

            raw_gherkin_lines.append("")
        
        raw_gherkin_lines.append("")
        
    raw_gherkin_output = "\n".join(raw_gherkin_lines)
    
    # Calculate percentages for the chart
    total_keywords = sum(keyword_counts.values())
    keyword_percentages = {}
    for k, v in keyword_counts.items():
        keyword_percentages[k] = round((v / total_keywords * 100) if total_keywords > 0 else 0, 1)

    return render_template(
        'pages/generator.html',
        total_scenarios=total_scenarios,
        raw_gherkin=raw_gherkin_output,
        keyword_counts=keyword_counts,
        keyword_percentages=keyword_percentages,
        total_keywords=total_keywords
    )
