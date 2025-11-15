# 🚀 Render Deployment Guide for Healthcare Chatbot Backend

This guide will walk you through deploying your FastAPI backend to Render as a Web Service.

---

## 📋 Prerequisites

Before deploying, ensure you have:
- ✅ A Render account (sign up at [render.com](https://render.com))
- ✅ Your GitHub repository connected to Render
- ✅ All external services configured (PostgreSQL, Neo4j, Redis, OpenAI)

---

## 🔧 Step 1: Create Procfile

Render needs a `Procfile` to know how to start your application. Create this file in the **root** of your repository:

**File: `Procfile`** (in project root)
```
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 2
```

> **Note**: Render automatically sets the `$PORT` environment variable. The `--workers 2` flag enables multiple worker processes for better performance.

---

## 📝 Step 2: Create render.yaml (Optional but Recommended)

For better configuration management, create a `render.yaml` file in the root:

**File: `render.yaml`** (in project root)
```yaml
services:
  - type: web
    name: healthcare-chatbot-api
    env: python
    buildCommand: pip install -r api/requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 2
    plan: starter  # or free, starter, standard, pro
    envVars:
      - key: ENVIRONMENT
        value: production
```

---

## 🌐 Step 3: Deploy on Render Dashboard

### 3.1 Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select your `healthcare-chatbot` repository

### 3.2 Configure Service Settings

Fill in the following details:

#### **Basic Settings:**

| Field | Value |
|-------|-------|
| **Name** | `healthcare-chatbot-api` (or your preferred name) |
| **Region** | Choose closest to your users (e.g., `Oregon (US West)`) |
| **Branch** | `main` (or your default branch) |
| **Root Directory** | Leave empty (or set to `api` if you want) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r api/requirements.txt` |
| **Start Command** | `uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 2` |

> **Important**: 
> - If you set **Root Directory** to `api`, adjust paths accordingly
> - The `$PORT` variable is automatically provided by Render
> - Use `--workers 2` for better performance (adjust based on your plan)

#### **Plan Selection:**

- **Free**: Good for testing, but has limitations (spins down after inactivity)
- **Starter ($7/month)**: Better for production, always-on
- **Standard ($25/month)**: Recommended for production with higher traffic

---

## 🔐 Step 4: Configure Environment Variables

In the Render dashboard, go to your service → **"Environment"** tab and add the following variables:

### **Required Environment Variables:**

#### 🗄️ Database Configuration
```
DATABASE_URL=postgresql://user:password@host:port/database
```
or
```
NEON_DB_URL=postgresql://user:password@host:port/database
```
> **Note**: Use your PostgreSQL connection string (NeonDB, Supabase, or Render PostgreSQL)

#### 🤖 OpenAI Configuration
```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

#### 🔐 JWT Authentication
```
JWT_SECRET_KEY=your-very-secure-random-secret-key-here
```
> **Tip**: Generate a secure key using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

#### 🕸️ Neo4j Configuration (Optional - has fallback)
```
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=neo4j
NEO4J_TRUST_ALL_CERTS=false
```

#### ⚡ Redis Configuration (Optional - for caching)
**Option 1: Upstash Redis (Recommended)**
```
UPSTASH_REDIS_REST_URL=https://your-redis-url.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-token
```

**Option 2: Standard Redis**
```
REDIS_URI=redis://user:password@host:port
```
or
```
REDIS_URI=rediss://user:password@host:port  # For SSL/TLS
```

#### 🌐 CORS Configuration
```
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```
> **Important**: Replace with your actual frontend domain(s). For local testing, you can include `http://localhost:3000`

#### ⚙️ Application Configuration
```
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=10000  # Render sets this automatically, but you can override
```

#### 🚦 Rate Limiting (Optional)
```
RATE_LIMIT=30          # Requests per window
RATE_WINDOW=60         # Window in seconds
DISABLE_RATE_LIMIT=0  # Set to 1 to disable
```

#### 💾 Cache Configuration (Optional)
```
ENABLE_CACHE=1
CACHE_TTL_SECONDS=3600
CACHE_VERSION=1
CACHE_COMPRESS_THRESHOLD=1024
```

---

## 📋 Complete Environment Variables Checklist

Copy and paste this checklist when setting up your environment variables:

```
✅ DATABASE_URL (or NEON_DB_URL)
✅ OPENAI_API_KEY
✅ JWT_SECRET_KEY
✅ CORS_ORIGINS
✅ ENVIRONMENT=production
✅ NEO4J_URI (optional)
✅ NEO4J_USER (optional)
✅ NEO4J_PASSWORD (optional)
✅ UPSTASH_REDIS_REST_URL (optional)
✅ UPSTASH_REDIS_REST_TOKEN (optional)
✅ REDIS_URI (optional, if not using Upstash)
```

---

## 🚀 Step 5: Deploy

1. Click **"Create Web Service"** or **"Save Changes"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies from `api/requirements.txt`
   - Start your application
3. Monitor the **"Logs"** tab for any errors
4. Once deployed, you'll get a URL like: `https://healthcare-chatbot-api.onrender.com`

---

## ✅ Step 6: Verify Deployment

### 6.1 Check Health Endpoint

Visit your service URL:
```
https://your-service-name.onrender.com/docs
```

You should see the FastAPI Swagger documentation.

### 6.2 Test API Endpoints

Test a simple endpoint:
```bash
curl https://your-service-name.onrender.com/health
```

### 6.3 Check Logs

In Render dashboard → **"Logs"** tab, you should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

---

## 🔧 Troubleshooting

### Issue: Build Fails

**Problem**: Dependencies not installing

**Solution**:
- Check that `api/requirements.txt` exists
- Verify Python version (should be 3.11+)
- Check build logs for specific error messages

### Issue: Application Crashes on Startup

**Problem**: Missing environment variables or database connection issues

**Solution**:
- Verify all required environment variables are set
- Check database connection string format
- Review logs for specific error messages
- Ensure database allows connections from Render's IPs

### Issue: CORS Errors

**Problem**: Frontend can't connect to backend

**Solution**:
- Verify `CORS_ORIGINS` includes your frontend domain
- Check that domain doesn't have trailing slashes
- Ensure `allow_credentials=True` is set (already in code)

### Issue: Database Connection Timeout

**Problem**: Database not accessible from Render

**Solution**:
- Ensure your database allows external connections
- Check firewall/security group settings
- Verify connection string is correct
- For NeonDB/Supabase: Check connection pooling settings

### Issue: Redis Connection Fails

**Problem**: Redis not connecting

**Solution**:
- Verify Redis credentials are correct
- Check if Redis service allows external connections
- For Upstash: Ensure REST URL and token are correct
- Application will work without Redis (uses fallback)

### Issue: Port Already in Use

**Problem**: Application can't bind to port

**Solution**:
- Ensure you're using `$PORT` environment variable
- Don't hardcode port numbers
- Check start command uses `--port $PORT`

---

## 📊 Monitoring & Maintenance

### View Logs
- Go to your service → **"Logs"** tab
- Logs are streamed in real-time
- Use filters to search for specific errors

### Check Metrics
- **"Metrics"** tab shows CPU, memory, and request metrics
- Monitor for performance issues
- Upgrade plan if needed

### Auto-Deploy
- Render automatically deploys on git push to main branch
- Manual deploys available in **"Manual Deploy"** section
- Rollback to previous deployments if needed

---

## 🔒 Security Best Practices

1. **Never commit `.env` files** - Use Render's environment variables
2. **Use strong JWT_SECRET_KEY** - Generate with: `secrets.token_urlsafe(32)`
3. **Restrict CORS_ORIGINS** - Only include your production domains
4. **Use HTTPS** - Render provides SSL certificates automatically
5. **Rotate secrets regularly** - Update API keys and secrets periodically
6. **Monitor logs** - Check for suspicious activity

---

## 💰 Cost Optimization

### Free Tier Limitations:
- Spins down after 15 minutes of inactivity
- Limited CPU and memory
- Slower cold starts

### Recommendations:
- Use **Starter plan ($7/month)** for production
- Consider **Standard plan ($25/month)** for higher traffic
- Monitor usage in **"Metrics"** tab

---

## 🔗 Next Steps

1. **Update Frontend**: Point your frontend API URL to your Render service
2. **Set up Custom Domain**: Add your domain in Render settings
3. **Enable Auto-Deploy**: Push to main branch to auto-deploy
4. **Set up Monitoring**: Configure alerts for downtime
5. **Backup Database**: Set up regular database backups

---

## 📞 Support

If you encounter issues:
1. Check Render's [Documentation](https://render.com/docs)
2. Review application logs
3. Check [Render Status Page](https://status.render.com)
4. Contact Render support if needed

---

## 📝 Quick Reference

### Start Command (if Procfile not used):
```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 2
```

### Build Command:
```bash
pip install -r api/requirements.txt
```

### Minimum Required Environment Variables:
```
DATABASE_URL
OPENAI_API_KEY
JWT_SECRET_KEY
CORS_ORIGINS
```

---

**🎉 Congratulations! Your backend is now deployed on Render!**

