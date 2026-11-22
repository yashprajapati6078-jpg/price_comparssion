"""
Entry point to run the RigRate Electronics Price Comparison server from the root directory.
"""
import sys
import os

# Prioritize backend directory in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import backend.app as _backend_module
app = _backend_module.app
start_scheduler = _backend_module.start_scheduler
seed_database = _backend_module.seed_database

# Check SQLite database integrity on startup; auto-heal if corrupt
db_path = os.path.join(backend_dir, 'electronics.db')
if os.path.exists(db_path):
    try:
        import sqlite3
        con = sqlite3.connect(db_path)
        chk = con.execute("PRAGMA integrity_check;").fetchone()
        con.close()
        if not chk or chk[0] != 'ok':
            print(f"[RigRate Warning] SQLite database corrupt ({chk}). Removing to rebuild fresh...")
            for f in [db_path, db_path + '-wal', db_path + '-shm']:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass
    except Exception as e:
        print(f"[RigRate Warning] Database integrity check failed: {e}")

# Ensure database tables exist and initial catalog is populated when running under Gunicorn
try:
    with app.app_context():
        from models import db, Category, Product
        db.create_all()
        if Category.query.count() == 0 or Product.query.count() == 0:
            print("[RigRate Startup] Seeding initial database...")
            seed_database()
except Exception as e:
    print(f"[RigRate Startup] Notice during DB check: {e}")
    if "malformed" in str(e).lower() or "disk image" in str(e).lower():
        try:
            print("[RigRate Startup] Malformed database detected. Rebuilding cleanly...")
            for f in [db_path, db_path + '-wal', db_path + '-shm']:
                if os.path.exists(f):
                    os.remove(f)
            with app.app_context():
                from models import db
                db.create_all()
                seed_database()
        except Exception as retry_err:
            print(f"[RigRate Startup] Re-seed failed: {retry_err}")

if __name__ == '__main__':
    seed_database()
    start_scheduler()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1' and not os.environ.get('PORT')
    print("\n" + "="*50)
    print(f"  RigRate is running at http://127.0.0.1:{port}")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=port, debug=debug_mode, threaded=True)
