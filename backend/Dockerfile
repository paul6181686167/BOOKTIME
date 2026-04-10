# Dockerfile pour déploiement Railway
FROM python:3.11-slim

# Variables environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Répertoire de travail
WORKDIR /app

# Installation dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation requirements Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Port exposé (dynamique via $PORT Railway)
EXPOSE 8001

# Commande de démarrage avec gestion robuste du port Railway
CMD ["python", "start.py"]