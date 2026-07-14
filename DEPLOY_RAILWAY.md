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
