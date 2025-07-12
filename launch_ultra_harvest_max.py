#!/usr/bin/env python3
"""
🚀 LANCEMENT ULTRA HARVEST 100K MAXIMUM
Script pour lancer Ultra Harvest avec configuration maximale et confiance 70%
"""

import asyncio
import os
import sys
from pathlib import Path

def main():
    print("""
🚀 ULTRA HARVEST 100K MAXIMUM - CONFIANCE 70%
==============================================
🎯 Objectif: 100,000 livres (maximum)
📊 Seuil confiance: 70% (vs 75% précédent)
🗄️ Base actuelle: 7,945 séries
🔄 Expansion attendue: +2,000-5,000 nouvelles séries
==============================================
""")
    
    # Aller dans le répertoire des scripts
    script_dir = Path('/app/backend/scripts')
    os.chdir(script_dir)
    
    # Ajout du répertoire au PYTHONPATH
    sys.path.insert(0, str(script_dir.parent))
    sys.path.insert(0, '/app/backend')
    
    # Exécution avec objectif maximum
    cmd = f"cd {script_dir} && python ultra_harvest_100k_tracking.py --target 100000"
    
    print(f"🔧 Commande: {cmd}")
    print("⏳ Démarrage Ultra Harvest 100K avec confiance 70%...")
    
    # Exécution
    exit_code = os.system(cmd)
    
    if exit_code == 0:
        print("\n✅ Ultra Harvest 100K terminé avec succès!")
    else:
        print(f"\n❌ Ultra Harvest 100K terminé avec erreur (code: {exit_code})")

if __name__ == "__main__":
    main()