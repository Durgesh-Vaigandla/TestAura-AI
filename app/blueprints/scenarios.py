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
        from app.models.domain import Document
        scenarios = Scenario.query.join(Requirement).join(Document).filter(Document.filename != '_adhoc_workspace.txt').order_by(Scenario.id.desc()).limit(100).all()
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

@scenarios_bp.route('/<int:sc_id>/generate-code', methods=['POST'])
def generate_code(sc_id):
    from flask import g
    from app.services.code_generator import code_generator
    
    if not g.current_project:
        return jsonify({"error": "No project selected."}), 400
        
    sc = Scenario.query.get_or_404(sc_id)
    try:
        filepath = code_generator.generate_playwright_spec(g.current_project, sc)
        return jsonify({"status": "success", "filepath": filepath})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@scenarios_bp.route('/<int:sc_id>/run-native', methods=['POST'])
def run_native(sc_id):
    from flask import g, request
    from app.services.local_runner import native_runner
    
    if not g.current_project:
        return jsonify({"error": "No project selected."}), 400
        
    filepath = request.json.get('filepath')
    if not filepath:
        return jsonify({"error": "Filepath required"}), 400
        
    sc = Scenario.query.get_or_404(sc_id)
    try:
        exec_id = native_runner.run_spec(g.current_project, sc, filepath)
        return jsonify({"status": "success", "execution_id": exec_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
