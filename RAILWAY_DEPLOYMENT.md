# Railway Deployment Guide

This guide explains how to deploy CineMatch to Railway with PostgreSQL.

## Prerequisites

1. A Railway account (https://railway.app)
2. Railway CLI installed (`npm i -g @railway/cli`)
3. Your API keys ready:
   - TMDB API Key (required for movie data)
   - At least one AI API key (OpenAI, Anthropic, or Google)
   - Supabase credentials (optional, for cloud sync)

## Deployment Steps

### Step 1: Create Railway Project

```bash
# Login to Railway
railway login

# Create a new project
railway init
```

### Step 2: Add PostgreSQL Database

1. Go to your Railway project dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Railway will automatically create a `DATABASE_URL` variable

### Step 3: Deploy Backend

```bash
cd backend

# Link to Railway project
railway link

# Deploy
railway up
```

**Set Backend Environment Variables** in Railway Dashboard:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Auto-set by Railway PostgreSQL |
| `SECRET_KEY` | Generate: `openssl rand -hex 32` |
| `DEBUG` | `false` |
| `TMDB_API_KEY` | Your TMDB API key |
| `OPENAI_API_KEY` | OpenAI API key (optional) |
| `ANTHROPIC_API_KEY` | Anthropic API key (optional) |
| `GOOGLE_API_KEY` | Google AI API key (optional) |
| `FRONTEND_URL` | Your frontend URL (set after deploying frontend) |
| `SUPABASE_URL` | Supabase project URL (optional) |
| `SUPABASE_KEY` | Supabase anon key (optional) |
| `SUPABASE_SECRET_KEY` | Supabase service role key (optional) |

### Step 4: Deploy Frontend

```bash
cd frontend

# Create a new Railway service in the same project
railway link

# Set the API URL build argument
railway variables set VITE_API_URL=https://your-backend-url.railway.app/api

# Deploy
railway up
```

### Step 5: Configure CORS

After both services are deployed:

1. Copy your frontend Railway URL (e.g., `https://cinematch-frontend.railway.app`)
2. Go to backend service → Variables
3. Set `FRONTEND_URL` to your frontend URL
4. Redeploy backend: `railway up` in backend directory

## Alternative: Deploy via GitHub

1. Push your code to GitHub
2. In Railway Dashboard:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect the Dockerfile

For monorepo deployment:
- Create two services pointing to the same repo
- Set root directory to `backend` for backend service
- Set root directory to `frontend` for frontend service

## Environment Variables Summary

### Backend (.env or Railway Variables)

```env
# Required
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=your-secret-key-min-32-chars
TMDB_API_KEY=your-tmdb-api-key

# AI APIs (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Production
DEBUG=false
FRONTEND_URL=https://your-frontend.railway.app

# Optional - Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SECRET_KEY=your-service-role-key
```

### Frontend (Build-time Variables)

```env
VITE_API_URL=https://your-backend.railway.app/api
```

## Database Migration

The app auto-creates tables on startup via SQLAlchemy. For production:

1. Tables are created automatically when backend starts
2. To seed movies, you can run the seed script locally pointing to production DB
3. Or create a one-time job in Railway to run the seed

## Custom Domain (Optional)

1. Go to service Settings → Networking → Custom Domain
2. Add your domain
3. Configure DNS as instructed by Railway
4. Update `FRONTEND_URL` in backend if using custom domain for frontend

## Monitoring

- Railway provides built-in logs: Dashboard → Service → Deployments → View Logs
- Health check endpoint: `GET /health`
- API status: `GET /api/status`

## Costs

Railway offers:
- $5/month free credit (Hobby plan)
- Pay-as-you-go pricing for usage beyond free tier
- PostgreSQL included in compute costs

## Troubleshooting

### CORS Errors
- Ensure `FRONTEND_URL` is set correctly in backend
- Check Railway logs for the CORS origins being used

### Database Connection Issues
- Verify `DATABASE_URL` is set by Railway PostgreSQL
- Check if PostgreSQL service is running

### Build Failures
- Check Dockerfile syntax
- Ensure all dependencies are in requirements.txt / package.json
- View build logs in Railway dashboard

### API Timeouts
- The recommendation ensemble has a 45-second timeout
- Consider upgrading Railway plan for more resources if needed
