# Alchemist OS Deployment Guide

## 1. Local Deployment
1. Set up your `.env` based on `development.env`.
2. Run `pip install -r backend/requirements.txt`
3. Run `npm install` in frontend.
4. Run `uvicorn main:app --reload` for backend.
5. Run `npm run dev` for frontend.

## 2. Docker Deployment (Recommended)
1. Copy `production.env` to `.env` and fill in secrets.
2. Run `docker-compose up -d --build`.
3. The system is available at `http://localhost:3000` and `http://localhost:8000`.
4. Grafana metrics at `http://localhost:3001`

## 3. VPS Deployment
1. Install Docker and Docker Compose on the VPS.
2. Clone repository.
3. Configure `.env`.
4. Run `docker-compose up -d`.
5. Expose ports via Nginx or Apache reverse proxy for SSL.

## 4. Troubleshooting
- **Database Locked**: Ensure volumes are correctly mounted and permissions are correct.
- **Port Conflicts**: Change the ports in `docker-compose.yml`.
- **API Key Errors**: Ensure `GROQ_API_KEY` is set correctly.
