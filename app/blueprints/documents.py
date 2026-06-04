from flask import render_template, request, current_app, redirect, url_for
from werkzeug.utils import secure_filename
import os
from app.blueprints import documents_bp
from app.models.domain import Document
from app import db
from app.services.task_manager import task_manager

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'txt', 'csv', 'xlsx'}

@documents_bp.route('/', methods=['GET'])
def index():
    from flask import g
    docs = Document.query.filter(Document.filename != '_adhoc_workspace.txt', Document.project_id == g.current_project.id).order_by(Document.upload_date.desc()).all()
    return render_template('pages/documents.html', documents=docs)

@documents_bp.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Save to DB
        from flask import g
        doc = Document(
            filename=filename,
            original_name=file.filename,
            file_path=file_path,
            project_id=g.current_project.id
        )
        db.session.add(doc)
        db.session.commit()
        
        # Trigger processing task
        # We will import parser and extractor here to avoid circular imports if any
        from app.services.document_parser import document_parser
        from app.services.requirement_extractor import requirement_extractor
        from app.services.requirement_analyzer import requirement_analyzer
        from app.models.domain import Requirement
        
        app_obj = current_app._get_current_object()
        def process_doc(doc_id, path):
            with app_obj.app_context():
                d = Document.query.get(doc_id)
                if not d: return
                
                try:
                    d.status = "Processing"
                    db.session.commit()
                    
                    # 1. Parse text
                    text = document_parser.parse_document(path, d.filename)
                    
                    # 2. Extract Requirements
                    raw_reqs = requirement_extractor.extract_from_text(text)
                    
                    # 3. Save to DB
                    for r_data in raw_reqs:
                        req = Requirement(
                            document_id=d.id,
                            req_id=r_data.get('req_id', ''),
                            title=r_data.get('title', ''),
                            description=r_data.get('description', ''),
                            actor=r_data.get('actor', ''),
                            action=r_data.get('action', ''),
                            object=r_data.get('object', ''),
                            
                            # Hierarchy Metadata
                            source_section=r_data.get('source_section', ''),
                            source_subsection=r_data.get('source_subsection', ''),
                            page_number=r_data.get('page_number', ''),
                            
                            # JSON fields
                            parent_reqs=r_data.get('parent_reqs', []),
                            constraints=r_data.get('constraints', []),
                            roles=r_data.get('roles', []),
                            validations=r_data.get('validations', []),
                            business_rules=r_data.get('business_rules', []),
                            security_rules=r_data.get('security_rules', []),
                            compliance_rules=r_data.get('compliance_rules', []),
                            dependencies=r_data.get('dependencies', []),
                            integration_points=r_data.get('integration_points', []),
                            risk_indicators=r_data.get('risk_indicators', []),
                            smart_tags=r_data.get('smart_tags', []),
                            health_metrics=r_data.get('health_metrics', {}),
                            
                            priority=r_data.get('priority', 'Medium'),
                            section=r_data.get('section', 'General'),
                            req_type=r_data.get('req_type', 'Functional'),
                            health_score=r_data.get('health_score', 0)
                        )
                        db.session.add(req)
                        
                    d.status = "Completed"
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    d = Document.query.get(doc_id)
                    d.status = "Failed"
                    db.session.commit()
                    print(f"Error processing {doc_id}: {e}")
                    
        task_manager.submit_task(process_doc, doc.id, file_path)
        
        return redirect(url_for('documents.index'))
    return "Invalid file type", 400

@documents_bp.route('/<int:doc_id>/delete', methods=['POST'])
def delete(doc_id):
    doc = Document.query.get_or_404(doc_id)
    
    # Try to delete the file
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as e:
        print(f"Failed to delete file {doc.file_path}: {e}")
        
    db.session.delete(doc)
    db.session.commit()
    return redirect(url_for('documents.index'))
