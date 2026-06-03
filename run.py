from app import create_app, db

app = create_app()

def init_db():
    with app.app_context():
        # Create FTS5 virtual tables manually if needed, but SQLAlchemy creates standard tables
        db.create_all()
        print("Database initialized.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'init-db':
        init_db()
    else:
        app.run(debug=True, port=5001)
