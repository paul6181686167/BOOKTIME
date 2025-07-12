#!/usr/bin/env python3
"""
⚡ EXPANSION OPTIMIZER - GESTIONNAIRE STRATÉGIES OPTIMISÉES
Optimiseur intelligent pour coordonner toutes les stratégies d'expansion

Fonctionnalités :
1. Coordination scripts expansion existants
2. Optimisation performance avec tracking
3. Stratégies adaptatives selon résultats
4. Monitoring temps réel
5. Auto-ajustement limites selon performance
"""

import asyncio
import subprocess
import json
import time
from pathlib import Path
import logging
from typing import Dict, List, Optional

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/expansion_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExpansionOptimizer:
    """Optimiseur intelligent expansion massive"""
    
    def __init__(self):
        self.scripts_dir = Path('/app/backend/scripts')
        self.data_dir = Path('/app/data')
        
        # Scripts disponibles avec nouvelles limites
        self.expansion_scripts = {
            'mega_expansion': {
                'script': 'mega_expansion_openlibrary.py',
                'default_limit': 5000,
                'max_limit': 50000,
                'strategies': ['keywords', 'authors', 'franchises', 'categories'],
                'avg_performance': 2.7  # livres/seconde historique
            },
            'ultra_expansion': {
                'script': 'ultra_expansion_openlibrary.py', 
                'default_limit': 10000,
                'max_limit': 100000,
                'strategies': ['languages', 'publishers', 'decades', 'genres', 'awards'],
                'avg_performance': 1.8
            },
            'mega_harvest': {
                'script': 'mega_harvest_openlibrary.py',
                'default_limit': 20000,
                'max_limit': 200000,
                'strategies': ['volume_patterns', 'prolific_authors', 'numeric_patterns'],
                'avg_performance': 3.5
            },
            'unlimited_manager': {
                'script': 'unlimited_expansion_manager.py',
                'default_limit': 100000,
                'max_limit': 1000000,
                'strategies': ['comprehensive_all'],
                'avg_performance': 5.0
            }
        }
        
        # Métriques session
        self.session_metrics = {
            'start_time': None,
            'total_books_processed': 0,
            'total_new_series': 0,
            'scripts_executed': [],
            'performance_data': {},
            'optimization_applied': []
        }

    async def run_optimized_expansion(self, target_books: int = 500000, adaptive: bool = True) -> Dict:
        """
        Lancer expansion optimisée avec toutes stratégies
        
        Args:
            target_books: Nombre cible livres à analyser (défaut: 500K)
            adaptive: Ajustement adaptatif limites selon performance
        """
        self.session_metrics['start_time'] = time.time()
        
        logger.info(f"""
⚡ EXPANSION OPTIMIZER DÉMARRÉ
============================
🎯 Objectif: {target_books:,} livres
🧠 Mode adaptatif: {'OUI' if adaptive else 'NON'}
📊 Scripts disponibles: {len(self.expansion_scripts)}
============================
""")
        
        try:
            # Répartition intelligente charge
            allocation = self._calculate_optimal_allocation(target_books)
            
            # Exécution séquentielle optimisée
            for script_name, target_allocation in allocation.items():
                if target_allocation > 0:
                    await self._execute_expansion_script(script_name, target_allocation, adaptive)
                    
                    # Vérification objectif atteint
                    if self.session_metrics['total_books_processed'] >= target_books:
                        logger.info(f"🎯 Objectif atteint: {self.session_metrics['total_books_processed']:,} livres")
                        break
            
            # Calcul métriques finales
            total_time = time.time() - self.session_metrics['start_time']
            performance = self.session_metrics['total_books_processed'] / total_time if total_time > 0 else 0
            
            result = {
                'success': True,
                'total_books_processed': self.session_metrics['total_books_processed'],
                'total_new_series': self.session_metrics['total_new_series'],
                'execution_time': total_time,
                'performance_bps': performance,  # books per second
                'scripts_used': len(self.session_metrics['scripts_executed']),
                'optimizations_applied': self.session_metrics['optimization_applied']
            }
            
            logger.info(f"""
✅ EXPANSION OPTIMIZER TERMINÉ !
===============================
📚 Livres traités: {result['total_books_processed']:,}
🆕 Nouvelles séries: {result['total_new_series']:,}
⚡ Performance: {result['performance_bps']:.1f} livres/sec
⏱️ Durée totale: {result['execution_time']:.1f}s
🔧 Scripts utilisés: {result['scripts_used']}
===============================
""")
            
            # Sauvegarder métriques pour futures optimisations
            await self._save_performance_metrics(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur expansion optimizer: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_optimal_allocation(self, target_books: int) -> Dict[str, int]:
        """Calcul allocation optimale selon performance historique"""
        total_performance = sum(script['avg_performance'] for script in self.expansion_scripts.values())
        
        allocation = {}
        for script_name, script_info in self.expansion_scripts.items():
            # Répartition proportionnelle à la performance
            weight = script_info['avg_performance'] / total_performance
            allocated = int(target_books * weight)
            
            # Respect limites maximales
            allocated = min(allocated, script_info['max_limit'])
            
            allocation[script_name] = allocated
            
        logger.info(f"📊 Allocation calculée: {allocation}")
        return allocation

    async def _execute_expansion_script(self, script_name: str, target: int, adaptive: bool):
        """Exécuter script expansion avec monitoring"""
        script_info = self.expansion_scripts[script_name]
        script_path = self.scripts_dir / script_info['script']
        
        if not script_path.exists():
            logger.warning(f"⚠️ Script non trouvé: {script_path}")
            return
        
        # Ajustement adaptatif limites
        if adaptive:
            target = self._adaptive_limit_adjustment(script_name, target)
        
        logger.info(f"🚀 Exécution {script_name} avec limite {target:,}")
        start_time = time.time()
        
        try:
            # Préparer commande
            cmd = [
                'python', str(script_path),
                '--limit', str(target)
            ]
            
            # Mode illimité si disponible
            if target > script_info['default_limit']:
                cmd.append('--unlimited')
            
            # Exécution avec capture sortie
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.scripts_dir
            )
            
            stdout, stderr = await process.communicate()
            execution_time = time.time() - start_time
            
            # Parser résultats
            result = self._parse_script_output(stdout.decode(), stderr.decode())
            
            # Mettre à jour métriques
            self.session_metrics['scripts_executed'].append({
                'script': script_name,
                'target': target,
                'execution_time': execution_time,
                'result': result
            })
            
            self.session_metrics['total_books_processed'] += result.get('books_processed', 0)
            self.session_metrics['total_new_series'] += result.get('new_series', 0)
            
            # Enregistrer performance pour adaptation future
            performance = result.get('books_processed', 0) / execution_time if execution_time > 0 else 0
            self.session_metrics['performance_data'][script_name] = performance
            
            logger.info(f"✅ {script_name} terminé: {result.get('books_processed', 0):,} livres en {execution_time:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Erreur exécution {script_name}: {e}")

    def _adaptive_limit_adjustment(self, script_name: str, target: int) -> int:
        """Ajustement adaptatif limite selon performance observée"""
        script_info = self.expansion_scripts[script_name]
        
        # Facteur d'ajustement selon performance historique
        if script_info['avg_performance'] > 3.0:
            # Script performant → augmenter limite
            adjusted = int(target * 1.5)
            self.session_metrics['optimization_applied'].append(f"{script_name}: limite augmentée x1.5")
        elif script_info['avg_performance'] < 2.0:
            # Script moins performant → conserver limite
            adjusted = target
        else:
            # Performance moyenne → légère augmentation
            adjusted = int(target * 1.2)
            self.session_metrics['optimization_applied'].append(f"{script_name}: limite augmentée x1.2")
        
        # Respect limite maximale
        adjusted = min(adjusted, script_info['max_limit'])
        
        if adjusted != target:
            logger.info(f"🔧 Ajustement adaptatif {script_name}: {target:,} → {adjusted:,}")
        
        return adjusted

    def _parse_script_output(self, stdout: str, stderr: str) -> Dict:
        """Parser sortie script pour extraire métriques"""
        result = {
            'books_processed': 0,
            'new_series': 0,
            'queries_made': 0,
            'success': True
        }
        
        try:
            # Rechercher patterns dans stdout
            lines = stdout.split('\n')
            for line in lines:
                if 'livres analysés' in line or 'books analyzed' in line:
                    # Extraire nombre
                    numbers = [int(s) for s in line.split() if s.isdigit()]
                    if numbers:
                        result['books_processed'] = max(numbers)
                
                elif 'nouvelles séries' in line or 'new series' in line:
                    numbers = [int(s) for s in line.split() if s.isdigit()]
                    if numbers:
                        result['new_series'] = max(numbers)
                
                elif 'requêtes' in line or 'queries' in line:
                    numbers = [int(s) for s in line.split() if s.isdigit()]
                    if numbers:
                        result['queries_made'] = max(numbers)
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur parsing output: {e}")
            
        if stderr and 'error' in stderr.lower():
            result['success'] = False
            result['error'] = stderr
            
        return result

    async def _save_performance_metrics(self, result: Dict):
        """Sauvegarder métriques pour optimisations futures"""
        try:
            metrics_file = self.data_dir / 'optimizer_metrics.json'
            
            # Charger historique
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    history = json.load(f)
            else:
                history = {'sessions': []}
            
            # Ajouter session actuelle
            session_data = {
                'timestamp': time.time(),
                'result': result,
                'session_metrics': self.session_metrics
            }
            history['sessions'].append(session_data)
            
            # Garder seulement 100 dernières sessions
            history['sessions'] = history['sessions'][-100:]
            
            # Sauvegarder
            with open(metrics_file, 'w') as f:
                json.dump(history, f, indent=2)
                
            logger.info("💾 Métriques performance sauvegardées")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur sauvegarde métriques: {e}")

    async def get_performance_report(self) -> Dict:
        """Générer rapport performance des scripts"""
        try:
            metrics_file = self.data_dir / 'optimizer_metrics.json'
            
            if not metrics_file.exists():
                return {'error': 'Pas de données historiques'}
            
            with open(metrics_file, 'r') as f:
                history = json.load(f)
            
            # Analyser performance par script
            script_stats = {}
            for session in history['sessions'][-10:]:  # 10 dernières sessions
                for script_exec in session['session_metrics'].get('scripts_executed', []):
                    script_name = script_exec['script']
                    
                    if script_name not in script_stats:
                        script_stats[script_name] = {
                            'executions': 0,
                            'total_books': 0,
                            'total_time': 0,
                            'avg_performance': 0
                        }
                    
                    stats = script_stats[script_name]
                    stats['executions'] += 1
                    stats['total_books'] += script_exec['result'].get('books_processed', 0)
                    stats['total_time'] += script_exec['execution_time']
                    
                    if stats['total_time'] > 0:
                        stats['avg_performance'] = stats['total_books'] / stats['total_time']
            
            return {
                'script_performance': script_stats,
                'total_sessions': len(history['sessions']),
                'last_session': history['sessions'][-1] if history['sessions'] else None
            }
            
        except Exception as e:
            return {'error': str(e)}

# Point d'entrée principal
async def main():
    """Point d'entrée expansion optimizer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Expansion Optimizer")
    parser.add_argument('--target', type=int, default=500000, help='Nombre cible de livres')
    parser.add_argument('--adaptive', action='store_true', help='Mode adaptatif intelligent')
    parser.add_argument('--report', action='store_true', help='Afficher rapport performance')
    args = parser.parse_args()
    
    optimizer = ExpansionOptimizer()
    
    if args.report:
        report = await optimizer.get_performance_report()
        print("\n📊 RAPPORT PERFORMANCE")
        print("======================")
        print(json.dumps(report, indent=2))
        return
    
    print(f"""
⚡ EXPANSION OPTIMIZER
====================
🎯 Objectif: {args.target:,} livres
🧠 Adaptatif: {'OUI' if args.adaptive else 'NON'}
====================
""")
    
    result = await optimizer.run_optimized_expansion(args.target, args.adaptive)
    
    if result['success']:
        print(f"""
✅ OPTIMISATION RÉUSSIE !
========================
📚 Livres: {result['total_books_processed']:,}
🆕 Séries: {result['total_new_series']:,}
⚡ Performance: {result['performance_bps']:.1f} l/s
⏱️ Durée: {result['execution_time']:.1f}s
========================
""")
    else:
        print(f"❌ ERREUR: {result.get('error', 'Inconnue')}")

if __name__ == "__main__":
    asyncio.run(main())