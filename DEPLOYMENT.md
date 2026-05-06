# EcoCred Deployment

## Frontend: Vercel

Deploy the `frontend` directory as a Vite app.

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_BASE=https://your-backend-service.onrender.com`

After your backend has a real URL, set `VITE_API_BASE` to that URL and redeploy the frontend.

## Backend and ML service: Render

This repo includes `render.yaml` for a Render Blueprint with:

- `ecocred-backend`: Django API
- `ecocred-ml-service`: FastAPI ML service
- `ecocred-db`: Postgres database

In Render, create a new Blueprint from this repository. Render will ask for any `sync: false` secrets in `render.yaml`.

After Vercel gives you a frontend URL, update these Render environment variables:

- `CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app`
- `CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app`

After Render gives you an ML service URL, update this backend environment variable:

- `ML_SERVICE_URL=https://your-ml-service.onrender.com`

## Temporary public demo with a tunnel

Run the local servers, then expose them:

```powershell
npx localtunnel --port 5173
npx localtunnel --port 8000
```

Use the backend tunnel URL as `VITE_API_BASE` if you rebuild or restart the frontend for a demo.
