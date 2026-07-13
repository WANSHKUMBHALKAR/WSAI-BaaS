# WSAI BaaS - AI Backend-as-a-Service

WSAI BaaS is an open-source AI Backend-as-a-Service platform that enables developers to rapidly build AI applications with authentication, memory, RAG, agent workflows, MCP support, multi-LLM integration, file storage, vector search, and API management.

## Tech Stack
- **Backend**: FastAPI, Python 3.12, PostgreSQL, Redis, Qdrant, Celery
- **Frontend**: Next.js 15, React, TailwindCSS, shadcn/ui
- **Infrastructure**: Docker, Docker Compose, GitHub Actions

## Features
- **Authentication**: JWT-based auth, user management
- **Workspace System**: Organizations, Projects, API Keys
- **AI Gateway**: Unified API for LLMs (OpenAI, Gemini, Claude, etc.)
- **Agent Framework**: Stateful agents with system prompts and memory
- **RAG & Memory**: Document processing, vector search via Qdrant
- **MCP Support**: Dynamic tool loading and agent execution

## Getting Started

### Prerequisites
- Docker and Docker Compose
- API Keys for the models you want to use (OpenAI, Gemini, etc.)

### Setup

1. Clone the repository
2. Navigate to the `deployment/docker` directory
3. Copy the example `.env` file (if available) and fill in your keys
4. Run Docker Compose:

```bash
cd deployment/docker
docker-compose up --build
```

### Accessing the Platform
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/api/v1/openapi.json

## Folder Structure
- `/backend`: The Python FastAPI backend
- `/frontend`: The Next.js dashboard
- `/deployment`: Docker configurations
- `/sdk`: Future SDKs for Python/JS
