# EcoCred Deployment

## One-click Render deployment

Use the Deploy to Render button in `README.md`, or open this URL:

https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FShilpi0620%2Fecocred%2Ftree%2Fmain

The Blueprint deploys:

- `ecocred-frontend`: Vite static site
- `ecocred-backend`: Django API
- `ecocred-ml-service`: FastAPI ML service
- `ecocred-db`: Postgres database

Expected public URLs:

- Frontend: `https://ecocred-frontend.onrender.com`
- Backend: `https://ecocred-backend.onrender.com`
- ML service: `https://ecocred-ml-service.onrender.com`

If Render assigns a different subdomain during setup, update these environment variables and redeploy:

- Frontend service: `VITE_API_BASE`
- Backend service: `CORS_ALLOWED_ORIGINS`
- Backend service: `CSRF_TRUSTED_ORIGINS`
- Backend service: `ML_SERVICE_URL`

## Temporary public demo with a tunnel

Run the local servers, then expose them:

```powershell
npx localtunnel --port 5173
npx localtunnel --port 8000
```

Use the backend tunnel URL as `VITE_API_BASE` if you rebuild or restart the frontend for a demo.
