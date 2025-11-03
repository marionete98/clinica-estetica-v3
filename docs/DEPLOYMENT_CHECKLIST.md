# Railway Deployment Checklist

## Pre-Deployment Checklist

### 1. Code Preparation

- [ ] All code committed to Git repository
- [ ] No sensitive data in repository (check .gitignore)
- [ ] All tests passing locally
- [ ] Dependencies up to date in requirements.txt
- [ ] Dockerfile builds successfully locally
- [ ] .env.example is up to date with all variables

### 2. Environment Variables

- [ ] All required variables documented
- [ ] API keys obtained and validated
- [ ] Webhook secrets generated (min 32 characters)
- [ ] Database credentials ready
- [ ] Redis connection string ready
- [ ] Chatwoot configuration ready

### 3. External Services

- [ ] Supabase project created
- [ ] Redis Cloud instance created
- [ ] Chatwoot account configured
- [ ] Calendar API accessible
- [ ] LLM provider API keys active

### 4. Validation

- [ ] Run `python scripts/validate_env.py` successfully
- [ ] Test health endpoint locally
- [ ] Test chat endpoint locally
- [ ] Verify all agent tools work
- [ ] Check scheduled jobs configuration

## Railway Setup Checklist

### 1. Create Railway Project

- [ ] Sign up/login to Railway (https://railway.app)
- [ ] Create new project
- [ ] Name: `clinica-luana-agent-system`
- [ ] Select region (closest to Brazil: us-west1)

### 2. Connect Repository

- [ ] Connect GitHub account to Railway
- [ ] Select repository
- [ ] Choose branch (main/master)
- [ ] Enable automatic deployments

### 3. Configure Build

- [ ] Verify Railway detects Dockerfile
- [ ] Build command: Automatic (uses Dockerfile)
- [ ] Start command: Automatic (from Dockerfile CMD)
- [ ] Root directory: `/` (default)

### 4. Add Environment Variables

Copy all variables from `.env` to Railway:

#### LLM Configuration
- [ ] `MODEL_PROVIDER`
- [ ] `XAI_API_KEY`
- [ ] `XAI_MODEL`
- [ ] `XAI_BASE_URL`
- [ ] `GEMINI_API_KEY`
- [ ] `GEMINI_MODEL`

#### Database
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_KEY`
- [ ] `SUPABASE_JWT_SECRET`

#### Cache
- [ ] `REDIS_URL`
- [ ] `REDIS_PASSWORD`
- [ ] `REDIS_HOST`
- [ ] `REDIS_PORT`

#### Chatwoot
- [ ] `CHATWOOT_API_URL`
- [ ] `CHATWOOT_ACCOUNT_ID`
- [ ] `CHATWOOT_API_TOKEN`
- [ ] `CHATWOOT_WEBHOOK_SECRET`

#### Calendar API
- [ ] `CALENDAR_API_URL`
- [ ] `CALENDAR_API_TIMEOUT`

#### Application
- [ ] `ENV=production`
- [ ] `LOG_LEVEL=INFO`
- [ ] All business configuration variables

### 5. Configure Service Settings

- [ ] Service name: `clinica-luana-agent-system`
- [ ] Health check path: `/health`
- [ ] Health check timeout: 5 seconds
- [ ] Restart policy: ON_FAILURE
- [ ] Max restarts: 5 per hour

### 6. Resource Allocation

Initial configuration:
- [ ] Memory: 512MB
- [ ] CPU: 0.5 vCPU
- [ ] Instances: 1

## Deployment Checklist

### 1. Initial Deployment

- [ ] Trigger deployment (push to main or manual trigger)
- [ ] Monitor build logs in Railway dashboard
- [ ] Wait for build to complete (typically 2-5 minutes)
- [ ] Verify deployment status shows "Active"

### 2. Verify Build Logs

Check for these success indicators:
- [ ] "Successfully built" message
- [ ] No error messages in build output
- [ ] Docker image created successfully
- [ ] Container started successfully

### 3. Verify Startup Logs

Check for these in application logs:
- [ ] "Starting Clínica Luana Multi-Agent System..."
- [ ] "Redis connection established"
- [ ] "Supabase connection established"
- [ ] "Chatwoot API connection verified"
- [ ] "APScheduler started successfully"
- [ ] "System startup complete"

### 4. Test Health Endpoint

```bash
curl https://your-app.railway.app/health
```

Expected response:
- [ ] Status code: 200
- [ ] `"status": "healthy"`
- [ ] All checks: `true`
- [ ] LLM provider configured correctly

### 5. Test Scheduler Status

```bash
curl https://your-app.railway.app/scheduler/status
```

Expected response:
- [ ] Status: "running"
- [ ] 3 jobs listed (reminder, feedback, alert_check)
- [ ] All jobs have next_run times

### 6. Test Metrics Endpoint

```bash
curl https://your-app.railway.app/metrics
```

Expected response:
- [ ] Status code: 200
- [ ] Metrics structure present (may be null initially)

### 7. Test Chat Endpoint

```bash
curl -X POST https://your-app.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+5594991398585",
    "message": "Olá, gostaria de informações sobre depilação a laser"
  }'
```

Expected response:
- [ ] Status code: 200
- [ ] Response contains agent reply
- [ ] Intent detected correctly
- [ ] No error messages

### 8. Test Dashboard

Visit: `https://your-app.railway.app/dashboard`

- [ ] Dashboard loads successfully
- [ ] Metrics displayed (may be zero initially)
- [ ] No JavaScript errors in console

## Post-Deployment Checklist

### 1. Configure Chatwoot Webhook

In Chatwoot dashboard:
- [ ] Go to Settings → Integrations → Webhooks
- [ ] Click "Add Webhook"
- [ ] URL: `https://your-app.railway.app/webhook/chatwoot`
- [ ] Events: Select "message_created"
- [ ] Secret: Use `CHATWOOT_WEBHOOK_SECRET` value
- [ ] Save webhook

### 2. Test Webhook Integration

- [ ] Send test message in Chatwoot
- [ ] Check Railway logs for webhook received
- [ ] Verify agent processes message
- [ ] Verify response sent back to Chatwoot
- [ ] Check message appears in Chatwoot conversation

### 3. Verify Database Operations

- [ ] Check Supabase logs table for entries
- [ ] Verify contacts table can be written to
- [ ] Check sessions table for conversation tracking
- [ ] Verify appointments can be created (if testing scheduling)

### 4. Verify Scheduled Jobs

Wait 30 minutes and check:
- [ ] Reminder job executed (check logs)
- [ ] No errors in job execution
- [ ] Jobs rescheduled for next run

### 5. Monitor Initial Traffic

For first 2 hours:
- [ ] Check logs every 15 minutes
- [ ] Monitor error rate (should be 0%)
- [ ] Check latency metrics (should be < 7s)
- [ ] Verify no unexpected restarts

### 6. Performance Validation

After 24 hours:
- [ ] P95 latency ≤ 7 seconds
- [ ] Error rate < 2%
- [ ] Handover rate < 30%
- [ ] No memory leaks (check Railway metrics)
- [ ] CPU usage < 70% average

## Rollback Checklist

If deployment fails or issues arise:

### 1. Immediate Rollback

- [ ] Go to Railway dashboard
- [ ] Click on deployment history
- [ ] Select previous working deployment
- [ ] Click "Redeploy"
- [ ] Wait for rollback to complete

### 2. Verify Rollback

- [ ] Test health endpoint
- [ ] Verify previous version is running
- [ ] Check logs for successful startup
- [ ] Test basic functionality

### 3. Investigate Issues

- [ ] Review deployment logs
- [ ] Check error messages
- [ ] Verify environment variables
- [ ] Test locally with production config
- [ ] Document issues found

### 4. Fix and Redeploy

- [ ] Fix identified issues
- [ ] Test fixes locally
- [ ] Commit and push fixes
- [ ] Trigger new deployment
- [ ] Monitor closely

## Monitoring Setup Checklist

### 1. Railway Monitoring

- [ ] Enable Railway metrics
- [ ] Set up CPU usage alerts (> 80%)
- [ ] Set up memory usage alerts (> 90%)
- [ ] Set up deployment failure alerts

### 2. Application Monitoring

- [ ] Verify logs are being captured
- [ ] Check metrics endpoint is accessible
- [ ] Set up external uptime monitoring (optional)
- [ ] Configure alert email (if enabled)

### 3. Database Monitoring

- [ ] Check Supabase dashboard
- [ ] Verify query performance
- [ ] Monitor database size
- [ ] Set up slow query alerts

### 4. External Service Monitoring

- [ ] Monitor Chatwoot API status
- [ ] Monitor Calendar API status
- [ ] Monitor LLM provider status
- [ ] Set up status page subscriptions

## Documentation Checklist

### 1. Update Documentation

- [ ] Document Railway URL
- [ ] Update webhook URLs in docs
- [ ] Document any deployment-specific configurations
- [ ] Update runbooks with production details

### 2. Team Communication

- [ ] Notify team of deployment
- [ ] Share Railway dashboard access
- [ ] Share monitoring dashboard access
- [ ] Document on-call procedures

### 3. Handoff Documentation

- [ ] Create operations guide
- [ ] Document common issues and solutions
- [ ] Create escalation procedures
- [ ] Document emergency contacts

## Success Criteria

Deployment is considered successful when:

- [ ] All health checks passing
- [ ] No errors in logs for 1 hour
- [ ] Webhook integration working
- [ ] Scheduled jobs running
- [ ] Test conversations complete successfully
- [ ] Metrics within acceptable ranges
- [ ] No unexpected restarts
- [ ] Team has access and training

## Emergency Contacts

- **Railway Support:** https://railway.app/help
- **Supabase Support:** https://supabase.com/support
- **Chatwoot Support:** https://www.chatwoot.com/help-center
- **On-Call Engineer:** [Add contact]
- **Project Lead:** [Add contact]

## Notes

Use this section to document deployment-specific notes:

- Deployment Date: _______________
- Deployed By: _______________
- Railway URL: _______________
- Issues Encountered: _______________
- Resolutions Applied: _______________

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-16  
**Requirements:** 9.4
