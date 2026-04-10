# Scripts BOOKTIME - Résolution Automatique Problème Création Compte

## Vue d'ensemble

Ces scripts résolvent définitivement le problème de création de compte dans l'environnement Preview Emergent en configurant automatiquement l'URL backend correcte.

## Scripts disponibles

### 🔧 configure_preview.sh
**Usage**: `./configure_preview.sh`
**Description**: Configure automatiquement l'URL backend pour l'environnement Preview Emergent
**Actions**:
- Détecte automatiquement l'URL Preview Emergent 
- Configure le fichier `/app/frontend/.env` avec la bonne URL
- Teste la connectivité API
- Redémarre les services
- Valide la solution

### 🩺 health_check.sh  
**Usage**: `./health_check.sh`
**Description**: Vérifie la santé de l'application et corrige automatiquement si nécessaire
**Actions**:
- Vérifie le statut des services
- Teste la configuration frontend
- Test fonctionnel création de compte
- Auto-correction si problème détecté

### ⏰ setup_monitoring.sh
**Usage**: `./setup_monitoring.sh` 
**Description**: Met en place une surveillance automatique
**Actions**:
- Configure un cron job de surveillance (toutes les 10 min)
- Hooks de démarrage automatique
- Documentation complète

### 🚀 startup_fix.sh
**Usage**: Exécuté automatiquement au démarrage
**Description**: S'assure de la bonne configuration au démarrage des services

### 🔄 cron_health_check.sh
**Usage**: Exécuté automatiquement par cron
**Description**: Surveillance périodique avec auto-correction

## Logs

- `/var/log/booktime_health.log` - Logs du health check
- `/var/log/booktime_cron.log` - Logs de la surveillance cron  
- `/var/log/booktime_startup.log` - Logs de démarrage

## Résolution manuelle

Si besoin de résolution manuelle :

```bash
# Diagnostic complet
./health_check.sh

# Reconfiguration forcée
./configure_preview.sh

# Vérification des services
sudo supervisorctl status

# Vérification de la configuration
cat /app/frontend/.env
```

## Historique du problème

**Problème**: En environnement Preview Emergent, le frontend tentait d'accéder à `localhost:8001` qui n'est pas accessible depuis l'extérieur.

**Solution**: Configuration automatique de `REACT_APP_BACKEND_URL` avec l'URL Preview Emergent détectée automatiquement.

**Sessions concernées**: 89.6, 89.7 (voir CHANGELOG.md)

## Maintenance

Les scripts sont conçus pour être autonomes et ne nécessitent pas de maintenance manuelle. La surveillance automatique détecte et corrige les problèmes.

Mise à jour des scripts: Modifier directement les fichiers et relancer `./setup_monitoring.sh` si nécessaire.
