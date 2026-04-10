#!/usr/bin/env python3
"""
Script de diagnostic Railway
Vérifie les variables d'environnement et la configuration
"""
import os
import sys

def main():
    print("🔍 DIAGNOSTIC RAILWAY BACKEND")
    print("=" * 50)
    
    # Variables d'environnement critiques
    env_vars = {
        'PORT': os.environ.get('PORT'),
        'MONGO_URL': os.environ.get('MONGO_URL'),
        'EMERGENT_LLM_KEY': os.environ.get('EMERGENT_LLM_KEY'),
        'ENVIRONMENT': os.environ.get('ENVIRONMENT'),
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
        'RAILWAY_SERVICE_NAME': os.environ.get('RAILWAY_SERVICE_NAME'),
    }
    
    print("📋 Variables d'environnement:")
    for key, value in env_vars.items():
        if value:
            if 'KEY' in key or 'URL' in key:
                # Masquer les valeurs sensibles
                masked = value[:10] + '...' if len(value) > 10 else value
                print(f"  ✅ {key}: {masked}")
            else:
                print(f"  ✅ {key}: {value}")
        else:
            print(f"  ❌ {key}: NON DÉFINIE")
    
    # Test conversion PORT
    print("\n🔢 Test conversion PORT:")
    port_str = os.environ.get('PORT')
    if port_str:
        try:
            port_int = int(port_str)
            print(f"  ✅ PORT '{port_str}' → {port_int} (entier)")
        except (ValueError, TypeError):
            print(f"  ❌ PORT '{port_str}' ne peut pas être converti en entier")
    else:
        print(f"  ⚠️ PORT non définie, utilisation du défaut 8001")
    
    # Vérification des fichiers critiques
    print("\n📁 Fichiers critiques:")
    files = ['app/main.py', 'requirements.txt', 'railway.json', 'start.py']
    for file in files:
        if os.path.exists(file):
            print(f"  ✅ {file}: PRÉSENT")
        else:
            print(f"  ❌ {file}: MANQUANT")
    
    # Test import application
    print("\n🚀 Test import application:")
    try:
        from app.main import app
        print(f"  ✅ Application importée avec succès")
        print(f"  📊 Type: {type(app)}")
    except Exception as e:
        print(f"  ❌ Erreur import: {e}")
        return False
    
    print("\n✅ Diagnostic terminé")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)