# Production Validation Quickstart

Quick guide to validate production compatibility after AutoGen 0.4 migration.

## Run Validation

```bash
py scripts/validate_production_compatibility.py
```

## Expected Output

```
✅ ALL TESTS PASSED - Production Ready!
Total Tests: 10
Passed: 10
Failed: 0
Success Rate: 100.0%
```

## What It Tests

1. **Environment Variables** - All required config present
2. **Railway Config** - Deployment settings valid
3. **Health Endpoint** - API health check working
4. **Supabase Database** - All tables accessible
5. **Redis Caching** - Context management working
6. **Chatwoot Integration** - Webhooks functional
7. **Agent Initialization** - All 6 agents with AutoGen 0.4
8. **Orchestrator Cleanup** - Resource management ready
9. **Scheduled Jobs** - Background jobs configured
10. **Error Handling** - Graceful degradation active

## If Tests Fail

### Check Environment Variables
```bash
# Verify .env file has all required variables
py scripts/validate_env.py
```

### Check Database Connection
```bash
# Verify Supabase schema
py scripts/verify_database.py
```

### Check Dependencies
```bash
# Ensure all packages installed
pip install -r requirements.txt
```

## Production Deployment

Once validation passes:

1. **Deploy to Staging:**
   ```bash
   git push staging main
   ```

2. **Monitor Logs:**
   - Check Railway logs for errors
   - Verify health endpoint: `https://your-app.railway.app/health`

3. **Test Flows:**
   - Send test messages via Chatwoot
   - Verify agent responses
   - Check scheduled jobs

4. **Deploy to Production:**
   - Gradual rollout (10% → 50% → 100%)
   - Monitor metrics continuously
   - Keep rollback ready

## Health Check

After deployment, verify health:

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "clinica-luana-agent-system",
  "version": "0.1.0",
  "checks": {
    "redis": true,
    "supabase": true,
    "chatwoot": true,
    "llm_config": true
  }
}
```

## Rollback

If issues occur:

```bash
railway rollback
```

## Documentation

- Full validation report: `docs/PRODUCTION_COMPATIBILITY_VALIDATION.md`
- Migration guide: `docs/AUTOGEN_MIGRATION_GUIDE.md`
- Deployment guide: `docs/RAILWAY_DEPLOYMENT_GUIDE.md`

## Support

If validation fails or you encounter issues:
1. Check logs: `railway logs`
2. Review error messages in validation output
3. Verify environment variables
4. Check service connectivity

---

**Status:** ✅ Production Ready  
**Last Validated:** October 16, 2025
