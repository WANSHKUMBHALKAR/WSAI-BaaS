import os
import sys

# Ensure the backend package root is on sys.path so imports like `app.*` work in tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
