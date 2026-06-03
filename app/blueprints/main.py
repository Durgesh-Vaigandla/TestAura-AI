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
