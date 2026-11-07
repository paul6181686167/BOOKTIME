#!/usr/bin/env python3
"""
Phase 2.1 : Optimisation MongoDB - Exécution directe
Script pour exécuter l'optimisation complète MongoDB de BOOKTIME
"""

import sys
import os
sys.path.append('/app/backend')

from app.database.optimization import MongoOptimizer

def main():
    print("🚀 PHASE 2.1 : OPTIMISATION MONGODB - DÉMARRAGE")
    print("=" * 60)
    
    try:
        # Initialisation de l'optimiseur
        optimizer = MongoOptimizer()
        
        # Exécution de l'optimisation complète
        result = optimizer.run_phase_2_1_optimization()
        
        print("\n✅ PHASE 2.1 TERMINÉE AVEC SUCCÈS !")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERREUR PHASE 2.1: {e}")
        return None

if __name__ == "__main__":
    main()