"""
Saksham_AI Application Launcher
Starts the FastAPI backend and serves the frontend on http://localhost:8000
"""

import sys
import os

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import uvicorn

# Add workspace directory to python path
workspace_dir = os.path.dirname(os.path.abspath(__file__))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from backend.database import init_db

def main():
    print("=" * 65)
    print("  [*] SAKSHAM_AI - Real-Time Prompt Coaching & Cost Platform")
    print("=" * 65)
    print("  Initializing SQLite database & historical BI analytics...")
    init_db()
    print("  Database initialized and pre-seeded with 30-day analytics.")
    print("  Starting FastAPI server on http://localhost:8000")
    print("  Open your browser to: http://localhost:8000")
    print("=" * 65)
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
