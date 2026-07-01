# TrustLens Deployment Guide

## Local Setup

To set up TrustLens locally:
1. Clone the repository.
2. Ensure you have Python 3.11+, Node.js 18+, and PostgreSQL installed.
3. Configure the environment variables as documented below.

**Note:** The root `docker-compose.yml` is specifically provided for local infrastructure/dev container setup. You can run `docker compose up -d` to spin up a local PostgreSQL database and the backend API quickly.

## PostgreSQL Setup

1. Create a local PostgreSQL database:
   ```sql
   CREATE DATABASE trustlens_db;
   CREATE USER trustlens WITH ENCRYPTED PASSWORD 'trustlens_password';
   GRANT ALL PRIVILEGES ON DATABASE trustlens_db TO trustlens;
   ```

## Environment Variables

Copy `.env.example` files to `.env` and fill in appropriate values.

### Backend (`backend/.env`)
* `APP_NAME`: Name of the application (e.g., TrustLens)
* `APP_ENV`: Environment (development/staging/production)
* `API_V1_PREFIX`: API prefix (e.g., `/api/v1`)
* `DATABASE_URL`: PostgreSQL connection string
* `JWT_SECRET_KEY`: Secret key for JWT tokens
* `JWT_ALGORITHM`: JWT Algorithm (e.g., HS256)
* `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiry time in minutes
* `REFRESH_TOKEN_EXPIRE_DAYS`: Expiry time in days
* `UPLOAD_DIR`: Directory for file uploads
* `REPORT_DIR`: Directory for reports
* `MAX_FILE_SIZE_MB`: Max file upload size
* `CORS_ORIGINS`: Allowed CORS origins

### Frontend (`frontend/.env`)
* `VITE_API_BASE_URL`: URL of the backend API (e.g., `https://api.trustlens.example.com/api/v1`)

## Backend Deployment

1. Set up a production PostgreSQL database.
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Run Alembic migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```
4. Start the application using an ASGI server like Uvicorn or Gunicorn:
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

**Important:** For production backend deployment, ensure you inject `DATABASE_URL` and `JWT_SECRET_KEY` from your hosting provider's environment variables (e.g., AWS Secrets Manager, Render env settings, etc.).

## Frontend Deployment

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Build the production assets:
   ```bash
   npm run build
   ```
3. Deploy the `dist/` directory to a static hosting service.

**Important:** For frontend deployment (e.g., using Vercel, Netlify), you must define the Vercel env variable in the platform dashboard:
`VITE_API_BASE_URL=https://your-backend-url/api/v1`

## Health Checks

After deployment, you can verify backend readiness using:
* Health Check Endpoint: `GET /api/v1/health`
* Version Endpoint: `GET /api/v1/version`

## Common Deployment Errors

* **Database Connection Failed**: Ensure `DATABASE_URL` is correctly formatted and the database server is accessible.
* **CORS Errors**: Verify that `CORS_ORIGINS` includes the exact URL of your deployed frontend.
* **JWT Missing**: Ensure `JWT_SECRET_KEY` is set securely.

## Troubleshooting

* If backend migrations fail, check `alembic.ini` configuration and verify `DATABASE_URL`.
* If frontend cannot connect to backend, check `VITE_API_BASE_URL` in the frontend build environment.
