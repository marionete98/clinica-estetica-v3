# Railway Deployment Quick Start

## 5-Minute Deployment Guide

This guide will get your Clínica Luana Multi-Agent System deployed to Railway in 5 minutes.

## Prerequisites

- Railway account (sign up at https://railway.app)
- GitHub repository with the code
- All API keys ready (xAI/Gemini, Supabase, Redis, Chatwoot)

## Step 1: Create Railway Project (1 minute)

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Click "Deploy Now"

Railway will automatically:
- Detect the Dockerfile
- Start building the image
- Create a service

## Step 2: Add Environment Variables (2 minutes)

1. Click on your service
2. Go to "Variables" tab
3. Click "Raw Editor"
4. Paste this template and fill in your values:

```bash
MODEL_PROVIDER=xai
XAI_API_KEY=your-key-here
XAI_MODEL=grok-4-reasoning
XAI_BASE_URL=https://api.x.ai/v1
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.5-flash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
REDIS_URL=redis://default:password@your-host:6379
REDIS_PASSWORD=your-password
REDIS_HOST=your-host.cloud.redislabs.com
REDIS_PORT=6379
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=12345
CHATWOOT_API_TOKEN=your-token
CHATWOOT_WEBHOOK_SECRET=your-secret
CALENDAR_API_URL=https://clinica-luana-calendar-production.up.railway.app/api
CALENDAR_API_TIMEOUT=10
ENV=production
LOG_LEVEL=INFO
```

5. Click "Update Variables"

Railway will automatically redeploy with the new variables.

## Step 3: Verify Deployment (2 minutes)

1. Wait for deployment to complete (watch the logs)
2. Click "Generate Domain" to get your public URL
3. Test the health endpoint:

```bash
curl https://your-app.railway.app/health
```

Expected: `"status": "healthy"`

4. Run the verification script:

```bash
python scripts/verify_deployment.py https://your-app.railway.app
```

Expected: All checks pass ✓

## Step 4: Configure Chatwoot Webhook (1 minute)

1. Go to Chatwoot → Settings → Integrations → Webhooks
2. Add new webhook:
   - URL: `https://your-app.railway.app/webhook/chatwoot`
   - Events: `message_created`
   - Secret: (use your `CHATWOOT_WEBHOOK_SECRET`)
3. Save

## Done! 🎉

Your system is now live. Test it by:

1. Sending a message in Chatwoot
2. Watching the Railway logs
3. Seeing the agent response in Chatwoot

## Next Steps

- [ ] Monitor logs for first hour
- [ ] Test all conversation flows
- [ ] Review metrics dashboard: `https://your-app.railway.app/dashboard`
- [ ] Set up alerts in Railway
- [ ] Complete full deployment checklist (see DEPLOYMENT_CHECKLIST.md)

## Troubleshooting

### Build Fails

**Check:** Railway build logs for errors
**Fix:** Ensure Dockerfile is correct and all dependencies in requirements.txt

### Health Check Fails

**Check:** Application logs for startup errors
**Fix:** Verify all environment variables are set correctly

### Webhook Not Working

**Check:** Railway logs for incoming requests
**Fix:** Verify webhook URL and secret in Chatwoot

### Agent Not Responding

**Check:** LLM provider API key is valid
**Fix:** Run `python scripts/validate_env.py` locally

## Support

- **Documentation:** See `docs/RAILWAY_DEPLOYMENT_GUIDE.md` for detailed guide
- **Checklist:** See `docs/DEPLOYMENT_CHECKLIST.md` for complete checklist
- **Railway Help:** https://railway.app/help
- **Project Issues:** Create issue in GitHub repository

---

**Requirements:** 9.4
