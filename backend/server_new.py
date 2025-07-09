"""
BOOKTIME API - Version Modulaire
Point d'entrée pour l'architecture modulaire
"""

from app.main import app

# Export pour compatibility
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)