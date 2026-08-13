# Comic Metaphor Engine

Map real-world problems to comic book storylines — scored, explained, and turned into
podcasts, lessons, and dialogue scripts. Part of the Overlay Writing pillar.

## What it does

- **Metaphor library**: 6+ curated protocols (Armor Wars, Secret Invasion, Days of Future
  Past, Planet Hulk, ...) covering ownership, trust, control, and avoidance risks, scored
  with a deterministic codex engine (Trueness / Flow / PCS / RPS / CU).
- **Semantic search**: FAISS + MiniLM embeddings over the protocol library.
- **Generation**: podcast monologues, marketing copy, dialogue scripts, and plain-language
  lessons from any topic.
- **Comic uploads (Creator plan, $1/mo)**: upload your own comic (PDF/TXT/MD/EPUB) and get
  an insight report — extracted storylines mapped to real-world lessons with scored metaphors,
  takeaways, and action items.

## Stack

- Backend: Python 3.11 / FastAPI (Vercel serverless via `a2wsgi`), Supabase (Auth + Postgres
  + Storage), Stripe Checkout + Customer Portal.
- Frontend: React 18 / Vite / TypeScript / zustand / Tailwind (`ui-v2/`).

## Quick start (dev mode)

No env vars needed — without Supabase/Stripe keys the backend runs in dev mode
(everyone is a `creator`, uploads + insights work locally).

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

cd ui-v2
npm install
npm run dev
```

## Tests

```bash
python -m pytest tests/ -q --ignore=backups   # backend
cd ui-v2 && npm run test                        # frontend
```

## Production setup

See `SETUP_SAAS.md` for the Supabase schema, Stripe product/price/webhook, and Vercel
deployment runbook. Repo: https://github.com/ncsound919/Comic-Metaphor-Engine
