# Deployment to Render

This guide provides step-by-step instructions to deploy CallMood API to Render.

## Prerequisites

- GitHub account with access to https://github.com/DAIAGlobal/callmood
- Render account (https://render.com)
- PostgreSQL or Redis services (optional, can use Render Databases)

## Deployment Steps

### 1. Connect GitHub to Render

1. Go to https://dashboard.render.com
2. Click "New Web Service"
3. Select "Build and deploy from a Git repository"
4. Connect your GitHub account
5. Select repository: `DAIAGlobal/callmood`
6. Branch: `main`

### 2. Configure Web Service

**Basic Settings:**
- Name: `callmood-api`
- Runtime: `Python 3.13`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn src.backend.app.main:app --host 0.0.0.0 --port $PORT`

**Instance Type:**
- Select: `Free` or `Pro Plan` (Starter recommended for production)

### 3. Environment Variables

Add these environment variables in Render dashboard:

```
PYTHON_VERSION=3.13
SECRET_KEY=<generate-strong-random-key>
DATABASE_URL=postgresql://user:password@host:5432/callmood
REDIS_URL=redis://localhost:6379
STORAGE_DIR=/tmp/storage
ARTIFACTS_DIR=/tmp/artifacts
CONFIG_PATH=/app/config.yaml
```

**Option A: Using Render PostgreSQL**

1. Create PostgreSQL database in Render
2. Copy connection string as `DATABASE_URL`

**Option B: Use Existing PostgreSQL**

Replace with your PostgreSQL credentials.

### 4. Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Clone the repository
   - Install dependencies
   - Start the application
3. Wait for deployment to complete (2-5 minutes)
4. Access API at: `https://callmood-api.onrender.com`

### 5. Verify Deployment

Test the API health endpoint:

```bash
curl https://callmood-api.onrender.com/health
```

Expected response:
```json
{"status": "ok"}
```

Test analysis endpoint:

```bash
curl -X POST https://callmood-api.onrender.com/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "audio_in/llamada1.m4a",
    "level": "STANDARD"
  }'
```

### 6. Configure Database (if using Render PostgreSQL)

After creating PostgreSQL service in Render:

1. Copy the connection string
2. Add to Web Service environment variables as `DATABASE_URL`
3. Redeploy the web service

### 7. Auto-Deploy on Push

Render automatically deploys when you push to the `main` branch.

To trigger a redeploy:
```bash
git commit --allow-empty -m "Trigger redeploy"
git push origin main
```

## API Endpoints

After deployment, access these endpoints:

**Analysis:**
- `POST /api/v1/analyze` - Analyze audio file
- `POST /api/v1/analyze/upload` - Upload and analyze
- `GET /api/v1/analyze/levels` - Get level info
- `GET /api/v1/analyze/health` - Service health

**Health:**
- `GET /health` - API health check

## Monitoring

In Render dashboard, you can:
- View logs in real-time
- Monitor CPU and memory usage
- Check deployment history
- Manage environment variables
- Scale instance size

## Troubleshooting

### Build Fails

Check the build logs in Render dashboard. Common issues:
- Missing dependencies in `requirements.txt`
- Incompatible Python version
- Database connection issues

### Service Won't Start

Check logs for:
```
Error: Cannot import module
Error: Database connection failed
Error: Missing environment variable
```

### Slow Performance

If analysis requests timeout:
- Upgrade to a larger instance
- Check database performance
- Monitor memory usage

## Cost Estimation

Free Tier: $0/month (includes 750 hours)
Starter: $7-12/month
Standard: $12+ /month (recommended for production)

## Next Steps

1. Add GPU support (optional, requires paid plan)
2. Setup CI/CD pipeline
3. Add monitoring/alerting
4. Scale horizontally with load balancer
5. Setup custom domain

## Support

For Render support: https://render.com/docs
For CallMood issues: https://github.com/DAIAGlobal/callmood/issues
