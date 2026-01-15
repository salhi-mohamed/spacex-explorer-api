# ------------------------------
# Étape 1 : installer les dépendances
# ------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Copier le fichier requirements et installer les packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------
# Étape 2 : créer l'image finale
# ------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copier les packages installés depuis l'étape builder
COPY --from=builder /usr/local /usr/local

# Copier le code de l'API
COPY app/ app/

# Exposer le port utilisé par FastAPI
EXPOSE 8000

# Commande pour démarrer l'API sur toutes les interfaces
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
