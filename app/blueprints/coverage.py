from flask import render_template, request, send_file
from app.blueprints import coverage_bp
from app.models.domain import Document
from app.services.coverage_service import coverage_service
from app.services.export_service import export_service
import io

@coverage_bp.route('/', methods=['GET'])
def index():
    doc_id = request.args.get('doc_id')
    docs = Document.query.all()
    
    metrics = None
    selected_doc = None
    
    if doc_id:
        metrics = coverage_service.get_coverage_metrics(int(doc_id))
        selected_doc = Document.query.get(doc_id)
        
    return render_template('pages/coverage.html', documents=docs, metrics=metrics, selected_doc=selected_doc)
    
@coverage_bp.route('/export/<int:doc_id>/feature', methods=['GET'])
def export_feature(doc_id):
    content = export_service.export_to_feature_file(doc_id)
    return send_file(
        io.BytesIO(content.encode('utf-8')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=f'document_{doc_id}_scenarios.feature'
    )
    
@coverage_bp.route('/export/<int:doc_id>/csv', methods=['GET'])
def export_csv(doc_id):
    content = export_service.export_to_csv(doc_id)
    return send_file(
        io.BytesIO(content.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'document_{doc_id}_scenarios.csv'
    )
