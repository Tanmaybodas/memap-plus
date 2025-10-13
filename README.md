# MeMap+ — Visual Digital Footprint & Impersonation Analyzer

MeMap+ is an AI-powered visual tool that maps a person’s digital footprint and detects possible impersonation by comparing social identities across platforms like Instagram, GitHub, Reddit, and Google mentions.

- Footprint Mode: Discover profiles across platforms and visualize connections.
- Comparison Mode: Compare two usernames to detect overlaps, similarities, and impersonation risk.

## Quick Start

Prereqs:
- Python 3.10 or 3.11
- Internet access

Setup:
```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
# Fast demo: embeddings disabled by default in .env
# Optionally fill API keys (see below)
```

Run:
```bash
streamlit run app.py
```

Open: http://localhost:8501

## Test Inputs

- Footprint Mode: octocat
- Comparison Mode: octocat vs 0ctocat (or yourhandle vs yourhandle_)

## Features

- Cross-platform mapping (GitHub, Reddit, Instagram, Google mentions)
- Comparison Mode for impersonation detection
- Visual graph (PyVis + NetworkX) with color-coded similarity edges
- AI/NLP similarity (RapidFuzz; optional sentence-transformers)
- Optional profile image similarity via perceptual hashing

## API Keys and .env

The app works out of the box with GitHub (unauthenticated). Optional keys unlock more sources:

```
# GitHub (optional for higher rate limits)
GITHUB_TOKEN=

# Reddit (required for Reddit data)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=MeMapPlus/0.1 by YOUR_REDDIT_USERNAME

# Google Custom Search (required for web mentions)
GOOGLE_CSE_ID=
GOOGLE_API_KEY=

# Instagram (optional login to improve reliability)
IG_USERNAME=
IG_PASSWORD=

# Feature toggles
ENABLE_EMBEDDINGS=false     # fast demo default
ENABLE_IMAGE_SIMILARITY=true
```

- Reddit keys: https://old.reddit.com/prefs/apps → create script app → copy client id/secret
- Google CSE: Create a Programmable Search Engine (entire web), enable Custom Search API, get API key and CX
- GitHub token: Settings → Developer settings → Personal access tokens (read:user)
- Instagram: Instaloader login optional; public data often works but can be rate-limited

## What Works Without Keys

- GitHub fetch + graphs
- Comparison Mode UI and similarity (fuzzy matching)
- GitHub avatar image similarity (if ENABLE_IMAGE_SIMILARITY=true)

## Docker

```bash
docker build -t memap-plus .
docker run -p 8501:8501 --env-file .env memap-plus
```

Open http://localhost:8501

## Project Structure

```
MeMapPlus/
├─ app.py
├─ requirements.txt
├─ .env.example
├─ .gitignore
├─ Dockerfile
├─ Makefile
├─ .streamlit/
│  └─ config.toml
├─ assets/
│  └─ logos/
│     └─ README.txt
├─ sample_data/
│  └─ example_profiles.json
├─ scripts/
│  ├─ setup.sh
│  └─ run.sh
└─ src/
   ├─ models/
   │  └─ types.py
   ├─ data/
   │  ├─ github_client.py
   │  ├─ reddit_client.py
   │  ├─ instagram_client.py
   │  └─ web_search.py
   ├─ similarity/
   │  ├─ text_similarity.py
   │  └─ image_similarity.py
   ├─ graph/
   │  └─ graph_builder.py
   └─ utils/
      └─ cache.py
```

## Demo Flow (2–3 min)

1) Footprint Mode: search “octocat” → show graph + mentions + exposure index.
2) Comparison Mode: “octocat” vs “0ctocat” → show similarity scores + risk level.
3) Close with privacy insights and next steps (face recognition, more platforms).