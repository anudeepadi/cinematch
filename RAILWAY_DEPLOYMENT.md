# Railway Deployment Guide

This guide explains how to deploy CineMatch to Railway using Supabase as the database.

## Prerequisites

1. A Railway account (https://railway.app)
2. Railway CLI installed (`npm i -g @railway/cli`)
3. A Supabase project (https://supabase.com) - this is your database
4. Your API keys ready:
   - TMDB API Key (required for movie data)
   - At least one AI API key (OpenAI, Anthropic, or Google)
   - Supabase credentials (required)

## Deployment Steps

### Step 1: Set Up Supabase Database

1. Go to https://supabase.com and create a project (or use existing)
2. Go to **Settings → Database → Connection string** (URI tab)
3. Copy the connection string - it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
4. Save this as `SUPABASE_DB_URL`

### Step 2: Migrate Local Data to Supabase

Before deploying, migrate your local SQLite data to Supabase:

```bash
cd backend

# Add SUPABASE_DB_URL to your .env file
echo 'SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres' >> .env

# Run migration script
source venv/bin/activate
python scripts/migrate_to_supabase.py
```

### Step 3: Create Railway Project

```bash
# Login to Railway
railway login

# Create a new project
railway init
```

### Step 4: Deploy Backend

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
| `SUPABASE_DB_URL` | PostgreSQL connection string from Supabase |
| `SECRET_KEY` | Generate: `openssl rand -hex 32` |
| `DEBUG` | `false` |
| `TMDB_API_KEY` | Your TMDB API key |
| `OPENAI_API_KEY` | OpenAI API key (optional) |
| `ANTHROPIC_API_KEY` | Anthropic API key (optional) |
| `GOOGLE_API_KEY` | Google AI API key (optional) |
| `FRONTEND_URL` | Your frontend URL (set after deploying frontend) |
| `SUPABASE_URL` | Supabase project URL (for API access) |
| `SUPABASE_KEY` | Supabase anon key |
| `SUPABASE_SECRET_KEY` | Supabase service role key |

### Step 5: Deploy Frontend

```bash
cd frontend

# Create a new Railway service in the same project
railway link

# Set the API URL build argument
railway variables set VITE_API_URL=https://your-backend-url.railway.app/api

# Deploy
railway up
```

### Step 6: Configure CORS

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
# Database - Supabase PostgreSQL (REQUIRED)
SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# Security (REQUIRED)
SECRET_KEY=your-secret-key-min-32-chars

# TMDB (REQUIRED for movie data)
TMDB_API_KEY=your-tmdb-api-key

# AI APIs (at least one required for recommendations)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Production settings
DEBUG=false
FRONTEND_URL=https://your-frontend.railway.app

# Supabase API access (for real-time sync features)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SECRET_KEY=your-service-role-key
```

### Frontend (Build-time Variables)

```env
VITE_API_URL=https://your-backend.railway.app/api
```

## Database Migration

Use the migration script to transfer your local data to Supabase:

```bash
cd backend
source venv/bin/activate
python scripts/migrate_to_supabase.py
```

This script:
1. Reads all data from local SQLite (users, movies, interactions, preferences)
2. Creates tables in Supabase PostgreSQL
3. Inserts all data with proper ID sequences
4. Verifies migration success

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

- **Railway**: $5/month free credit (Hobby plan), pay-as-you-go after
- **Supabase**: Free tier includes 500MB database, 1GB file storage

## Troubleshooting

### CORS Errors
- Ensure `FRONTEND_URL` is set correctly in backend
- Check Railway logs for the CORS origins being used

### Database Connection Issues
- Verify `SUPABASE_DB_URL` is set correctly
- Check Supabase dashboard for connection status
- Ensure your IP isn't blocked (Supabase allows all IPs by default)

### Build Failures
- Check Dockerfile syntax
- Ensure all dependencies are in requirements.txt / package.json
- View build logs in Railway dashboard

### API Timeouts
- The recommendation ensemble has a 45-second timeout
- Consider upgrading Railway plan for more resources if needed

### Migration Issues
- Ensure `SUPABASE_DB_URL` is set in `.env` before running migration
- Check that SQLite database exists at `backend/cinematch.db`
