# 🚀 GUIDE DÉPLOIEMENT ULTRA HARVEST PERMANENT

## 📋 RÉSUMÉ RAPIDE

✅ **Ultra Harvest 100k peut tourner en permanence en production**  
✅ **Mécanisme** : Cron job hebdomadaire + rate limiting  
✅ **Fréquence** : Dimanche 2h UTC (optimal API + maintenance)  
✅ **Target** : 1000 livres/semaine (vs 100k développement)  
✅ **Impact** : +500-2000 nouvelles séries/an automatiquement  

## ⚡ DÉPLOIEMENT EXPRESS

### 1. Railway (Recommandé)
```bash
# Ajouter au railway.toml
[build]
command = "chmod +x /app/scripts/weekly_ultra_harvest.sh"

[deploy]
variables = [
  "ULTRA_HARVEST_ENABLED=true",
  "CRON_SCHEDULE=0 2 * * 0"
]
```

### 2. Kubernetes
```yaml
# ultra-harvest-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ultra-harvest-weekly
spec:
  schedule: "0 2 * * 0"  # Dimanche 2h UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: ultra-harvest
            image: booktime:latest
            command: ["/app/scripts/weekly_ultra_harvest.sh"]
```

### 3. Cron Manuel
```bash
# Ajouter à crontab -e
0 2 * * 0 cd /app && /app/scripts/weekly_ultra_harvest.sh
```

## 📊 CONFIGURATION PRODUCTION

### Rate Limiting Respectueux
- **Délai entre requêtes** : 500ms (vs 50-150ms dev)
- **Max requêtes/heure** : 100
- **Target réduit** : 1000 livres/run
- **User-Agent** : BOOKTIME-Production/1.0

### Exclusions Maintenues
- ✅ Livres cuisine : cookbook, recipes, culinary
- ✅ Revues universitaires : university_press_analysis désactivée
- ✅ Publications académiques : textbook, handbook, proceedings

## 🔍 MONITORING AUTOMATIQUE

### Scripts Disponibles
```bash
# Monitoring santé système
python /app/scripts/monitor_ultra_harvest_production.py

# Statistiques base données
python /app/backend/scripts/ultra_harvest_100k_tracking.py --stats

# Test exécution manuelle
/app/scripts/weekly_ultra_harvest.sh
```

### Métriques Cibles
- **Nouvelles séries/semaine** : 10-50
- **Durée exécution** : <10 minutes
- **Taux succès** : >95%
- **Impact API** : <100 requêtes/semaine

## 📁 FICHIERS CRÉÉS

```
/app/scripts/
├── weekly_ultra_harvest.sh              # Script cron principal
├── monitor_ultra_harvest_production.py  # Monitoring automatique
/app/config/
├── crontab_production.conf              # Configuration cron complète
```

## ✅ AVANTAGES PRODUCTION

🎯 **Croissance automatique** : Base séries enrichie sans intervention  
🔍 **Découverte continue** : Nouvelles publications détectées  
🛡️ **Rate limiting** : Respectueux des limites Open Library  
📊 **Monitoring** : Alertes automatiques si problèmes  
🧹 **Maintenance** : Nettoyage logs/backups automatique  

## 🎯 NEXT STEPS

1. **Immédiat** : Tester scripts en staging
2. **Semaine 1** : Déployer cron job production  
3. **Semaine 2-4** : Optimiser selon métriques réelles

**✅ ULTRA HARVEST PERMANENT = CROISSANCE SÉRIES AUTOMATIQUE** 🚀