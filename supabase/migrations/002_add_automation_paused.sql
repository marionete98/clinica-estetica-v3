-- Migration: Add automation_paused field to sessions table
-- Purpose: Support human takeover functionality
-- Date: 2025-10-16

-- Add automation_paused column to sessions table
ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS automation_paused BOOLEAN DEFAULT FALSE;

-- Add human_takeover_reason column for tracking why automation was paused
ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS human_takeover_reason TEXT;

-- Create index for faster queries on automation_paused
CREATE INDEX IF NOT EXISTS idx_sessions_automation_paused 
ON sessions(automation_paused) 
WHERE automation_paused = TRUE;

-- Add comment
COMMENT ON COLUMN sessions.automation_paused IS 'Flag indicating if AI automation is paused for human takeover';
COMMENT ON COLUMN sessions.human_takeover_reason IS 'Reason why automation was paused (e.g., escalation, explicit request)';
