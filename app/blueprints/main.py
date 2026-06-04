from flask import render_template
from app.blueprints import main_bp
from app.models.domain import Document, Requirement, Scenario

@main_bp.route('/')
def index():
    doc_count = Document.query.count()
    req_count = Requirement.query.count()
    scen_count = Scenario.query.count()
    return render_template('pages/index.html', doc_count=doc_count, req_count=req_count, scen_count=scen_count)

@main_bp.route('/api/system-status')
def system_status():
    from app.services.llm_service import llm_service, _HAS_LLAMA
    import os
    
    is_ready = _HAS_LLAMA and os.path.exists(llm_service.model_path)
    is_loaded = llm_service.is_loaded
    
    if is_loaded:
        return '''
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <svg class="-ml-0.5 mr-1.5 h-2 w-2 text-green-500 animate-pulse" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
          AI Engine Online
        </span>
        '''
    elif is_ready:
        return '''
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800" title="AI model is ready to be loaded on first request">
          <svg class="-ml-0.5 mr-1.5 h-2 w-2 text-yellow-400" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
          AI Engine Standby
        </span>
        '''
    else:
        return '''
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800" title="Model file not found or llama-cpp not installed">
          <svg class="-ml-0.5 mr-1.5 h-2 w-2 text-red-400" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
          AI Engine Offline
        </span>
        '''

@main_bp.route('/switch-project/<int:project_id>')
def switch_project(project_id):
    from flask import session, redirect, request
    session['current_project_id'] = project_id
    # Redirect back to where they came from
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/projects', methods=['GET', 'POST'])
def manage_projects():
    from flask import request, redirect, url_for, render_template
    from app.models.domain import Project
    from app import db
    
    if request.method == 'POST':
        name = request.form.get('name')
        desc = request.form.get('description')
        context = request.form.get('global_context')
        target_dir = request.form.get('target_directory')
        test_folder = request.form.get('test_folder') or 'testaura_e2e'
        test_command = request.form.get('test_command') or 'npx playwright test --reporter=json'
        
        if name:
            new_proj = Project(
                name=name, 
                description=desc, 
                global_context=context,
                target_directory=target_dir,
                test_folder=test_folder,
                test_command=test_command
            )
            db.session.add(new_proj)
            db.session.commit()
            return redirect(url_for('main.manage_projects'))
            
    projects = Project.query.all()
    return render_template('pages/projects.html', projects=projects)

@main_bp.route('/create-test')
def create_test():
    from flask import g
    from app.models.domain import Document
    
    docs = []
    if g.current_project:
        docs = Document.query.filter(Document.filename != '_adhoc_workspace.txt', Document.project_id == g.current_project.id).all()
        
    return render_template('pages/create_test.html', documents=docs)
