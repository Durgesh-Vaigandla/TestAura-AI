from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app.blueprints.main import main_bp
    from app.blueprints.documents import documents_bp
    from app.blueprints.requirements import requirements_bp
    from app.blueprints.scenarios import scenarios_bp
    from app.blueprints.coverage import coverage_bp
    from app.blueprints.generator import generator_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(requirements_bp)
    app.register_blueprint(scenarios_bp)
    app.register_blueprint(coverage_bp)
    app.register_blueprint(generator_bp)

    return app
