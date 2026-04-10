"""
BOOKTIME - Server Principal
Point d'entrée principal pour l'API modulaire
Architecture : FastAPI + MongoDB + JWT + Modularisation complète
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Port dynamique pour Railway/Cloud deployment
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)