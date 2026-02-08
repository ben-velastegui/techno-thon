-- Task Extraction System Database Schema
-- PostgreSQL compatible DDL

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS transcripts CASCADE;
DROP TABLE IF EXISTS priority_weights CASCADE;
DROP TABLE IF EXISTS category_sla CASCADE;
DROP TABLE IF EXISTS task_policies CASCADE;
DROP TABLE IF EXISTS task_categories CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS participants CASCADE;

-- Participants (healthcare workers)
CREATE TABLE participants (
    participant_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_participants_name ON participants(name);
CREATE INDEX idx_participants_role ON participants(role);

-- Patients
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mrn VARCHAR(50) UNIQUE NOT NULL, -- Medical Record Number
    date_of_birth DATE,
    high_acuity BOOLEAN DEFAULT false,
    critical_status BOOLEAN DEFAULT false,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patients_mrn ON patients(mrn);
CREATE INDEX idx_patients_name ON patients(name);
CREATE INDEX idx_patients_acuity ON patients(high_acuity, critical_status);

-- Task Categories
CREATE TABLE task_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    requires_patient BOOLEAN DEFAULT false,
    requires_participant BOOLEAN DEFAULT true,
    requires_due_date BOOLEAN DEFAULT false,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_task_categories_name ON task_categories(category_name);

-- Task Policies (JSON-based policy storage)
CREATE TABLE task_policies (
    policy_id SERIAL PRIMARY KEY,
    policy_version VARCHAR(50) NOT NULL UNIQUE,
    policy_data JSONB NOT NULL, -- Stores complete policy as JSON
    active BOOLEAN DEFAULT true,
    effective_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_task_policies_version ON task_policies(policy_version);
CREATE INDEX idx_task_policies_active ON task_policies(active);

-- Category SLA (Service Level Agreements)
CREATE TABLE category_sla (
    sla_id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES task_categories(category_id),
    sla_hours INTEGER NOT NULL,
    escalation_hours INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id)
);

CREATE INDEX idx_category_sla_category ON category_sla(category_id);

-- Priority Weights (for scoring algorithm)
CREATE TABLE priority_weights (
    weight_id SERIAL PRIMARY KEY,
    weight_name VARCHAR(100) NOT NULL UNIQUE,
    weight_category VARCHAR(50) NOT NULL, -- 'urgency', 'category', 'acuity', 'complexity', 'sla'
    weight_value NUMERIC(10, 2) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_priority_weights_category ON priority_weights(weight_category);
CREATE INDEX idx_priority_weights_name ON priority_weights(weight_name);

-- Transcripts (source data)
CREATE TABLE transcripts (
    transcript_id SERIAL PRIMARY KEY,
    transcript_text TEXT NOT NULL,
    source VARCHAR(100), -- 'audio', 'manual', 'import', etc.
    recorded_at TIMESTAMP,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transcripts_recorded_at ON transcripts(recorded_at);

-- Tasks (final extracted and prioritized tasks)
CREATE TABLE tasks (
    task_id SERIAL PRIMARY KEY,
    transcript_id INTEGER REFERENCES transcripts(transcript_id),
    participant_id INTEGER REFERENCES participants(participant_id),
    patient_id INTEGER REFERENCES patients(patient_id),
    category_id INTEGER REFERENCES task_categories(category_id),
    
    -- Core task data
    description TEXT NOT NULL,
    due_date TIMESTAMP,
    expected_completion_date TIMESTAMP,
    
    -- Priority data
    priority_score NUMERIC(5, 2) NOT NULL CHECK (priority_score >= 0 AND priority_score <= 100),
    priority_level VARCHAR(20) NOT NULL CHECK (priority_level IN ('critical', 'high', 'medium', 'low', 'minimal')),
    
    -- Provenance data (stored as JSON)
    source_spans JSONB, -- Character offsets from transcript
    enriched_fields JSONB, -- Computed and enriched data
    score_breakdown JSONB, -- Priority calculation details
    
    -- Lineage tracking
    lineage_metadata JSONB NOT NULL, -- Processing chain
    qa_metadata JSONB NOT NULL, -- QA validation details
    prioritization_metadata JSONB NOT NULL, -- Priority calculation metadata
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
    completed_at TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tasks
CREATE INDEX idx_tasks_participant ON tasks(participant_id);
CREATE INDEX idx_tasks_patient ON tasks(patient_id);
CREATE INDEX idx_tasks_category ON tasks(category_id);
CREATE INDEX idx_tasks_priority ON tasks(priority_level, priority_score);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_transcript ON tasks(transcript_id);

-- GIN index for JSONB fields (for fast JSON queries)
CREATE INDEX idx_tasks_lineage_gin ON tasks USING GIN (lineage_metadata);
CREATE INDEX idx_tasks_source_spans_gin ON tasks USING GIN (source_spans);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE participants IS 'Healthcare workers who create tasks';
COMMENT ON TABLE patients IS 'Patients referenced in tasks';
COMMENT ON TABLE task_categories IS 'Task classification categories';
COMMENT ON TABLE task_policies IS 'JSON-based policy definitions';
COMMENT ON TABLE category_sla IS 'Service level agreements per category';
COMMENT ON TABLE priority_weights IS 'Weights for priority scoring algorithm';
COMMENT ON TABLE transcripts IS 'Source transcripts for task extraction';
COMMENT ON TABLE tasks IS 'Extracted, validated, and prioritized tasks';

COMMENT ON COLUMN tasks.source_spans IS 'JSON object with character offsets tracking data provenance in transcript';
COMMENT ON COLUMN tasks.lineage_metadata IS 'Complete processing chain with agent versions and timestamps';
COMMENT ON COLUMN tasks.priority_score IS 'Calculated priority score (0-100)';
