#!/bin/bash
echo "=== $(date) - Performance Monitor ==="
echo "Mémoire:"
free -h | grep Mem
echo "Top 3 processus par mémoire:"
ps aux --sort=-%mem | head -4
echo "Espace disque:"
df -h /app
echo "================================"
