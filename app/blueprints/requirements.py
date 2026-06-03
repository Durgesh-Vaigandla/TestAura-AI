from flask import render_template, request, jsonify, current_app, redirect, url_for
from app.blueprints import requirements_bp
from app.models.domain import Requirement, Document, Scenario
from app import db

@requirements_bp.route('/', methods=['GET'])
def index():
    doc_id = request.args.get('doc_id')
    
    if doc_id:
        reqs = Requirement.query.filter_by(document_id=doc_id).order_by(Requirement.id).all()
        doc = Document.query.get(doc_id)
    else:
        reqs = Requirement.query.order_by(Requirement.id.desc()).limit(100).all()
        doc = None
        
    return render_template('pages/requirements.html', requirements=reqs, document=doc)

@requirements_bp.route('/<int:req_id>/generate', methods=['POST'])
def generate_scenarios(req_id):
    from app.services.scenario_builder import scenario_builder
    from app.models.domain import Scenario
    
    req = Requirement.query.get_or_404(req_id)
    
    # Check if already generated to prevent duplicates
    if len(req.scenarios) > 0:
        return jsonify({"status": "already_generated"})
        
    req_data = {
        "actor": req.actor,
        "action": req.action,
        "object": req.object,
        "validations": req.validations,
        "roles": req.roles
    }
    
    scenario_dicts = scenario_builder.build_from_requirement(req_data)
    
    for s_dict in scenario_dicts:
        sc = Scenario(
            requirement_id=req.id,
            title=s_dict["title"],
            scenario_type=s_dict["scenario_type"],
            given=s_dict["given"],
            when=s_dict["when"],
            then=s_dict["then"]
        )
        db.session.add(sc)
        
    db.session.commit()
    return f'''
    <div class="pt-4 mt-4 border-t border-gray-100">
        <p class="text-xs text-center mt-2 text-green-600 font-medium">{len(scenario_dicts)} Scenarios Generated Successfully!</p>
        <div class="mt-2 text-center">
            <a href="/scenarios?req_id={req.id}" class="text-xs text-blue-600 hover:underline">View Scenarios →</a>
        </div>
    </div>
    '''

@requirements_bp.route('/bulk-generate', methods=['POST'])
def generate_bulk():
    from app.services.task_manager import task_manager
    
    req_ids = request.form.getlist('req_ids')
    if not req_ids:
        return jsonify({"status": "error", "message": "No requirements selected"})
        
    # Insert placeholders for UI feedback
    for req_id in req_ids:
        # Clear any existing scenarios for this requirement to prevent duplicates
        Scenario.query.filter_by(requirement_id=req_id).delete()
        
        placeholder = Scenario(
            requirement_id=req_id,
            title="AI generating scenarios in background...",
            scenario_type="Pending",
            status="Generating"
        )
        db.session.add(placeholder)
    db.session.commit()
    
    app_obj = current_app._get_current_object()
    
    def process_scenarios(ids):
        with app_obj.app_context():
            from app.services.scenario_builder import scenario_builder
            for r_id in ids:
                req = Requirement.query.get(r_id)
                if not req: continue
                
                req_data = {
                    "title": req.title,
                    "description": req.description,
                    "actor": req.actor,
                    "action": req.action,
                    "roles": req.roles,
                    "security_rules": req.security_rules,
                    "integration_points": req.integration_points
                }
                
                scenario_dicts = scenario_builder.build_from_requirement(req_data)
                
                # Delete placeholder
                Scenario.query.filter_by(requirement_id=r_id, status="Generating").delete()
                
                # Insert actuals
                for sd in scenario_dicts:
                    sc = Scenario(
                        requirement_id=req.id,
                        title=sd.get('title', 'Generated Scenario'),
                        scenario_type=sd.get('scenario_type', 'Happy Path'),
                        given=sd.get('given', ''),
                        when=sd.get('when', ''),
                        then=sd.get('then', ''),
                        status='Generated'
                    )
                    db.session.add(sc)
                    
                db.session.commit()
                
    task_manager.submit_task(process_scenarios, req_ids)
    
    return redirect(url_for('scenarios.index'))
