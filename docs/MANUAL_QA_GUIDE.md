# Manual QA Testing Guide

## Overview

This guide provides comprehensive instructions for executing manual QA tests on the Clínica Luana Multi-Agent System. The testing covers 24 real-world conversation scenarios across three categories:

- **8 FAQ Conversations**: Treatment information, pricing, policies, contraindications
- **8 Scheduling Conversations**: Booking flows, availability, confirmations
- **8 Rescheduling/Cancellation Conversations**: Policy validation, limits, no-show scenarios

## Requirements Covered

- **5.1-5.5**: FAQ Agent functionality
- **2.1-2.8**: Scheduling Agent functionality
- **3.1-3.3**: Booking creation and confirmation
- **4.1-4.8**: Rescheduling and cancellation policies
- **11.1-11.5**: Success criteria validation

## Prerequisites

### Required Access

1. **WhatsApp**: Access to test phone number for sending messages
2. **Chatwoot**: Admin access to view conversations and escalations
3. **Supabase**: Read access to verify bookings and logs
4. **System**: Running deployment (local or Railway)

### Environment Setup

```bash
# Ensure system is running
python scripts/verify_deployment.py

# Check health endpoint
curl http://localhost:8000/health

# Or for Railway deployment
curl https://your-app.railway.app/health
```

### Test Data Preparation

- Use unique phone numbers for each test to avoid conflicts
- Clear any existing test data from previous runs
- Ensure knowledge base is populated with clinic information

## Running the Tests

### Interactive Test Guide

The recommended approach is to use the interactive test guide script:

```bash
# Run all 24 tests
python scripts/manual_qa_test_guide.py

# Run specific category
python scripts/manual_qa_test_guide.py --category faq
python scripts/manual_qa_test_guide.py --category scheduling
python scripts/manual_qa_test_guide.py --category rescheduling

# Save results to specific file
python scripts/manual_qa_test_guide.py --output my_test_results.json
```

### Test Execution Flow

For each test case, the script will:

1. **Display test details**: ID, title, description, requirements
2. **Show expected behavior**: What the system should do
3. **Provide validation steps**: How to verify correct behavior
4. **Wait for tester**: Pause while you execute the test
5. **Record results**: Capture pass/fail status and notes
6. **Track metrics**: Latency, booking creation, message delivery

### Manual Execution (Without Script)

If you prefer to run tests manually without the script:

1. Open the test case list in `scripts/manual_qa_test_guide.py`
2. For each test case:
   - Send the specified message via WhatsApp
   - Observe system response
   - Validate against expected behavior
   - Check validation steps
   - Record result in spreadsheet or document

## Test Categories

### Category 1: FAQ Conversations (8 tests)

**Purpose**: Validate FAQ Agent's ability to answer questions about treatments, pricing, and policies.

**Test Cases**:
- FAQ-01: Treatment information (depilação a laser)
- FAQ-02: Fixed pricing queries
- FAQ-03: Consultation-based pricing (harmonização)
- FAQ-04: Cancellation policies
- FAQ-05: Contraindications
- FAQ-06: Post-treatment care
- FAQ-07: Business hours
- FAQ-08: Escalation to human agent

**Key Validations**:
- ✓ Accurate information from knowledge base
- ✓ Professional and welcoming tone
- ✓ Use of message templates when applicable
- ✓ Proper escalation when needed
- ✓ Low confidence signaling

### Category 2: Scheduling Conversations (8 tests)

**Purpose**: Validate Scheduler Agent's ability to handle booking requests with business rule enforcement.

**Test Cases**:
- SCH-01: Simple booking with available slot
- SCH-02: No available slots
- SCH-03: Outside business hours (Sunday)
- SCH-04: Insufficient advance notice (< 1 hour)
- SCH-05: Confirmation flow
- SCH-06: Check existing bookings
- SCH-07: Multiple services inquiry
- SCH-08: Consultation booking

**Key Validations**:
- ✓ Business hours respected (Mon-Fri 08:30-19:00, Sat 08:30-12:00)
- ✓ Minimum 1-hour advance booking
- ✓ Explicit confirmation before creating booking
- ✓ Booking appears in database with correct status
- ✓ Confirmation message sent via WhatsApp
- ✓ Room and equipment allocation

### Category 3: Rescheduling/Cancellation (8 tests)

**Purpose**: Validate policy enforcement for cancellations and rescheduling limits.

**Test Cases**:
- RES-01: Valid cancellation (within policy)
- RES-02: Invalid cancellation (outside policy)
- RES-03: First rescheduling attempt
- RES-04: Second rescheduling attempt
- RES-05: Third attempt (blocked)
- RES-06: Cancel non-existent booking
- RES-07: Reschedule to unavailable slot
- RES-08: No-show policy explanation

**Key Validations**:
- ✓ Cancellation policies enforced (4h harmonização, 24h laser)
- ✓ Rescheduling limit of 2 enforced
- ✓ Counter incremented correctly in database
- ✓ No-show policy explained clearly
- ✓ Escalation offered for special cases

## Success Criteria

### Requirement 11.1: Zero 5xx Errors

**Validation**:
```sql
-- Check logs for 5xx errors in last hour
SELECT COUNT(*) 
FROM logs 
WHERE ts > NOW() - INTERVAL '1 hour'
  AND error_message LIKE '5%';
```

**Expected**: 0 errors

### Requirement 11.2: 100% Booking Creation

**Validation**:
```sql
-- Check bookings created during test session
SELECT id, contact_id, service_id, status, created_at
FROM appointments
WHERE created_at > 'TEST_START_TIME'
ORDER BY created_at DESC;
```

**Expected**: All scheduling tests that should create bookings have corresponding records

### Requirement 11.3: Correct Status Updates

**Validation**:
```sql
-- Check cancellation and rescheduling updates
SELECT id, status, reschedule_count, cancellation_reason
FROM appointments
WHERE updated_at > 'TEST_START_TIME'
  AND status IN ('cancelled', 'confirmed');
```

**Expected**: Status reflects test actions correctly

### Requirement 11.4: P95 Latency ≤ 7 seconds

**Validation**: Script automatically calculates P95 from recorded latencies

**Expected**: P95 ≤ 7000ms

### Requirement 11.5: All Messages Delivered

**Validation**: Manual verification that all responses were received via WhatsApp

**Expected**: 100% delivery rate

## Validation Checklist

### Pre-Test Validation

- [ ] System health check passes
- [ ] Supabase connection working
- [ ] Redis connection working
- [ ] Chatwoot webhook configured
- [ ] Knowledge base populated
- [ ] Test phone numbers ready

### During Test Validation

For each test:
- [ ] Message sent successfully
- [ ] Response received within reasonable time
- [ ] Response content matches expected behavior
- [ ] Tone and language appropriate
- [ ] No errors or incorrect information

### Post-Test Validation

- [ ] All 24 tests executed
- [ ] Results recorded for each test
- [ ] Database state verified
- [ ] Logs checked for errors
- [ ] Metrics calculated
- [ ] Success criteria evaluated

## Common Issues and Troubleshooting

### Issue: No Response from System

**Possible Causes**:
- Webhook not configured correctly
- System not running
- LLM provider timeout
- Redis connection issue

**Resolution**:
1. Check system health: `GET /health`
2. Verify webhook in Chatwoot settings
3. Check Railway logs for errors
4. Verify environment variables

### Issue: Incorrect Information in Responses

**Possible Causes**:
- Knowledge base not populated
- Outdated information in KB
- LLM hallucination

**Resolution**:
1. Verify KB data: `SELECT * FROM knowledge_base WHERE active = true`
2. Update KB if needed: `python scripts/seed_data_v2.py`
3. Check FAQ agent prompt for accuracy

### Issue: Booking Not Created

**Possible Causes**:
- Validation failed (business hours, advance time)
- Database connection issue
- Confirmation not provided

**Resolution**:
1. Check validation rules in scheduler_tools.py
2. Verify Supabase connection
3. Ensure explicit confirmation was given

### Issue: Escalation Not Working

**Possible Causes**:
- Chatwoot API credentials incorrect
- Assignment logic failing
- Automation pause not set

**Resolution**:
1. Verify CHATWOOT_API_TOKEN in environment
2. Check Chatwoot API logs
3. Verify sessions table has automation_paused flag

## Reporting Results

### Automated Report

The test script generates a JSON report with:
- Timestamp and test metadata
- Individual test results
- Pass/fail counts by category
- P95 latency calculation
- Database verification results

**Location**: `test_results/manual_qa_results_YYYYMMDD_HHMMSS.json`

### Manual Report Template

If not using the script, document results in this format:

```markdown
# Manual QA Test Results

**Date**: YYYY-MM-DD
**Tester**: [Name]
**Environment**: [Local/Railway]
**Duration**: [Time]

## Summary
- Total Tests: 24
- Passed: X
- Failed: Y
- Skipped: Z

## FAQ Tests (8)
- FAQ-01: ✅ PASSED - [notes]
- FAQ-02: ✅ PASSED - [notes]
...

## Scheduling Tests (8)
- SCH-01: ✅ PASSED - [notes]
...

## Rescheduling Tests (8)
- RES-01: ✅ PASSED - [notes]
...

## Success Criteria
- [ ] 0 errors 5xx
- [ ] P95 latency ≤ 7s
- [ ] 100% bookings in database
- [ ] All messages delivered

## Issues Found
1. [Description]
2. [Description]

## Recommendations
1. [Recommendation]
2. [Recommendation]
```

## Next Steps After QA

### If All Tests Pass

1. Document results in project repository
2. Update task status in tasks.md
3. Proceed to Task 20 (Documentation)
4. Prepare for go-live (Task 21)

### If Tests Fail

1. Document failures with detailed notes
2. Create issues for each failure
3. Prioritize fixes based on severity
4. Re-run failed tests after fixes
5. Repeat until all tests pass

## Tips for Effective Testing

1. **Test in Order**: Follow the sequence (FAQ → Scheduling → Rescheduling)
2. **Take Notes**: Document unexpected behaviors immediately
3. **Use Fresh Data**: Start with clean test data for each run
4. **Verify Database**: Always check database state after scheduling tests
5. **Test Edge Cases**: Don't just test happy paths
6. **Monitor Logs**: Keep an eye on system logs during testing
7. **Take Breaks**: Testing 24 scenarios takes time - pace yourself
8. **Document Everything**: More notes = easier debugging

## Reference

- **Requirements**: `.kiro/specs/multi-agent-scheduling/requirements.md`
- **Design**: `.kiro/specs/multi-agent-scheduling/design.md`
- **Tasks**: `.kiro/specs/multi-agent-scheduling/tasks.md`
- **Test Script**: `scripts/manual_qa_test_guide.py`
- **E2E Tests**: `tests/test_e2e.py` (automated reference)

## Contact

For questions or issues during testing:
- Check documentation in `docs/` directory
- Review error handling guide: `docs/ERROR_HANDLING_GUIDE.md`
- Consult agents guide: `docs/AGENTS_GUIDE.md`
