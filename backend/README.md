u# PromptHub Backend

API REST complète pour la plateforme PromptHub : partage de prompts, votes, forum d'entraide et test en direct de modèles LLM (OpenAI / Claude / Gemini).

## Stack technique

- **FastAPI** + **Uvicorn**
- **SQLAlchemy 2.0** + **PostgreSQL** (Alembic pour les migrations)
- **Pydantic v2** pour la validation
- **JWT** (python-jose) pour l'authentification
- **Fernet** (cryptography) pour le chiffrement des clés API utilisateurs
- **httpx** pour les appels asynchrones aux providers LLM

## Structure

```
app/
├── api/
│   ├── v1/
│   │   ├── endpoints/      # auth, users, prompts, requests, playground, admin
│   │   └── router.py       # Agrégateur des routes v1
│   └── deps.py             # get_db, get_current_user, get_current_admin
├── core/                   # config, database, security, encryption
├── crud/                   # Couche d'abstraction BDD
├── models/                 # user, prompt, request, comment, vote
├── schemas/                # Schémas Pydantic (entrées/sorties)
├── services/               # llm_service, moderation
└── main.py                 # Point d'entrée FastAPI
```

## Démarrage rapide

### 1. Avec Docker (PostgreSQL + API)

```bash
docker compose up --build
```

### 2. En local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Base de données PostgreSQL
createdb prompthub

cp .env.example .env
alembic upgrade head

uvicorn app.main:app --reload
```

### 3. Frontend React / Vite

```bash
cd frontend
cp .env.example .env
npm install --legacy-peer-deps
npm run dev -- --host 0.0.0.0
```

Le frontend pointe par défaut sur l’API backend : http://localhost:8000/api/v1

Documentation interactive : http://localhost:8000/docs

## Endpoints principaux

| Méthode | Route | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Inscription |
| POST | `/api/v1/auth/login` | Connexion (form OAuth2) |
| POST | `/api/v1/auth/refresh` | Rafraîchir le token |
| GET/PUT | `/api/v1/users/me` | Profil courant |
| PUT | `/api/v1/users/me/api-keys/{provider}` | Enregistrer une clé API (chiffrée) |
| GET | `/api/v1/prompts` | Liste des prompts (recherche, tags, pagination) |
| POST | `/api/v1/prompts` | Créer un prompt |
| POST | `/api/v1/prompts/{id}/vote` | Voter (+1/-1) |
| POST | `/api/v1/prompts/{id}/comments` | Commenter |
| GET | `/api/v1/requests` | Forum / entraide |
| POST | `/api/v1/playground` | Tester un LLM (clé utilisateur) |
| POST | `/api/v1/playground/stream` | Streaming SSE de la réponse |
| GET | `/api/v1/admin/stats` | Statistiques (admin) |

## Sécurité

- Mots de passe hachés avec **bcrypt**
- Clés API utilisateurs chiffrées avec **Fernet** avant stockage (`encryption.py`)
- Modération automatique du contenu (`services/moderation.py`)
- Routeurs admin protégés (`get_current_admin`)

## Tests

```bash
pytest
```
