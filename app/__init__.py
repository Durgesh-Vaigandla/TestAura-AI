from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    
    with app.app_context():
        from flask import g, session, request
        from app.models.domain import Project
        
        @app.before_request
        def load_project_context():
            # Skip for static files
            if request.path.startswith('/static/'):
                return
                
            project_id = session.get('current_project_id')
            if project_id:
                g.current_project = Project.query.get(project_id)
            else:
                # Default to first project if none selected
                g.current_project = Project.query.first()
                if g.current_project:
                    session['current_project_id'] = g.current_project.id
                    
        @app.context_processor
        def inject_projects():
            projects = Project.query.all()
            return dict(all_projects=projects)

    from app.blueprints.main import main_bp
    from app.blueprints.documents import documents_bp
    from app.blueprints.requirements import requirements_bp
    from app.blueprints.scenarios import scenarios_bp
    from app.blueprints.coverage import coverage_bp
    from app.blueprints.generator import generator_bp
    from app.blueprints.execution import execution_bp
    from app.blueprints.quick_test import quick_test_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(requirements_bp)
    app.register_blueprint(scenarios_bp)
    app.register_blueprint(coverage_bp)
    app.register_blueprint(generator_bp)
    app.register_blueprint(execution_bp)
    app.register_blueprint(quick_test_bp)

    return app
