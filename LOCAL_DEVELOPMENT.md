Local development

1. Copy `.env.example` to `.env` and edit values.
2. Start services with Docker Compose:

```bash
docker-compose up --build
```

3. The backend will be available at `http://localhost:8000` and frontend at `http://localhost:3000`.
4. To run tests locally:

```bash
cd backend
pip install -r requirements.txt
pytest -q
```
