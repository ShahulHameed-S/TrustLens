# TrustLens

## Description
TrustLens is a comprehensive platform for automated content verification, deepfake detection, metadata forensics, and blockchain-based audit logging. It provides robust tools to establish trust in digital media.

## Features
- AI-based Deepfake Detection
- Metadata Extraction & Forensics
- Digital Content Verification
- Blockchain Audit Trails
- Comprehensive Trust Scoring

## Tech Stack
- **Backend:** FastAPI (Python), PostgreSQL, SQLAlchemy, Alembic, Pytest
- **Frontend:** React, TypeScript, Vite, Tailwind CSS (optional)
- **Database:** PostgreSQL

## Architecture Overview
The system follows a monolithic backend with modular service-based architecture, exposing a RESTful API built with FastAPI. The frontend is a Single Page Application (SPA) communicating with the backend API.

## Environment Variables
Environment variables are managed through `.env` files. See `.env.example` in the root, `backend/`, and `frontend/` directories for reference.

### Key Variables
* `DATABASE_URL`: Connection string to PostgreSQL
* `JWT_SECRET_KEY`: Secret for signing tokens
* `VITE_API_BASE_URL`: Frontend configuration for API URL

## Backend Setup
1. `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment.
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `alembic upgrade head`

## Frontend Setup
1. `cd frontend`
2. Install dependencies: `npm install`

## Running Locally
**Backend:**
```bash
cd backend
uvicorn app.main:app --reload
```
**Frontend:**
```bash
cd frontend
npm run dev
```

## Testing
Run backend tests using Pytest:
```bash
cd backend
pytest
```

## Deployment Overview
Deployment involves building the frontend static assets and hosting them via a CDN/static host, while deploying the backend FastAPI application behind an ASGI server (like Uvicorn + Gunicorn) connecting to a managed PostgreSQL database. See `docs/10_Deployment/Deployment_Guide.md` for full details.

## API Docs
When the backend is running locally, API documentation is available at:
* Swagger UI: http://localhost:8000/api/v1/openapi.json (or `/docs`)

## Author
Developed for TrustLens.
