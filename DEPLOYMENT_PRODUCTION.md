**Deployment Guide (Vercel frontend, Railway backend)**

- Frontend: deploy the `frontend/` folder to Vercel. Configure environment variables in Vercel dashboard matching `.env.example` (only frontend-relevant keys like `NEXT_PUBLIC_API_URL`).
- Backend: use Railway to deploy the backend container from GHCR or from Dockerfile.

Steps (recommended):
1. Push code to `main` branch. CI will run lint, tests, migrations, and build the backend image.
2. CI publishes backend image to GHCR `ghcr.io/<owner>/<repo>-backend:latest`.
3. In Railway, create a new project and choose `Deploy from Container Registry`.
4. Select the GHCR image above or connect to GitHub and set up deployment from main branch.
5. Set environment variables on Railway (see `.env.example`).
6. Configure health checks in Railway: use `/ready` for readiness and `/live` for liveness.

Database: create a Neon Postgres instance and set `DATABASE_URL` accordingly.
Redis: create Upstash Redis and set `REDIS_URL`.
Vector DB: create Qdrant Cloud and set `QDRANT_URL` and `QDRANT_API_KEY`.

Notes:
- Ensure `SECRET_KEY` is set in production.
- Use Railway one-off tasks to run `alembic upgrade head` when needed.
