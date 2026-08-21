import os
import sys

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

try:
    schema = app.openapi()
    print("OpenAPI schema generated successfully!")
except Exception as e:
    import traceback
    print("OpenAPI Generation Exception Traceback:")
    traceback.print_exc()
