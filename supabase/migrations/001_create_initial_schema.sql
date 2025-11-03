-- Migration: Create initial schema for Clínica Luana multi-agent scheduling system
-- Date: 2025-10-16
-- Requirements: 3.1, 3.2, 3.3, 16.1

-- ============================================================================
-- CONTACTS TABLE
-- ============================================================================
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    consent BOOLEAN DEFAULT false,
    no_show_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contacts_phone ON contacts(phone);

COMMENT ON TABLE contacts IS 'Patient contact information';
COMMENT ON COLUMN contacts.phone IS 'Brazilian phone number in format (XX) XXXXX-XXXX';
COMMENT ON COLUMN contacts.consent IS 'LGPD consent for data processing';
COMMENT ON COLUMN contacts.no_show_count IS 'Number of no-show occurrences';

-- ============================================================================
-- ROOMS TABLE
-- ============================================================================
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    room_type VARCHAR(50),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE rooms IS 'Treatment rooms available in the clinic';
COMMENT ON COLUMN rooms.room_type IS 'Type: treatment, consultation, laser, cryo';

-- ============================================================================
-- EQUIPMENT TABLE
-- ============================================================================
CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    equipment_type VARCHAR(50),
    room_id UUID REFERENCES rooms(id),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_equipment_room ON equipment(room_id);

COMMENT ON TABLE equipment IS 'Medical equipment available for treatments';

-- ============================================================================
-- SERVICES TABLE
-- ============================================================================
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    duration_min INTEGER NOT NULL,
    price_fixed DECIMAL(10,2),
    requires_consultation BOOLEAN DEFAULT false,
    consultation_price DECIMAL(10,2),
    cancellation_hours INTEGER DEFAULT 24,
    room_id UUID REFERENCES rooms(id),
    equipment_id UUID REFERENCES equipment(id),
    active BOOLEAN DEFAULT true,
    description TEXT,
    contraindications TEXT,
    post_treatment_care TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_services_category ON services(category);
CREATE INDEX idx_services_active ON services(active);

COMMENT ON TABLE services IS 'Aesthetic procedures offered by the clinic';
COMMENT ON COLUMN services.category IS 'Category: Facial, Corporal, Pós-Operatório, Emagrecimento';
COMMENT ON COLUMN services.price_fixed IS 'Fixed price in BRL, NULL if requires consultation';
COMMENT ON COLUMN services.cancellation_hours IS 'Minimum hours required for cancellation (4h harmonization, 24h laser)';

-- ============================================================================
-- APPOINTMENTS TABLE
-- ============================================================================
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id UUID REFERENCES contacts(id) NOT NULL,
    service_id UUID REFERENCES services(id) NOT NULL,
    room_id UUID REFERENCES rooms(id),
    equipment_id UUID REFERENCES equipment(id),
    conversation_id VARCHAR(255),
    start_ts TIMESTAMPTZ NOT NULL,
    end_ts TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed',
    reschedule_count INTEGER DEFAULT 0,
    reminder_d1_sent BOOLEAN DEFAULT false,
    reminder_h2_sent BOOLEAN DEFAULT false,
    feedback_sent BOOLEAN DEFAULT false,
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_status CHECK (status IN ('confirmed', 'cancelled', 'no_show', 'completed'))
);

CREATE INDEX idx_appointments_start_status ON appointments(start_ts, status);
CREATE INDEX idx_appointments_contact ON appointments(contact_id);
CREATE INDEX idx_appointments_service ON appointments(service_id);
CREATE INDEX idx_appointments_conversation ON appointments(conversation_id);
CREATE INDEX idx_appointments_reminders ON appointments(start_ts, reminder_d1_sent, reminder_h2_sent) WHERE status = 'confirmed';

COMMENT ON TABLE appointments IS 'Scheduled appointments with patients';
COMMENT ON COLUMN appointments.status IS 'Status: confirmed, cancelled, no_show, completed';
COMMENT ON COLUMN appointments.reschedule_count IS 'Number of times this appointment has been rescheduled (max 2)';
COMMENT ON COLUMN appointments.reminder_d1_sent IS 'D-1 reminder sent (18-26h before)';
COMMENT ON COLUMN appointments.reminder_h2_sent IS 'H-2 reminder sent (1.5-2.5h before)';

-- ============================================================================
-- SESSIONS TABLE
-- ============================================================================
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) UNIQUE NOT NULL,
    contact_id UUID REFERENCES contacts(id),
    summary TEXT,
    last_intent VARCHAR(50),
    automation_paused BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_conversation ON sessions(conversation_id);
CREATE INDEX idx_sessions_contact ON sessions(contact_id);

COMMENT ON TABLE sessions IS 'Conversation context and state management';
COMMENT ON COLUMN sessions.conversation_id IS 'Chatwoot conversation ID';
COMMENT ON COLUMN sessions.automation_paused IS 'True when escalated to human agent';

-- ============================================================================
-- LOGS TABLE
-- ============================================================================
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ts TIMESTAMPTZ DEFAULT NOW(),
    conversation_id VARCHAR(255),
    contact_id UUID REFERENCES contacts(id),
    intent VARCHAR(50),
    provider VARCHAR(20),
    latency_ms INTEGER,
    tools_used TEXT[],
    cost_estimate DECIMAL(10,4),
    error_message TEXT,
    request_payload JSONB,
    response_payload JSONB
);

CREATE INDEX idx_logs_ts ON logs(ts DESC);
CREATE INDEX idx_logs_conversation ON logs(conversation_id);
CREATE INDEX idx_logs_intent ON logs(intent);
CREATE INDEX idx_logs_provider ON logs(provider);
CREATE INDEX idx_logs_error ON logs(ts DESC) WHERE error_message IS NOT NULL;

COMMENT ON TABLE logs IS 'Structured logs for observability and debugging';
COMMENT ON COLUMN logs.provider IS 'LLM provider: xai or gemini';
COMMENT ON COLUMN logs.latency_ms IS 'Response latency in milliseconds';
COMMENT ON COLUMN logs.cost_estimate IS 'Estimated cost in BRL for this interaction';

-- ============================================================================
-- MESSAGE TEMPLATES TABLE
-- ============================================================================
CREATE TABLE message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    variables TEXT[],
    category VARCHAR(50),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_templates_name ON message_templates(name);
CREATE INDEX idx_templates_category ON message_templates(category);

COMMENT ON TABLE message_templates IS 'Predefined message templates for standardized communication';
COMMENT ON COLUMN message_templates.variables IS 'Array of variable names like [name, date, time]';

-- ============================================================================
-- KNOWLEDGE BASE TABLE
-- ============================================================================
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    version VARCHAR(20),
    keywords TEXT[],
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_kb_category ON knowledge_base(category);
CREATE INDEX idx_kb_keywords ON knowledge_base USING GIN(keywords);
CREATE INDEX idx_kb_active ON knowledge_base(active);

COMMENT ON TABLE knowledge_base IS 'Knowledge base articles for FAQ agent';
COMMENT ON COLUMN knowledge_base.keywords IS 'Keywords for search matching';

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON services
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON message_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kb_updated_at BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
