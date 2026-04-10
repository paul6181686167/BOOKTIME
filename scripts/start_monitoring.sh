#!/bin/bash
# Démarre la surveillance en arrière-plan

PID_FILE="/var/run/booktime_monitor.pid"

# Vérifier si déjà en cours
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "Surveillance déjà active (PID: $(cat $PID_FILE))"
    exit 0
fi

# Démarrer en arrière-plan
nohup /app/scripts/monitor_daemon.sh >/dev/null 2>&1 &
echo $! > "$PID_FILE"

echo "Surveillance démarrée (PID: $(cat $PID_FILE))"
