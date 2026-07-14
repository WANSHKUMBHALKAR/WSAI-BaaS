# Deploying to Railway (config-only)

This repository contains configuration and a GitHub Actions workflow to deploy the backend and frontend to Railway. The workflow is intentionally configuration-first: it will not run until you provide Railway credentials in GitHub Secrets.

What this repo provides
- `railway.json` — Informational description of services and required environment variables.
- `.github/workflows/deploy_to_railway.yml` — A GitHub Actions workflow that uses the `railwayapp/railway-deploy` action to deploy the `backend` service and (optionally) run Alembic migrations.

Pre-requisites
- A Railway account (https://railway.app).
- Admin access to this GitHub repository to add repository secrets.

Required GitHub repository secrets
- `RAILWAY_API_KEY` — Your Railway API token.
- `RAILWAY_PROJECT_ID` — The Railway project id (found in the Railway project settings).

Optional secrets for automated migrations
- `RUN_MIGRATIONS` — set to `true` to run Alembic migrations as part of the workflow.
- `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT` — used by Alembic when `RUN_MIGRATIONS=true`.

Required runtime environment variables for the backend
Copy the variables below into Railway's environment settings for the backend service (or set them as project-level variables):

```
ENVIRONMENT=production
SECRET_KEY=<strong-secret>
POSTGRES_SERVER=<host>
POSTGRES_USER=<user>
POSTGRES_PASSWORD=<password>
POSTGRES_DB=<db>
POSTGRES_PORT=5432
REDIS_URL=<redis://...>
QDRANT_URL=<qdrant-host>
QDRANT_API_KEY=<optional>
OPENAI_API_KEY=<optional>
GEMINI_API_KEY=<optional>
CLAUDE_API_KEY=<optional>
OLLAMA_BASE_URL=<optional>
NEXT_PUBLIC_API_URL=https://<your-backend>/api/v1
```

How to connect and deploy (high level)
1. In Railway, create a new project and connect your GitHub repository (WSAI-BaaS).
2. Create two services: a `backend` service using the `./backend` Dockerfile and a `frontend` service using the `./frontend` Dockerfile (the `railway.json` lists these paths).
3. Add the environment variables listed above to the Railway project or service.
4. In your GitHub repository, add the secrets `RAILWAY_API_KEY` and `RAILWAY_PROJECT_ID` (and optionally `RUN_MIGRATIONS` and the `POSTGRES_*` secrets) under Settings → Secrets and variables → Actions.
5. Push to `main` or open a PR targeting `main`. The workflow `.github/workflows/deploy_to_railway.yml` will run on pushes to `main` and deploy the backend.

Notes and recommendations
- The workflow is configured to run Alembic migrations only when `RUN_MIGRATIONS` is set to `true` and the `POSTGRES_*` secrets are provided. This avoids accidental migrations without explicit consent.
- If you prefer to run migrations as a controlled one-off, leave `RUN_MIGRATIONS` unset and use Railway's console to execute `alembic upgrade head` inside the backend container.
- Do not store secrets in the repository. Use Railway's environment variables and GitHub Secrets.

Post-deploy checks
- Health: `https://<your-backend>/health`
- Readiness: `https://<your-backend>/ready`
- Liveness: `https://<your-backend>/live`

If you'd like, I can also:
- Create a separate workflow that builds and publishes the backend image to GHCR, then triggers Railway deployment using the GHCR image.
- Add a one-click script to bootstrap a Railway project using the Railway CLI (requires installing Railway CLI and authenticating).
Railway deployment guide

1. Build & publish image
- Push to `main`; GitHub Actions will publish the backend image to GHCR as `ghcr.io/<owner>/<repo>-backend:latest`.

2. Create a new Railway service
- In Railway, create a new service and choose `Deploy from Container Registry`.
- Select `GitHub Container Registry` and connect your GitHub account if prompted.
- Choose the image `ghcr.io/<owner>/<repo>-backend:latest`.

3. Configure environment variables
- Add the same environment variables you use locally. At minimum:
  - `DATABASE_URL` (Postgres)
  - `SECRET_KEY`
  - `OPENAI_API_KEY` (or other provider keys)
  - `REDIS_URL` (if used)
  - `QDRANT_URL` / `QDRANT_API_KEY` (if used)

4. (Optional) Run migrations
- Railway allows running one-off tasks. Use `alembic upgrade head` in the container to run migrations.

5. Healthchecks & scaling
- Add a healthcheck endpoint path `/health` (if not present) and configure Railway to use it.
- Set service instance size and scale rules based on traffic.

6. Notes
- For staging, tag images like `:staging` and configure Railway to pull that tag instead.
- If you prefer, configure automated deploys from GHCR on image push.
