# Thread Bot

Génère et envoie 3 threads tech/cybersec par email toutes les 44 minutes via GitHub Actions.

## Setup (5 étapes)

### 1. Crée le repo GitHub
- Nouveau repo privé, nom : `thread-bot`
- Upload les fichiers : `main.py` + `.github/workflows/thread-bot.yml`

### 2. Ajoute les secrets
Dans ton repo → Settings → Secrets and variables → Actions → New repository secret

| Nom | Valeur |
|---|---|
| `NEWS_API_KEY` | ta clé newsapi.org |
| `GEMINI_API_KEY` | ta clé aistudio.google.com |
| `GMAIL_USER` | elom.karl.patrick@gmail.com |
| `GMAIL_APP_PASSWORD` | ton app password 16 caractères |

### 3. Active GitHub Actions
Onglet Actions → Enable

### 4. Test manuel
Actions → Thread Bot → Run workflow

### 5. Vérifie ta boîte mail
Email reçu = tout marche. Le bot tourne ensuite automatiquement toutes les 44 min.
