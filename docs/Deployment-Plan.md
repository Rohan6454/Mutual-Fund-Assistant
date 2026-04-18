# Production Deployment Plan

This document outlines the production architecture and deployment steps for the Mutual Fund FAQ Assistant. The application is divided into three execution environments:

## 1. Frontend (Next.js) ⚡ Vercel

The client-facing Chatbot and Library interfaces are built on Next.js and optimized for edges.

**Deployment Steps:**
1. Connect your GitHub repository to [Vercel](https://vercel.com).
2. Configure the **Root Directory** to `phase-6-frontend-ui`.
3. Vercel will automatically detect Next.js.
4. Set the Environment Variables:
   - `NEXT_PUBLIC_API_URL` = `<YOUR_RENDER_BACKEND_URL>`
5. Deploy. (Automatic preview deployments will trigger on every pull request).

## 2. Backend (FastAPI) ☁️ Render

The backend provides the API endpoints for chat orchestration and handles the Gemini LLM inference and Qdrant database communication.

**Deployment Steps:**
1. Connect your repository to [Render](https://render.com).
2. Create a new **Web Service**.
3. Set the **Root Directory** to `phase-5-backend-api` (or deploy from root but configure the start command).
4. **Environment**: Python 3
5. **Build Command**: `pip install -r ../requirements.txt`
6. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Define your secrets in Render's Environment Variables:
   - `GEMINI_API_KEY`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
8. Deploy.

## 3. Data Scheduler (Python) 🐙 GitHub Actions

The data scraping and embedding pipeline (`scheduler_service.py`) operates entirely asynchronously. It runs as a daily cron job to inject fresh schema data into Qdrant.

**Deployment Steps:**
1. The repository already contains a GitHub Action workflow file `.github/workflows/daily-ingest.yml`.
2. Navigate to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions**.
3. Add your production secrets:
   - `GEMINI_API_KEY`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
4. The GitHub Action is configured to run automatically at 03:45 UTC (09:15 AM IST). You can also run it manually from the "Actions" tab by clicking "Run Workflow".

---

## Post-Deployment Checklist

- [ ] Ensure Vercel `NEXT_PUBLIC_API_URL` is pointing directly to the generated Render URL (e.g., `https://mf-backend.onrender.com`).
- [ ] Verify Render backend health endpoint `/api/health` returns `200 OK`.
- [ ] Perform a manual run of the GitHub Action to verify Qdrant population.
- [ ] Test a query on the live Vercel frontend.
