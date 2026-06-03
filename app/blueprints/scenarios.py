from flask import render_template, request, jsonify
from app.blueprints import scenarios_bp
from app.models.domain import Scenario, Requirement
from app import db

@scenarios_bp.route('/', methods=['GET'])
def index():
    req_id = request.args.get('req_id')
    if req_id:
        scenarios = Scenario.query.filter_by(requirement_id=req_id).all()
        req = Requirement.query.get(req_id)
    else:
        scenarios = Scenario.query.order_by(Scenario.id.desc()).limit(100).all()
        req = None
        
    return render_template('pages/scenarios.html', scenarios=scenarios, requirement=req)

@scenarios_bp.route('/<int:sc_id>/refine', methods=['POST'])
def refine_scenario(sc_id):
    from app.services.llm_service import llm_service
    sc = Scenario.query.get_or_404(sc_id)
    
    sc_dict = {
        "title": sc.title,
        "given": sc.given,
        "when": sc.when,
        "then": sc.then
    }
    
    refined_text = llm_service.refine_scenario_wording(sc_dict)
    
    sc.status = "Refined by AI"
    # To keep simple, we might just keep the refined text in the status or a new field, 
    # but for now we just return it to display in UI.
    db.session.commit()
    
    return jsonify({"status": "success", "refined_text": refined_text})
