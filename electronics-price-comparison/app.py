"""
Entry point to run the RigRate Electronics Price Comparison server from the root directory.
"""
import sys
import os

# Prioritize backend directory in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Avoid root directory shadowing backend app module
root_dir = os.path.abspath(os.path.dirname(__file__))
had_root = root_dir in sys.path
if had_root:
    sys.path.remove(root_dir)

import app as _backend_module
app = _backend_module.app
start_scheduler = _backend_module.start_scheduler
seed_database = _backend_module.seed_database

if had_root:
    sys.path.append(root_dir)

if __name__ == '__main__':
    seed_database()
    start_scheduler()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1' and not os.environ.get('PORT')
    print("\n" + "="*50)
    print(f"  RigRate is running at http://127.0.0.1:{port}")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=port, debug=debug_mode, threaded=True)
