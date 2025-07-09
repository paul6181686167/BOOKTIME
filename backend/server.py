"""
BOOKTIME - Server Principal
Point d'entrée principal pour l'API modulaire
Architecture : FastAPI + MongoDB + JWT + Modularisation complète
"""
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)