from flask import Blueprint, render_template, request, jsonify, redirect
from app.models.domain import Document, Requirement, Scenario
from app import db
from app.services.llm_service import llm_service

quick_test_bp = Blueprint('quick_test', __name__, url_prefix='/quick-test')

def get_or_create_adhoc_workspace():
    # Hidden workspace document
    doc = Document.query.filter_by(filename='_adhoc_workspace.txt').first()
    if not doc:
        doc = Document(
            filename='_adhoc_workspace.txt',
            original_name='Ad-Hoc Workspace (Hidden)',
            file_path='/dev/null',
            status='Completed'
        )
        db.session.add(doc)
        db.session.commit()
    return doc

@quick_test_bp.route('/')
def quick_test_page():
    return render_template('pages/quick_test.html')

@quick_test_bp.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt_text = data.get('prompt')
    
    if not prompt_text:
        return jsonify({'error': 'Prompt is required'}), 400
        
    doc = get_or_create_adhoc_workspace()
    
    # Create a wrapper requirement for these scenarios
    req = Requirement(
        document_id=doc.id,
        req_id=f"ADHOC-{len(doc.requirements) + 1}",
        title=prompt_text[:50] + "..." if len(prompt_text) > 50 else prompt_text,
        description=prompt_text,
        req_type="Ad-Hoc Script"
    )
    db.session.add(req)
    db.session.commit()
    
    # Ask LLM to generate scenarios based on the prompt
    from flask import g
    project_context = g.current_project.global_context if g.current_project else ""
    generated_scenarios = llm_service.generate_adhoc_scenarios(prompt_text, project_context)
    
    scenario_ids = []
    for sc_data in generated_scenarios:
        scenario = Scenario(
            requirement_id=req.id,
            title=sc_data.get('title', 'Ad-Hoc Test'),
            given=sc_data.get('given', ''),
            when=sc_data.get('when', ''),
            then=sc_data.get('then', ''),
            scenario_type=sc_data.get('scenario_type', 'Happy Path'),
            status='Approved'
        )
        db.session.add(scenario)
        db.session.commit()
        scenario_ids.append(scenario.id)
        
    # Return the IDs so the frontend can immediately trigger execution
    return jsonify({
        'success': True,
        'scenario_ids': scenario_ids,
        'scenarios': generated_scenarios
    })

@quick_test_bp.route('/discover', methods=['POST'])
def discover():
    data = request.json
    target_url = data.get('target_url')
    
    if not target_url:
        return jsonify({'error': 'Target URL is required'}), 400
        
    # 1. Run Scout
    from engines.web.playwright.scout import scout
    dom_summary = scout.extract_dom_summary(target_url)
    if "error" in dom_summary.lower() and "failed" in dom_summary.lower():
        return jsonify({'error': 'Could not extract DOM from target URL. Ensure the dev server is running.'}), 500
        
    # 2. Generate Scenarios
    from flask import g
    project_context = g.current_project.global_context if g.current_project else ""
    generated_scenarios = llm_service.generate_discovery_scenarios(dom_summary, project_context)
    
    doc = get_or_create_adhoc_workspace()
    req = Requirement(
        document_id=doc.id,
        req_id=f"DISCOVER-{len(doc.requirements) + 1}",
        title=f"Auto-Discovery for {target_url}",
        description=f"Generated via Autonomous Scout against {target_url}",
        req_type="Auto-Discovery"
    )
    db.session.add(req)
    db.session.commit()
    
    scenario_ids = []
    for sc_data in generated_scenarios:
        scenario = Scenario(
            requirement_id=req.id,
            title=sc_data.get('title', 'Discovery Test'),
            given=sc_data.get('given', ''),
            when=sc_data.get('when', ''),
            then=sc_data.get('then', ''),
            scenario_type=sc_data.get('scenario_type', 'Discovery'),
            status='Approved'
        )
        db.session.add(scenario)
        db.session.commit()
        scenario_ids.append(scenario.id)
        
    return jsonify({
        'success': True,
        'scenario_ids': scenario_ids,
        'scenarios': generated_scenarios
    })
