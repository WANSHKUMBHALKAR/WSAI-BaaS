FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.prod.txt ./requirements.prod.txt
RUN pip install --no-cache-dir -r requirements.prod.txt

COPY . .

RUN chmod +x /app/entrypoint.sh || true

# Use entrypoint script; migrations only run when RUN_MIGRATIONS=true
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
