""" uv run python -m api [port] """
import sys

import uvicorn

uvicorn.run("api.main:app", host="0.0.0.0", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
