# Railway Deployment - Quick Reference Card

## 🚀 Quick Deploy (30 minutes total)

### 1. Pre-Flight Check (5 min)
```bash
python scripts/validate_env.py
```
✅ All validations passed → Continue  
❌ Failures → Fix issues and retry

### 2. Database Setup (10 min)
```bash
# In Supabase SQL Editor:
# Run: supabase/migrations/001_create_initial_schema.sql

# Then locally:
python scripts/seed_data_v2.py
python scripts/verify_database.py
```
✅ Database properly configured → Continue

### 3. Railway Deploy (5 min)
1. Create project at https://railway.app
2. Connect GitHub repo
3. Add environment variables (see below)
4. Deploy automatically

### 4. Verify (5 min)
```bash
python scripts/verify_deployment.py https://your-app.railway.app
```
✅ All verifications passed → Continue

### 5. Configure Chatwoot (2 min)
- URL: `https://your-app.railway.app/webhook/chatwoot`
- Events: `message_created`
- Secret: Your `CHATWOOT_WEBHOOK_SECRET`

### 6. Test Integration (5 min)
```bash
# Automated tests
python scripts/test_chatwoot_integration.py https://your-app.railway.app

# Manual test
# Send test message in Chatwoot → Verify response
```
✅ All tests passed → Production ready

## 📋 Essential Environment Variables

```bash
# LLM
MODEL_PROVIDER=xai
XAI_API_KEY=sk-...

# Database
SUPABASE_URL=https://...
SUPABASE_KEY=...

# Cache
REDIS_URL=redis://...

# Chatwoot
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=...
CHATWOOT_API_TOKEN=...
CHATWOOT_WEBHOOK_SECRET=...

# Calendar
CALENDAR_API_URL=https://clinica-luana-calendar-production.up.railway.app/api

# App
ENV=production
LOG_LEVEL=INFO
```

## 🔍 Health Check URLs

| Endpoint | URL | Expected |
|----------|-----|----------|
| Health | `/health` | `"status": "healthy"` |
| Metrics | `/metrics` | Metrics data |
| Dashboard | `/dashboard` | HTML page |
| Scheduler | `/scheduler/status` | `"status": "running"` |
| Chat Test | `/chat` (POST) | Agent response |

## 📊 Success Metrics

| Metric | Target | Alert If |
|--------|--------|----------|
| P95 Latency | ≤ 7s | > 7s for 10 min |
| Error Rate | < 2% | > 2% for 10 min |
| Handover Rate | < 30% | > 30% for 1 hour |
| Conversion | > 70% | < 50% for 4 hours |

## 🛠️ Troubleshooting Commands

```bash
# Validate environment
python scripts/validate_env.py

# Verify database
python scripts/verify_database.py

# Verify deployment
python scripts/verify_deployment.py https://your-app.railway.app

# Test Chatwoot integration
python scripts/test_chatwoot_integration.py https://your-app.railway.app

# Check Railway logs
railway logs

# Test health endpoint
curl https://your-app.railway.app/health

# Test chat endpoint
curl -X POST https://your-app.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"phone": "+5594991398585", "message": "Olá"}'
```

## 🚨 Common Issues

| Issue | Quick Fix |
|-------|-----------|
| Build fails | Check `Dockerfile` and `requirements.txt` |
| Health fails | Verify all env vars set |
| High latency | Check LLM provider status |
| Webhook fails | Verify URL and secret |
| DB errors | Check Supabase credentials |

## 📚 Documentation

- **Full Guide:** `docs/RAILWAY_DEPLOYMENT_GUIDE.md`
- **Quick Start:** `docs/RAILWAY_QUICKSTART.md`
- **Checklist:** `docs/DEPLOYMENT_CHECKLIST.md`
- **Database:** `docs/DATABASE_MIGRATION_GUIDE.md`
- **Summary:** `docs/DEPLOYMENT_SUMMARY.md`

## 💰 Cost Estimate

**~$20-30/month** for 1000 conversations
- Railway: $5-15
- LLM: $10-20
- Supabase: $0 (free tier)
- Redis: $0 (free tier)

## 📞 Support

- Railway: https://railway.app/help
- Supabase: https://supabase.com/support
- Project Issues: GitHub repository

---

**Keep this card handy during deployment!**
