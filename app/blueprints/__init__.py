from flask import Blueprint

main_bp = Blueprint('main', __name__)
documents_bp = Blueprint('documents', __name__, url_prefix='/documents')
requirements_bp = Blueprint('requirements', __name__, url_prefix='/requirements')
scenarios_bp = Blueprint('scenarios', __name__, url_prefix='/scenarios')
coverage_bp = Blueprint('coverage', __name__, url_prefix='/coverage')
generator_bp = Blueprint('generator', __name__, url_prefix='/generator')
execution_bp = Blueprint('execution', __name__, url_prefix='/execution')

from app.blueprints import main, documents, requirements, scenarios, coverage, generator, execution
