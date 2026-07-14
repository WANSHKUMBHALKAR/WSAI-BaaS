# Deploying to Vercel (Frontend) — Quick Guide

This repository is a monorepo with a Next.js frontend in `frontend/` and a Python FastAPI backend in `backend/`.

Recommended approach (fastest for today):

- Deploy the **frontend** to Vercel (GUI). Set `NEXT_PUBLIC_API_URL` to point to your backend API (hosted elsewhere), or to Vercel backend service if you configure it.
- Deploy the **backend** to a Python-capable host (Render, Railway, Fly, or Docker on cloud). Vercel's Python support is limited; using a dedicated host is more reliable.

Steps — Frontend on Vercel:

1. Push your repo to GitHub (if not already).
2. Go to Vercel dashboard → "New Project" → Import Git Repository.
3. For the project root, Vercel should detect the `frontend/` Next.js app automatically. If using monorepo import, set up the `frontend` service or configure the Root to `frontend`.
4. In Project Settings → Environment Variables add:
   - `NEXT_PUBLIC_API_URL` = `https://your-backend.example.com/api/v1` (or your Vercel backend service URL)
   - Any LLM keys used by the frontend (if applicable). NOTE: Client-side keys must be prefixed with `NEXT_PUBLIC_` — avoid exposing secret keys in the browser.
5. Leave the Build Command as `npm run build` (or `pnpm build`), and the Output Directory blank for Next.js.
6. Deploy — Vercel will build and publish the frontend.

Backend options:

- If you want the backend on Vercel, you'll need to configure a Python serverless entrypoint and ensure Vercel's Platforms features support your stack. This project uses FastAPI in `backend/app/main.py` and likely expects a long-running server; deploying to Render/Railway is easier.
- Required environment variables for the backend (see `backend/app/core/config.py`):
  - `SECRET_KEY`
  - `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`
  - `REDIS_URL`
  - `QDRANT_HOST`, `QDRANT_PORT`
  - `OPENAI_API_KEY`, `GEMINI_API_KEY`, `CLAUDE_API_KEY`, `OLLAMA_BASE_URL` (as needed)

Local test command examples:

```powershell
cd frontend
npm install
npm run build

cd ..\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Notes & next steps I can take for you:

- Add Vercel project settings JSON or `vercel.json` (already added) for monorepo routing.
- Create lightweight serverless wrappers if you prefer backend on Vercel (experimental).
- Automate CI to set `NEXT_PUBLIC_API_URL` per environment.

Tell me whether you want me to deploy only the frontend to Vercel now (I'll prepare the repo and instructions), or also prepare the backend for deployment to Render/Railway.
