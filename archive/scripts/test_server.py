#!/usr/bin/env python3

import sys
import os
sys.path.append('/app/backend')

try:
    print("🔍 Importation du module server...")
    from server import app
    print("✅ Import réussi!")
    
    print(f"📊 Nombre de routes: {len(app.routes)}")
    
    print("🔍 Test de l'instance FastAPI...")
    print(f"Title: {app.title}")
    print(f"Description: {app.description}")
    
    print("🔍 Middleware configurés:")
    for middleware in app.user_middleware:
        print(f"  - {middleware}")
    
    print("✅ Tous les tests passent!")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()