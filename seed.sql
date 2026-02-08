-- Seed Data for Task Extraction System

-- Insert Participants (healthcare workers)
INSERT INTO participants (name, role, department, email) VALUES
('Dr. Sarah Chen', 'Physician', 'Cardiology', 'sarah.chen@hospital.org'),
('Nurse Mike Johnson', 'Registered Nurse', 'Emergency', 'mike.johnson@hospital.org'),
('Dr. Emily Rodriguez', 'Physician', 'Internal Medicine', 'emily.rodriguez@hospital.org'),
('Dr. James Wilson', 'Physician', 'Surgery', 'james.wilson@hospital.org'),
('Lisa Thompson', 'Care Coordinator', 'Patient Services', 'lisa.thompson@hospital.org');

-- Insert Patients
INSERT INTO patients (name, mrn, date_of_birth, high_acuity, critical_status) VALUES
('John Davis', 'MRN001234', '1965-03-15', false, false),
('Maria Garcia', 'MRN005678', '1978-07-22', true, false),
('Robert Smith', 'MRN009012', '1952-11-08', true, true),
('Jennifer Lee', 'MRN003456', '1990-05-30', false, false);

-- Insert Task Categories
INSERT INTO task_categories (category_name, description, requires_patient, requires_participant, requires_due_date) VALUES
('Medication Review', 'Review and update patient medications', true, true, false),
('Lab Follow-up', 'Follow up on laboratory results', true, true, true),
('Patient Call', 'Call patient for various reasons', true, true, false),
('Administrative', 'Administrative tasks not patient-specific', false, true, false);

-- Insert Category SLAs
INSERT INTO category_sla (category_id, sla_hours, escalation_hours, description) VALUES
(1, 48, 72, 'Medication reviews should be completed within 48 hours'),
(2, 24, 36, 'Lab follow-ups are time-sensitive and should be done within 24 hours'),
(3, 72, 96, 'Patient calls should be completed within 3 days'),
(4, 120, 168, 'Administrative tasks have a 5-day SLA');

-- Insert Priority Weights
INSERT INTO priority_weights (weight_name, weight_category, weight_value, description) VALUES
-- Urgency weights
('urgent_keyword', 'urgency', 15.00, 'Weight added when "urgent" is mentioned'),
('asap_keyword', 'urgency', 20.00, 'Weight added when "asap" or "as soon as possible" is mentioned'),
('stat_keyword', 'urgency', 25.00, 'Weight added when "stat" is mentioned'),
('critical_keyword', 'urgency', 20.00, 'Weight added when "critical" is mentioned'),

-- Category weights
('medication_review_category', 'category', 10.00, 'Base weight for medication review tasks'),
('lab_followup_category', 'category', 20.00, 'Base weight for lab follow-up tasks'),
('patient_call_category', 'category', 5.00, 'Base weight for patient call tasks'),
('administrative_category', 'category', 2.00, 'Base weight for administrative tasks'),

-- Acuity weights
('high_acuity_patient', 'acuity', 15.00, 'Weight for high acuity patients'),
('critical_status_patient', 'acuity', 25.00, 'Weight for critical status patients'),

-- Complexity weights
('complex_task', 'complexity', -5.00, 'Complex tasks may need more time (negative weight)'),
('routine_task', 'complexity', 5.00, 'Routine tasks can be prioritized higher'),

-- SLA weights
('sla_near_breach_25', 'sla', 20.00, 'Weight when <25% of SLA time remaining'),
('sla_near_breach_50', 'sla', 10.00, 'Weight when <50% of SLA time remaining');

-- Insert Task Policy
INSERT INTO task_policies (policy_version, policy_data, active) VALUES
('v1.0.0', '{
  "version": "1.0.0",
  "effective_date": "2025-01-01",
  "rules": {
    "extraction": {
      "min_description_length": 10,
      "max_description_length": 1000,
      "required_confidence": 0.7,
      "ambiguity_threshold": 0.5
    },
    "normalization": {
      "default_sla_application": true,
      "auto_category_matching": true,
      "require_source_spans": true
    },
    "qa": {
      "critical_fields": ["description"],
      "reject_on_invalid_ids": true,
      "max_null_required_fields": 1,
      "min_qa_confidence": 0.8
    },
    "prioritization": {
      "score_range": [0, 100],
      "default_base_score": 50.0,
      "priority_thresholds": {
        "critical": 80,
        "high": 60,
        "medium": 40,
        "low": 20,
        "minimal": 0
      }
    }
  },
  "category_requirements": {
    "Medication Review": {
      "required_fields": ["patient_id", "description"],
      "optional_fields": ["due_date"],
      "validation_rules": [
        {
          "rule_id": "MR001",
          "description": "Patient must be specified for medication reviews",
          "severity": "critical"
        }
      ]
    },
    "Lab Follow-up": {
      "required_fields": ["patient_id", "description", "due_date"],
      "optional_fields": [],
      "validation_rules": [
        {
          "rule_id": "LF001",
          "description": "Lab follow-ups must have a due date",
          "severity": "critical"
        },
        {
          "rule_id": "LF002",
          "description": "Patient must be specified for lab follow-ups",
          "severity": "critical"
        }
      ]
    },
    "Patient Call": {
      "required_fields": ["patient_id", "description"],
      "optional_fields": ["due_date"],
      "validation_rules": [
        {
          "rule_id": "PC001",
          "description": "Patient must be specified for patient calls",
          "severity": "critical"
        }
      ]
    },
    "Administrative": {
      "required_fields": ["description"],
      "optional_fields": ["participant_id", "due_date"],
      "validation_rules": []
    }
  },
  "business_rules": {
    "duplicate_prevention": false,
    "participant_authority_check": false,
    "reasonable_due_date_days": 365
  }
}', true);

-- Insert Sample Transcripts
INSERT INTO transcripts (transcript_text, source, recorded_at) VALUES
('Dr. Chen here. I need to review Maria Garcia''s medications ASAP. Her MRN is MRN005678. She mentioned some side effects during her last visit. This is urgent and should be done by tomorrow.', 
 'audio', 
 CURRENT_TIMESTAMP - INTERVAL '2 hours'),

('Mike Johnson speaking. We need to follow up on Robert Smith''s lab results from yesterday. MRN009012. His potassium levels were critical. Please call him today.',
 'audio',
 CURRENT_TIMESTAMP - INTERVAL '1 hour'),

('This is Emily Rodriguez. Can someone schedule a call with Jennifer Lee, MRN003456, to discuss her discharge plan? No rush, sometime this week is fine.',
 'audio',
 CURRENT_TIMESTAMP - INTERVAL '30 minutes'),

('Administrative note: We need to update the patient intake forms. This should be done by end of month.',
 'manual',
 CURRENT_TIMESTAMP - INTERVAL '15 minutes');

-- Verify seed data
SELECT 'Participants' as table_name, COUNT(*) as row_count FROM participants
UNION ALL
SELECT 'Patients', COUNT(*) FROM patients
UNION ALL
SELECT 'Task Categories', COUNT(*) FROM task_categories
UNION ALL
SELECT 'Category SLAs', COUNT(*) FROM category_sla
UNION ALL
SELECT 'Priority Weights', COUNT(*) FROM priority_weights
UNION ALL
SELECT 'Task Policies', COUNT(*) FROM task_policies
UNION ALL
SELECT 'Transcripts', COUNT(*) FROM transcripts;
