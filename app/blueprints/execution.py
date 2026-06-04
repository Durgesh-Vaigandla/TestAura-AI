from flask import Blueprint, render_template, request, jsonify
from app.models.domain import Scenario, Execution, ExecutionStep, ExecutionResult
from app import db
from engines.core.execution_context import ExecutionContext, ExecutionMode
from engines.web.playwright.playwright_runner import PlaywrightRunner
from engines.evidence.artifact_manager import ArtifactManager
import json
import threading

execution_bp = Blueprint('execution', __name__, url_prefix='/execution')

@execution_bp.route('/')
def execution_lab():
    scenarios = Scenario.query.all()
    executions = Execution.query.order_by(Execution.created_at.desc()).limit(10).all()
    return render_template('pages/execution.html', scenarios=scenarios, executions=executions)

@execution_bp.route('/run', methods=['POST'])
def run_execution():
    data = request.json
    target_url = data.get('target_url')
    mode_str = data.get('mode', 'Fast')
    scenario_ids = data.get('scenario_ids', [])
    
    if not target_url or not scenario_ids:
        return jsonify({'error': 'Target URL and at least one scenario are required'}), 400
        
    mode = ExecutionMode(mode_str)
    
    # Create DB Record
    exec_record = Execution(
        target_url=target_url,
        engine='playwright',
        mode=mode.value,
        status='Running'
    )
    db.session.add(exec_record)
    db.session.commit()
    
    # Generate Intents using LLM
    from app.services.llm_service import llm_service
    intents = []
    for sid in scenario_ids:
        scenario = Scenario.query.get(sid)
        if scenario:
            scenario_dict = {
                'title': scenario.title,
                'given': scenario.given,
                'when': scenario.when,
                'then': scenario.then
            }
            steps = llm_service.generate_execution_intent(scenario_dict, target_url)
            intent = {
                "id": scenario.id,
                "title": scenario.title,
                "steps": steps
            }
            intents.append(intent)
            
    # Run async
    thread = threading.Thread(target=_run_async, args=(exec_record.id, target_url, mode, intents))
    thread.start()
    
    return jsonify({'execution_id': exec_record.id, 'status': 'Started'})

def _run_async(exec_id, target_url, mode, intents):
    from app import create_app
    app = create_app()
    with app.app_context():
        exec_record = Execution.query.get(exec_id)
        artifact_mgr = ArtifactManager()
        artifacts_dir = artifact_mgr.create_execution_dir(exec_id)
        
        context = ExecutionContext(
            execution_id=exec_id,
            target_url=target_url,
            mode=mode,
            engine_name='playwright',
            artifacts_dir=artifacts_dir
        )
        
        runner = PlaywrightRunner()
        try:
            result_payload = runner.run(intents, context)
            
            exec_record.status = result_payload.status
            exec_record.duration = result_payload.total_duration
            
            # Save Results
            for scen_res in result_payload.scenario_results:
                db_res = ExecutionResult(
                    execution_id=exec_id,
                    scenario_id=scen_res.scenario_id,
                    status=scen_res.status,
                    duration=scen_res.duration,
                    error_message=scen_res.error_message
                )
                db.session.add(db_res)
                
                for step_res in scen_res.steps:
                    db_step = ExecutionStep(
                        execution_id=exec_id,
                        scenario_id=scen_res.scenario_id,
                        step_index=step_res.step_index,
                        action=step_res.action,
                        target=step_res.target,
                        status=step_res.status,
                        error_message=step_res.error_message,
                        start_time=None, # Update these if we want strict start/end times
                        end_time=None
                    )
                    db.session.add(db_step)
                    
                from app.models.domain import Screenshot
                for path in scen_res.screenshots:
                    db_screenshot = Screenshot(
                        execution_id=exec_id,
                        file_path=path
                    )
                    db.session.add(db_screenshot)
                    
            db.session.commit()
            
        except Exception as e:
            exec_record.status = "Failed"
            db.session.commit()
            print(f"Execution Failed: {e}")
        finally:
            runner.cleanup()

@execution_bp.route('/status/<int:execution_id>')
def get_status(execution_id):
    exec_record = Execution.query.get_or_404(execution_id)
    return jsonify({
        'status': exec_record.status,
        'duration': exec_record.duration,
        'mode': exec_record.mode
    })

@execution_bp.route('/<int:execution_id>')
def execution_details(execution_id):
    exec_record = Execution.query.get_or_404(execution_id)
    return render_template('pages/execution_details.html', execution=exec_record)
