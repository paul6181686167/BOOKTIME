"""
Script de démarrage pour Render.com
Différences vs Railway :
  - Pas de test MongoDB bloquant au démarrage (Render a déjà les var d'env)
  - Port via $PORT (identique)
  - Logs sans emojis pour compatibilité console Render
"""
import os
import sys

def main():
    port = int(os.environ.get("PORT", 8001))
    env  = os.environ.get("ENVIRONMENT", "production")

    print(f"[BOOKTIME] Demarrage backend - env={env} port={port}")

    # Vérification rapide des variables critiques
    if not os.environ.get("MONGO_URL"):
        print("[BOOKTIME] ERREUR: MONGO_URL non definie - verifie les variables Render")
        sys.exit(1)

    # S'assurer que le mode mock est desactive
    os.environ["RAILWAY_MONGODB_MOCK"] = "false"

    try:
        import uvicorn
        from app.main import app

        print(f"[BOOKTIME] Application chargee - demarrage sur 0.0.0.0:{port}")

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True,
        )

    except Exception as e:
        print(f"[BOOKTIME] Erreur fatale au demarrage: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
