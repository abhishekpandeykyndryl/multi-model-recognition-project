# Azure MFA Multiagent Demo

This repository demonstrates a Multi-Factor Authentication system using Azure Face + Azure Speaker Verification + Password.

See `backend_fastapi/` for the recommended async implementation.

## Quickstart (local, FastAPI)
1. Copy `.env.example` to `.env` and set your Azure keys & endpoints
2. From `backend_fastapi/` run:
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8080
   ```
3. Open `frontend/index.html` (serve static file) and point API base to `http://localhost:8080`
