# ⚡ Quick Setup Checklist for Render Deployment

Use this checklist when entering details in Render's dashboard.

---

## 📝 Render Dashboard Configuration

### Step 1: Basic Settings

When creating a new Web Service, enter these values:

| Field | Enter This Value |
|-------|------------------|
| **Name** | `healthcare-chatbot-api` |
| **Region** | Choose closest to your users |
| **Branch** | `main` |
| **Root Directory** | *(leave empty)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r api/requirements.txt` |
| **Start Command** | `uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 2` |

---

## 🔐 Step 2: Environment Variables

Go to **Environment** tab and add these variables one by one:

### ✅ Required Variables (Must Have)

```
DATABASE_URL
```
**Value**: Your PostgreSQL connection string
**Example**: `postgresql://user:pass@host:5432/dbname`

```
OPENAI_API_KEY
```
**Value**: Your OpenAI API key
**Example**: `sk-proj-...`

```
JWT_SECRET_KEY
```
**Value**: A secure random string (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
**Example**: `xK9mP2vQ7wR4tY8uI0oP3aS6dF9gH2jK5lM8nQ1rT4vW7yZ0`

```
CORS_ORIGINS
```
**Value**: Your frontend domain(s), comma-separated
**Example**: `https://your-frontend.vercel.app,https://www.your-frontend.com`

```
ENVIRONMENT
```
**Value**: `production`

---

### ⚙️ Optional Variables (Recommended)

#### Neo4j (Optional - has fallback)
```
NEO4J_URI
```
**Value**: `bolt://your-neo4j-host:7687`

```
NEO4J_USER
```
**Value**: `neo4j`

```
NEO4J_PASSWORD
```
**Value**: Your Neo4j password

#### Redis Cache (Optional - improves performance)
**Option A: Upstash Redis (Recommended)**
```
UPSTASH_REDIS_REST_URL
```
**Value**: `https://your-redis.upstash.io`

```
UPSTASH_REDIS_REST_TOKEN
```
**Value**: Your Upstash token

**Option B: Standard Redis**
```
REDIS_URI
```
**Value**: `redis://user:pass@host:6379` or `rediss://user:pass@host:6379` (for SSL)

#### Rate Limiting (Optional)
```
RATE_LIMIT
```
**Value**: `30`

```
RATE_WINDOW
```
**Value**: `60`

#### Logging (Optional)
```
LOG_LEVEL
```
**Value**: `INFO` or `DEBUG`

---

## 📋 Copy-Paste Checklist

Use this when adding environment variables:

```
☐ DATABASE_URL
☐ OPENAI_API_KEY
☐ JWT_SECRET_KEY
☐ CORS_ORIGINS
☐ ENVIRONMENT=production
☐ NEO4J_URI (optional)
☐ NEO4J_USER (optional)
☐ NEO4J_PASSWORD (optional)
☐ UPSTASH_REDIS_REST_URL (optional)
☐ UPSTASH_REDIS_REST_TOKEN (optional)
☐ REDIS_URI (optional)
☐ RATE_LIMIT (optional)
☐ RATE_WINDOW (optional)
☐ LOG_LEVEL (optional)
```

---

## 🎯 Quick Start Command Reference

If you need to manually enter the start command, use:

```bash
cd api && uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
```

**Important Notes:**
- Always use `$PORT` (Render sets this automatically)
- The `cd api` is needed because your code is in the `api/` folder
- `--workers 2` enables multiple processes for better performance

---

## ✅ Verification Steps

After deployment:

1. **Check Service URL**: Should be like `https://healthcare-chatbot-api.onrender.com`
2. **Visit `/docs`**: `https://your-service.onrender.com/docs` should show Swagger UI
3. **Check Logs**: In Render dashboard → Logs tab, should see "Application startup complete"
4. **Test Health**: Visit `https://your-service.onrender.com/health` (if endpoint exists)

---

## 🚨 Common Mistakes to Avoid

❌ **Don't** hardcode port numbers (use `$PORT`)
❌ **Don't** forget the `cd api` in start command
❌ **Don't** use `localhost` in CORS_ORIGINS for production
❌ **Don't** commit `.env` files with secrets
❌ **Don't** use weak JWT_SECRET_KEY

✅ **Do** use environment variables for all secrets
✅ **Do** test locally before deploying
✅ **Do** check logs if deployment fails
✅ **Do** verify all environment variables are set

---

## 📞 Need Help?

1. Check `RENDER_DEPLOYMENT.md` for detailed guide
2. Review Render logs for specific errors
3. Verify all environment variables are correctly set
4. Test database/Redis connections separately

---

**💡 Tip**: Save this file and refer to it while setting up your Render service!

