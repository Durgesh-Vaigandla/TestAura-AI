from app import create_app, db

app = create_app()

def init_db():
    with app.app_context():
        # Create FTS5 virtual tables manually if needed, but SQLAlchemy creates standard tables
        db.create_all()
        # Migration: Add columns to existing tables if needed
        try:
            db.session.execute(db.text("ALTER TABLE documents ADD COLUMN project_id INTEGER REFERENCES projects(id)"))
            db.session.execute(db.text("ALTER TABLE executions ADD COLUMN project_id INTEGER REFERENCES projects(id)"))
            db.session.execute(db.text("ALTER TABLE projects ADD COLUMN target_directory VARCHAR(500)"))
            db.session.execute(db.text("ALTER TABLE projects ADD COLUMN test_folder VARCHAR(255) DEFAULT 'testaura_e2e'"))
            db.session.execute(db.text("ALTER TABLE projects ADD COLUMN test_command VARCHAR(255) DEFAULT 'npx playwright test --reporter=json'"))
            db.session.commit()
        except Exception as e:
            # Column likely already exists
            db.session.rollback()

        # Migration: Create Default Project if none exists
        from app.models.domain import Project, Document, Execution
        if Project.query.count() == 0:
            default_project = Project(
                name="Default Workspace",
                description="Your automatically migrated legacy workspace.",
                global_context="Write global instructions here that apply to all tests in this project (e.g. login credentials, roles, tabs to click)."
            )
            db.session.add(default_project)
            db.session.commit()
            
            # Migrate all Documents and Executions
            Document.query.update({'project_id': default_project.id})
            Execution.query.update({'project_id': default_project.id})
            db.session.commit()
            
        print("Database initialized.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'init-db':
        init_db()
    else:
        app.run(debug=True, port=5001)
