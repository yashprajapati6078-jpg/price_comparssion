"""
Entry point to run the RigRate Electronics Price Comparison server from the root directory.
"""
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app, start_scheduler

if __name__ == '__main__':
    start_scheduler()
    print("\n" + "="*50)
    print("  RigRate is running at http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)
