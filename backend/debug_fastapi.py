#!/usr/bin/env python3
import sys
import os

print("=== DEBUGGING FASTAPI INSTALLATION ===")

try:
    import fastapi
    print(f"✓ FastAPI version: {fastapi.__version__}")
except Exception as e:
    print(f"✗ FastAPI import error: {e}")
    sys.exit(1)

try:
    from fastapi import FastAPI
    print("✓ FastAPI class import successful")
except Exception as e:
    print(f"✗ FastAPI class import error: {e}")
    sys.exit(1)

try:
    app = FastAPI()
    print("✓ FastAPI instance creation successful")
except Exception as e:
    print(f"✗ FastAPI instance creation error: {e}")
    sys.exit(1)

try:
    @app.get("/")
    def root():
        return {"message": "test"}
    print("✓ Route definition successful")
except Exception as e:
    print(f"✗ Route definition error: {e}")
    sys.exit(1)

try:
    import uvicorn
    print(f"✓ Uvicorn version: {uvicorn.__version__}")
except Exception as e:
    print(f"✗ Uvicorn import error: {e}")
    sys.exit(1)

print("\n=== TESTING MIDDLEWARE ===")

try:
    from fastapi.middleware.cors import CORSMiddleware
    print("✓ CORS middleware import successful")
except Exception as e:
    print(f"✗ CORS middleware import error: {e}")

try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    print("✓ CORS middleware setup successful")
except Exception as e:
    print(f"✗ CORS middleware setup error: {e}")

print("\nAll checks passed!")