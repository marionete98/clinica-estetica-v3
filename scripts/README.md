# Scripts Directory

This directory contains utility scripts for database management, deployment verification, and system maintenance.

## Database Management Scripts

### seed_data_v2.py ✅ (RECOMMENDED)

Seeds the Supabase database with initial clinic data.

**Purpose:** Insert rooms, procedures, knowledge base articles, and message templates

**Usage:**
```bash
# Set environment variables
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-service-role-key

# Run seed script
python scripts/seed_data_v2.py
```

**What Gets Seeded:**
- **Rooms (7 total):** Sala 01-05, Apartamento, Esterilização
- **Procedures (15+ treatments):** Depilação a Laser, Harmonização Facial/Corporal, etc.
- **Knowledge Base (13+ articles):** Treatment info, policies, consultations
- **Message Templates:** Standardized communication templates

**Requirements:** 5.2, 13.1, 13.2, 13.3, 14.1, 14.2, 15.1, 15.2, 4.2, 4.3

### verify_database.py

Verifies database schema, seed data, and operations.

**Purpose:** Validate that database is properly configured

**Usage:**
```bash
python scripts/verify_database.py
```

**Checks:**
- All required tables exist (contacts, rooms, services, appointments, etc.)
- Seed data is populated (7 rooms, 15+ services, 13+ KB articles)
- CRUD operations work correctly
- Triggers function properly (updated_at)

**Requirements:** 3.1, 3.2

### check_schema.py

Validates the database schema against expected structure.

**Purpose:** Check schema consistency

**Usage:**
```bash
python scripts/check_schema.py
```

### inspect_redis.py ✅

Comprehensive Redis configuration and data inspection utility.

**Purpose:** Analyze Redis server status, cache structure, and performance

**Usage:**
```bash
python scripts/inspect_redis.py
```

**Inspection Areas:**
- **Redis Server Info:** Version, memory usage, uptime, modules, database stats
- **KB Cache Structure:** Knowledge base entries, indexes, templates, conversation keys
- **Sample Data:** Cache metadata, sample entries, templates, and indexes
- **Memory Usage:** Breakdown by key patterns (KB, templates, conversations, indexes)
- **Key Expiration:** TTL analysis for different key types
- **Redis Operations:** Test basic operations (SET, GET, DELETE, SET operations)

**Output:** Comprehensive report with pass/fail status for each inspection area

**Use Cases:**
- Troubleshoot Redis connectivity issues
- Monitor knowledge base cache performance
- Analyze memory usage patterns
- Verify cache synchronization
- Debug cache-related problems

**Requirements:** Redis connection configured in environment

### test_simple_cache.py ✅

Simple cache infrastructure testing utility for KB cache service.

**Purpose:** Basic validation of cache infrastructure components before running full cache tests

**Usage:**
```bash
python scripts/test_simple_cache.py
```

**What It Tests:**
- ✓ Import validation for cache dependencies
- ✓ Redis client connectivity and basic operations
- ✓ Supabase client connectivity and queries
- ✓ Repository function imports
- ✓ Basic Redis SET/GET/DELETE operations

**Test Flow:**
1. **Import Tests:** Validates all required modules can be imported
2. **Redis Operations:** Tests basic cache operations (set, get, delete)
3. **Supabase Connection:** Verifies database connectivity with simple query
4. **Infrastructure Ready:** Confirms cache infrastructure is operational

**Output:** Step-by-step validation with ✅/❌ indicators

**Use Cases:**
- Pre-deployment cache infrastructure validation
- Troubleshoot cache service import issues
- Verify Redis and Supabase connectivity
- Quick cache readiness check
- Debug cache initialization problems

**Requirements:** Redis and Supabase connections configured

## Deployment and Validation Scripts

### validate_env.py

Validates environment variables and API keys before deployment.

**Purpose:** Ensure all required configuration is set and valid

**Usage:**
```bash
python scripts/validate_env.py
```

**Checks:**
- ✓ Required environment variables are set
- ✓ LLM provider API keys are valid (xAI/Gemini)
- ✓ Supabase connection works
- ✓ Redis connection works
- ✓ Chatwoot API is accessible
- ✓ Calendar API is accessible

**Output:** Color-coded validation results with specific error messages

**Requirements:** 9.1, 9.2, 9.3, 9.4

### verify_deployment.py

Verifies Railway deployment is healthy and functional.

**Purpose:** Validate production deployment after going live

**Usage:**
```bash
python scripts/verify_deployment.py https://your-app.railway.app
```

**Checks:**
- ✓ Root endpoint accessible
- ✓ Health check passing (all components)
- ✓ Scheduler running (3 jobs)
- ✓ Metrics endpoint working
- ✓ Chat endpoint functional
- ✓ Dashboard accessible

**Output:** Comprehensive verification report with next steps

**Requirements:** 9.4

## Agent Migration Verification Scripts

### verify_followup_migration.py ✅

Verifies the Followup Agent migration to AutoGen 0.4.

**Purpose:** Validate that the Followup Agent has been successfully migrated to AutoGen 0.4 architecture

**Usage:**
```bash
python scripts/verify_followup_migration.py
```

**What It Checks:**
- ✓ Agent creation successful
- ✓ Agent type is FollowupAgent
- ✓ Has cleanup() method for resource management
- ✓ Has model_client attribute
- ✓ Has all send methods (booking confirmation, reminders, feedback)
- ✓ Internal agent is AssistantAgent (AutoGen 0.4)
- ✓ Model client is OpenAIChatCompletionClient
- ✓ Tools are properly registered

**Output:** Step-by-step validation with ✓ indicators

**Use Cases:**
- Verify AutoGen 0.4 migration completion
- Validate agent structure and methods
- Confirm tool registration
- Pre-deployment migration check

**Requirements:** AutoGen 0.4 dependencies installed

**Documentation:** See `docs/FOLLOWUP_AGENT_MIGRATION.md` for migration details

## Integration Testing Scripts

### test_chatwoot_integration.py ✅

Tests the complete Chatwoot webhook integration flow.

**Purpose:** Verify webhook configuration and end-to-end message processing

**Usage:**
```bash
# Test deployed system
python scripts/test_chatwoot_integration.py https://your-app.railway.app

# Test local development
python scripts/test_chatwoot_integration.py http://localhost:8000
```

**What It Tests:**
- ✓ Health endpoint verification
- ✓ Webhook signature generation
- ✓ Webhook payload creation and sending
- ✓ Webhook acceptance (200 OK response)
- ✓ Message processing in background
- ✓ Log creation in Supabase
- ✓ Multiple message scenarios (FAQ, scheduling, greetings)

**Test Scenarios:**
1. "Olá, gostaria de informações sobre depilação a laser" (FAQ)
2. "Quais são os horários de funcionamento?" (FAQ)
3. "Quero agendar uma consulta" (Scheduling)

**Output:** Comprehensive test report with pass/fail for each scenario

**Requirements:** 1.1, 1.5, 3.5

**Documentation:** See `docs/CHATWOOT_INTEGRATION_GUIDE.md` for setup details

## Deprecated Scripts

### seed_data.py ⚠️

**Status:** DEPRECATED - Use seed_data_v2.py instead

Original seed script, replaced by v2 which is adapted for the current schema.

## Prerequisites

All scripts require:
- Python 3.11+
- Project dependencies installed: `pip install -r requirements.txt`
- Environment variables configured (see `.env.example`)

## Environment Variables

### For Database Scripts

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key  # Use service_role, not anon key
```

### For Validation Scripts

```bash
# All variables from .env.example
MODEL_PROVIDER=xai
XAI_API_KEY=sk-...
GEMINI_API_KEY=...
SUPABASE_URL=https://...
SUPABASE_KEY=...
REDIS_URL=redis://...
CHATWOOT_API_URL=https://...
CHATWOOT_ACCOUNT_ID=...
CHATWOOT_API_TOKEN=...
CHATWOOT_WEBHOOK_SECRET=...
CALENDAR_API_URL=https://...
```

## Common Workflows

### 1. Initial Database Setup

```bash
# Step 1: Run migration in Supabase dashboard
# (Copy contents of supabase/migrations/001_create_initial_schema.sql)

# Step 2: Populate seed data
python scripts/seed_data_v2.py

# Step 3: Verify database
python scripts/verify_database.py
```

Expected output: All checks pass ✓

### 2. Pre-Deployment Validation

```bash
# Step 1: Validate environment
python scripts/validate_env.py

# Step 2: Fix any issues reported
# Step 3: Deploy to Railway
```

Expected output: All validations passed ✓

### 3. Post-Deployment Verification

```bash
# Step 1: Verify deployment
python scripts/verify_deployment.py https://your-app.railway.app

# Step 2: Test Chatwoot integration
python scripts/test_chatwoot_integration.py https://your-app.railway.app

# Step 3: Check all endpoints pass
# Step 4: Monitor logs for first hour
```

Expected output: All verifications passed ✓

### 4. Chatwoot Integration Testing

```bash
# Step 1: Configure webhook in Chatwoot
# (Follow docs/CHATWOOT_INTEGRATION_GUIDE.md)

# Step 2: Run integration tests
python scripts/test_chatwoot_integration.py https://your-app.railway.app

# Step 3: Send test messages in Chatwoot
# Step 4: Verify responses and logs
```

Expected output: All tests passed ✓

## Troubleshooting

### "Module not found" errors

**Cause:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
```

### "Environment variable not set" errors

**Cause:** Required variables missing

**Solution:**
```bash
# Option 1: Export variables
export SUPABASE_URL=https://...
export SUPABASE_KEY=...

# Option 2: Create .env file
cp .env.example .env
# Edit .env with your values
```

### "Connection refused" errors

**Cause:** Service unreachable

**Solution:**
- Check network connectivity
- Verify URLs are correct
- Check service status pages
- Verify firewall settings

### "Permission denied" errors

**Cause:** Incorrect credentials or insufficient permissions

**Solution:**
- Use service_role key for Supabase (not anon key)
- Verify API tokens have correct permissions
- Check token hasn't expired

### "Duplicate key" errors in seed script

**Cause:** Data already exists

**Solution:**
- Script uses upsert, so this shouldn't happen
- If it does, check for data conflicts
- Consider clearing tables and re-seeding

### Validation script fails

**Cause:** Configuration or connectivity issues

**Solution:**
1. Read error messages carefully
2. Fix reported issues one by one
3. Re-run validation
4. Consult documentation for specific errors

## Script Output Examples

### Successful Validation

```
✓ All required variables are set
✓ xAI API key is valid (model: grok-4-reasoning)
✓ Supabase connection is valid
✓ Redis connection is valid
✓ Chatwoot API connection is valid
✓ Calendar API connection is valid

✓ All validations passed!
System is ready for Railway deployment.
```

### Successful Database Verification

```
✓ Table 'contacts' exists
✓ Table 'rooms' exists
...
✓ All 9 required tables exist

✓ Rooms: 7 rows (expected: 7)
✓ Services: 15 rows (expected: 15+)
✓ Knowledge Base: 13 articles (expected: 13+)

✓ Database is properly configured!
```

### Successful Deployment Verification

```
✓ Root endpoint is accessible
✓ Overall status: healthy
✓ Scheduler status: running
✓ Found 3 scheduled jobs
✓ Chat endpoint is functional

✓ All verifications passed!
Deployment is healthy and ready for use.
```

## Documentation

For detailed guides, see:
- **Database setup:** `docs/DATABASE_MIGRATION_GUIDE.md`
- **Deployment:** `docs/RAILWAY_DEPLOYMENT_GUIDE.md`
- **Quick start:** `docs/RAILWAY_QUICKSTART.md`
- **Health checks:** `docs/HEALTH_CHECK_CONFIGURATION.md`
- **Deployment checklist:** `docs/DEPLOYMENT_CHECKLIST.md`

## Support

For issues or questions:
1. Check documentation in `docs/` directory
2. Review error messages carefully
3. Verify environment variables are set correctly
4. Test connectivity to external services
5. Create issue in GitHub repository with:
   - Script name
   - Error message
   - Environment (local/Railway)
   - Steps to reproduce

---

**Last Updated:** 2025-10-16  
**Requirements:** 1.1, 1.5, 3.1, 3.2, 3.5, 5.2, 9.1, 9.2, 9.3, 9.4, 13.1-13.3, 14.1-14.2, 15.1-15.2
