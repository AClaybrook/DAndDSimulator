""" uv run python -m api [port]. Listens on this machine only; set HOST=0.0.0.0 to serve other devices on your network """
import os
import sys

import uvicorn

uvicorn.run("api.main:app", host=os.environ.get("HOST", "127.0.0.1"), port=int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
