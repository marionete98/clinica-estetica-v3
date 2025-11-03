# Database Migration Guide

## Overview

This guide provides instructions for executing database migrations and seeding initial data for the Clínica Luana Multi-Agent System on Supabase.

## Prerequisites

- Supabase project created
- Service role key available
- Python 3.11+ installed locally
- Project dependencies installed (`pip install -r requirements.txt`)

## Migration Files

### Location

All migration files are located in: `supabase/migrations/`

### Current Migrations

1. **001_create_initial_schema.sql** - Creates all database tables and indexes
   - Tables: contacts, rooms, equipment, services, appointments, sessions, logs, message_templates, knowledge_base
   - Indexes for performance optimization
   - Triggers for automatic updated_at timestamps
   - Requirements: 3.1, 3.2, 3.3, 16.1

## Seed Scripts

### Location

Seed scripts are located in: `scripts/`

### Available Scripts

1. **seed_data_v2.py** - Populates initial clinic data
   - Rooms (7 rooms)
   - Procedures (15+ services)
   - Knowledge base articles (13+ articles)
   - Message templates
   - Requirements: 5.2, 13.1, 13.2, 13.3, 14.1, 14.2, 15.1, 15.2, 4.2, 4.3

## Method 1: Supabase Dashboard (Recommended for Production)

### Step 1: Run Migration

1. Log into Supabase dashboard
2. Go to your project
3. Navigate to **SQL Editor**
4. Click **New Query**
5. Copy the contents of `supabase/migrations/001_create_initial_schema.sql`
6. Paste into the query editor
7. Click **Run** (or press Ctrl+Enter)
8. Verify success message: "Success. No rows returned"

### Step 2: Verify Tables Created

1. Navigate to **Table Editor**
2. Verify all tables are present:
   - contacts
   - rooms
   - equipment
   - services
   - appointments
   - sessions
   - logs
   - message_templates
   - knowledge_base

### Step 3: Run Seed Script

1. Set up environment variables locally:
   ```bash
   export SUPABASE_URL=https://your-project.supabase.co
   export SUPABASE_KEY=your-service-role-key
   ```

2. Run the seed script:
   ```bash
   python scripts/seed_data_v2.py
   ```

3. Verify output shows successful inserts:
   ```
   Seeding rooms...
     ✓ Sala 01
     ✓ Sala 02
     ...
   Seeding procedures...
     ✓ Depilação a Laser
     ✓ Harmonização Facial
     ...
   ```

### Step 4: Verify Seed Data

1. In Supabase dashboard, go to **Table Editor**
2. Check **rooms** table: Should have 7 rows
3. Check **services** table: Should have 15+ rows
4. Check **knowledge_base** table: Should have 13+ rows
5. Check **message_templates** table: Should have templates

## Method 2: Supabase CLI (Alternative)

### Prerequisites

Install Supabase CLI:
```bash
npm install -g supabase
```

### Step 1: Initialize Supabase

```bash
# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-ref
```

### Step 2: Run Migration

```bash
# Apply migration
supabase db push

# Or run specific migration
supabase db execute --file supabase/migrations/001_create_initial_schema.sql
```

### Step 3: Run Seed Script

```bash
# Set environment variables
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-service-role-key

# Run seed script
python scripts/seed_data_v2.py
```

## Method 3: Python Script (Automated)

### Create Migration Runner Script

Create `scripts/run_migrations.py`:

```python
#!/usr/bin/env python3
"""
Run database migrations on Supabase.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client

def run_migration(supabase: Client, migration_file: Path):
    """Run a single migration file."""
    print(f"Running migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        # Execute SQL
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        print(f"✓ Migration {migration_file.name} completed successfully")
        return True
    except Exception as e:
        print(f"✗ Migration {migration_file.name} failed: {e}")
        return False

def main():
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set")
        sys.exit(1)
    
    # Create client
    supabase = create_client(url, key)
    
    # Get migration files
    migrations_dir = Path(__file__).parent.parent / 'supabase' / 'migrations'
    migration_files = sorted(migrations_dir.glob('*.sql'))
    
    if not migration_files:
        print("No migration files found")
        sys.exit(1)
    
    print(f"Found {len(migration_files)} migration(s)")
    
    # Run migrations
    success_count = 0
    for migration_file in migration_files:
        if run_migration(supabase, migration_file):
            success_count += 1
    
    print(f"\n{success_count}/{len(migration_files)} migrations completed successfully")
    
    if success_count == len(migration_files):
        print("\n✓ All migrations completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Some migrations failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### Run Migrations

```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-service-role-key

python scripts/run_migrations.py
python scripts/seed_data_v2.py
```

## Verification Checklist

After running migrations and seeds, verify:

### Tables Created

- [ ] contacts table exists with indexes
- [ ] rooms table exists
- [ ] equipment table exists
- [ ] services table exists with cancellation_hours column
- [ ] appointments table exists with all status constraints
- [ ] sessions table exists
- [ ] logs table exists with JSONB columns
- [ ] message_templates table exists
- [ ] knowledge_base table exists with GIN index

### Triggers Created

- [ ] update_contacts_updated_at trigger
- [ ] update_services_updated_at trigger
- [ ] update_appointments_updated_at trigger
- [ ] update_sessions_updated_at trigger
- [ ] update_templates_updated_at trigger
- [ ] update_kb_updated_at trigger

### Seed Data Populated

- [ ] 7 rooms in rooms table
- [ ] 15+ procedures in services table
- [ ] 13+ articles in knowledge_base table
- [ ] Message templates populated
- [ ] All active flags set to true

### Test Queries

Run these queries in Supabase SQL Editor to verify:

```sql
-- Check table counts
SELECT 'rooms' as table_name, COUNT(*) as count FROM rooms
UNION ALL
SELECT 'services', COUNT(*) FROM services
UNION ALL
SELECT 'knowledge_base', COUNT(*) FROM knowledge_base
UNION ALL
SELECT 'message_templates', COUNT(*) FROM message_templates;

-- Check indexes
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;

-- Check triggers
SELECT trigger_name, event_object_table 
FROM information_schema.triggers 
WHERE trigger_schema = 'public';

-- Test a simple insert
INSERT INTO contacts (phone, name, consent) 
VALUES ('+5594999999999', 'Test User', true);

-- Verify updated_at trigger works
SELECT id, name, created_at, updated_at FROM contacts WHERE phone = '+5594999999999';

-- Clean up test data
DELETE FROM contacts WHERE phone = '+5594999999999';
```

## Troubleshooting

### Migration Fails: "relation already exists"

**Cause:** Tables already exist from previous migration

**Solution:**
1. Drop existing tables (CAUTION: This deletes all data):
   ```sql
   DROP TABLE IF EXISTS logs CASCADE;
   DROP TABLE IF EXISTS sessions CASCADE;
   DROP TABLE IF EXISTS appointments CASCADE;
   DROP TABLE IF EXISTS services CASCADE;
   DROP TABLE IF EXISTS equipment CASCADE;
   DROP TABLE IF EXISTS rooms CASCADE;
   DROP TABLE IF EXISTS contacts CASCADE;
   DROP TABLE IF EXISTS message_templates CASCADE;
   DROP TABLE IF EXISTS knowledge_base CASCADE;
   ```

2. Re-run migration

### Seed Script Fails: "duplicate key value"

**Cause:** Seed data already exists

**Solution:**
1. Check existing data:
   ```sql
   SELECT COUNT(*) FROM rooms;
   SELECT COUNT(*) FROM services;
   ```

2. If data exists and is correct, skip seeding

3. If data is incorrect, delete and re-seed:
   ```sql
   DELETE FROM services;
   DELETE FROM rooms;
   DELETE FROM knowledge_base;
   DELETE FROM message_templates;
   ```

### Permission Denied Errors

**Cause:** Using anon key instead of service_role key

**Solution:**
- Verify you're using the service_role key (starts with `eyJ...`)
- Get it from Supabase dashboard → Settings → API → service_role key

### Connection Timeout

**Cause:** Network issues or incorrect URL

**Solution:**
- Verify SUPABASE_URL is correct
- Check internet connection
- Try from different network
- Check Supabase status page

## Rollback Procedures

### Rollback Migration

If migration causes issues:

1. **Backup data first** (if any exists):
   ```sql
   -- Export to CSV via Supabase dashboard
   ```

2. **Drop all tables**:
   ```sql
   DROP TABLE IF EXISTS logs CASCADE;
   DROP TABLE IF EXISTS sessions CASCADE;
   DROP TABLE IF EXISTS appointments CASCADE;
   DROP TABLE IF EXISTS services CASCADE;
   DROP TABLE IF EXISTS equipment CASCADE;
   DROP TABLE IF EXISTS rooms CASCADE;
   DROP TABLE IF EXISTS contacts CASCADE;
   DROP TABLE IF EXISTS message_templates CASCADE;
   DROP TABLE IF EXISTS knowledge_base CASCADE;
   DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
   ```

3. **Re-run migration** with fixes

### Rollback Seed Data

To remove seed data:

```sql
-- Remove seed data (keeps structure)
DELETE FROM knowledge_base;
DELETE FROM message_templates;
DELETE FROM services;
DELETE FROM equipment;
DELETE FROM rooms;

-- Verify tables are empty
SELECT COUNT(*) FROM rooms;
SELECT COUNT(*) FROM services;
```

## Production Deployment Checklist

When deploying to production:

- [ ] Backup existing database (if any)
- [ ] Run migrations in maintenance window
- [ ] Verify all tables created
- [ ] Run seed scripts
- [ ] Verify seed data
- [ ] Test application connectivity
- [ ] Run verification queries
- [ ] Update Railway environment variables if needed
- [ ] Test end-to-end flow
- [ ] Monitor logs for errors
- [ ] Document any issues

## Maintenance

### Adding New Migrations

1. Create new migration file: `002_description.sql`
2. Follow naming convention: `XXX_description.sql`
3. Include rollback instructions in comments
4. Test locally first
5. Apply to production during maintenance window

### Updating Seed Data

1. Modify `scripts/seed_data_v2.py`
2. Use upsert to avoid duplicates
3. Test locally first
4. Run on production
5. Verify changes

### Regular Maintenance

**Weekly:**
- Check table sizes
- Review slow queries
- Optimize indexes if needed

**Monthly:**
- Vacuum tables
- Update statistics
- Review and archive old logs

## Support

- **Supabase Documentation:** https://supabase.com/docs
- **Supabase Support:** https://supabase.com/support
- **Project Issues:** Create issue in GitHub repository

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-16  
**Requirements:** 3.1, 3.2
