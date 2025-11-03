# Jobs Module - Scheduled Tasks

This module contains scheduled jobs for the Clínica Luana multi-agent system.

## Overview

The jobs module implements automated background tasks that run on a schedule to send reminders and feedback requests to patients.

## Jobs

### 1. Reminder Job (`reminder_job.py`)

**Purpose:** Send appointment reminders to patients

**Schedule:** Every 30 minutes

**Functions:**
- `send_d1_reminders()` - Sends D-1 reminders (18-26 hours before appointment)
- `send_h2_reminders()` - Sends H-2 reminders (1.5-2.5 hours before appointment)
- `run_reminder_job()` - Main function that runs both D-1 and H-2 reminders

**Requirements:** 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8

**Features:**
- Queries appointments in specific time windows
- Checks if reminders were already sent (avoids duplicates)
- Retrieves contact and service details
- Formats personalized messages
- Marks reminders as sent in database
- Comprehensive error handling and logging

**D-1 Reminder Content:**
- Appointment date and time
- Procedure name
- Room assignment
- Arrival instructions
- Contact information

**H-2 Reminder Content:**
- Appointment time (today)
- Procedure name
- Late policy reminder (10 minutes max)
- Clinic location

### 2. Feedback Job (`feedback_job.py`)

**Purpose:** Send post-treatment feedback requests to patients

**Schedule:** Daily at 10:00 AM

**Functions:**
- `send_feedback_requests()` - Sends feedback requests for completed appointments
- `run_feedback_job()` - Main function that runs the feedback job

**Requirements:** 17.1, 17.2, 17.3, 17.5

**Features:**
- Queries completed appointments from 24 hours ago (23-25h window)
- Checks if feedback was already sent (avoids duplicates)
- Uses message templates when available
- Logs feedback requests to prevent duplicates
- Comprehensive error handling and logging

**Feedback Request Content:**
- Personalized greeting
- Treatment/procedure name
- Questions about experience
- Invitation for feedback
- Contact information

## Configuration

### APScheduler Setup (in `main.py`)

```python
# Reminder job - runs every 30 minutes
scheduler.add_job(
    run_reminder_job,
    trigger=IntervalTrigger(minutes=30),
    id='reminder_job',
    name='Send appointment reminders (D-1 and H-2)',
    replace_existing=True,
    max_instances=1,
    misfire_grace_time=300  # 5 minutes
)

# Feedback job - runs daily at 10:00
scheduler.add_job(
    run_feedback_job,
    trigger=CronTrigger(hour=10, minute=0),
    id='feedback_job',
    name='Send post-treatment feedback requests',
    replace_existing=True,
    max_instances=1,
    misfire_grace_time=600  # 10 minutes
)
```

## Dependencies

- **APScheduler:** For job scheduling
- **Followup Agent:** For sending messages via Chatwoot
- **Supabase:** For querying appointments and contacts
- **Repository Layer:** For database operations

## Monitoring

### Scheduler Status Endpoint

```
GET /scheduler/status
```

Returns:
```json
{
  "status": "running",
  "jobs": [
    {
      "id": "reminder_job",
      "name": "Send appointment reminders (D-1 and H-2)",
      "next_run": "2025-10-16T14:30:00",
      "trigger": "interval[0:30:00]",
      "max_instances": 1
    },
    {
      "id": "feedback_job",
      "name": "Send post-treatment feedback requests",
      "next_run": "2025-10-17T10:00:00",
      "trigger": "cron[hour='10', minute='0']",
      "max_instances": 1
    }
  ],
  "job_count": 2,
  "timestamp": "2025-10-16T14:15:30"
}
```

## Logging

All jobs log their execution with structured logging:

**Reminder Job Logs:**
- Job start/completion
- Appointments found and processed
- Reminders sent successfully
- Reminders failed (with reasons)
- Errors with full stack traces

**Feedback Job Logs:**
- Job start/completion
- Completed appointments found
- Feedback requests sent
- Feedback requests failed (with reasons)
- Errors with full stack traces

## Error Handling

Both jobs implement comprehensive error handling:

1. **Database Errors:** Caught and logged, job continues with other appointments
2. **Missing Data:** Skips appointments with missing contact/service data
3. **Chatwoot API Errors:** Logged with retry information
4. **Unexpected Errors:** Caught at job level, logged with full context

## Testing

To manually trigger jobs (for testing):

```python
# Test reminder job
from jobs.reminder_job import run_reminder_job
import asyncio

result = asyncio.run(run_reminder_job())
print(result)

# Test feedback job
from jobs.feedback_job import run_feedback_job

result = asyncio.run(run_feedback_job())
print(result)
```

## Future Enhancements

1. **Retry Logic:** Implement exponential backoff for failed messages
2. **Batch Processing:** Process appointments in batches for better performance
3. **Custom Schedules:** Allow per-patient reminder preferences
4. **Analytics:** Track reminder effectiveness and feedback response rates
5. **A/B Testing:** Test different message templates for better engagement
