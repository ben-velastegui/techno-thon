# Task Extraction System - POC

A deterministic, LangGraph-based task extraction system for healthcare transcripts with strict database grounding and policy enforcement.

## 🏗️ Architecture

```
Transcript → Extraction → Normalization → QA → Prioritization → Save
```

Each step is a LangGraph node operating on shared typed state:

- **Extraction**: Extracts tasks from transcript with strict DB grounding
- **Normalization**: Enriches data with SLAs, defaults, computed fields
- **QA**: Validates against policy, accepts or rejects with reason
- **Prioritization**: Calculates weighted priority score (0-100)
- **Save**: Persists to PostgreSQL database

## 📁 Project Structure

```
/agent_prompts/          # Agent system prompts (4 files)
  extraction.txt         # Extraction rules and grounding
  normalization.txt      # Normalization and enrichment
  qa.txt                 # Quality assurance validation
  prioritization.txt     # Priority scoring algorithm

/schemas/                # JSON schemas (2 files)
  task_draft_schema.json # For extraction & normalization output
  task_final_schema.json # For prioritized task ready for DB

/orchestration/          # LangGraph pipeline
  pipeline.py            # Complete state machine + DB tools

/api/                    # FastAPI REST API
  main.py                # API endpoints

database.sql             # PostgreSQL schema DDL
seed.sql                 # Sample data for testing
README.md                # This file
requirements.txt         # Python dependencies
.env.example             # Environment variables template
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- AWS Account with Bedrock access (Claude models enabled)
  - **See `AWS_SETUP.md` for detailed AWS configuration instructions**

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Create database
createdb task_extraction

# Run schema
psql -d task_extraction -f database.sql

# Load seed data
psql -d task_extraction -f seed.sql
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:

```bash
# AWS Credentials (for Bedrock access)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=task_extraction
DB_USER=postgres
DB_PASSWORD=postgres
```

### 4. Run API Server

```bash
# Optional: Test AWS Bedrock connectivity first
python test_aws_bedrock.py

# From project root
cd api
uvicorn main:app --reload

# API will be available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### 5. Test the Pipeline

```bash
curl -X POST http://localhost:8000/process_transcript \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Dr. Chen here. I need to review Maria Garcia'\''s medications ASAP. Her MRN is MRN005678. This is urgent and should be done by tomorrow."
  }'
```

## 🧠 How It Works

### State Management

The pipeline uses a strongly typed `PipelineState` object that flows through all nodes:

```python
class PipelineState(TypedDict):
    transcript: str
    db_context: Dict[str, Any]        # Grounding data
    policy_snapshot: Dict[str, Any]   # Active policy
    extracted_task: Optional[Dict]
    normalized_task: Optional[Dict]
    qa_result: Optional[Dict]
    final_task: Optional[Dict]
    rejection_reason: Optional[str]
    saved_task_id: Optional[int]
    status: Literal["pending", "rejected", "completed"]
```

### Database Grounding

Every agent receives:

1. **Participants**: All active healthcare workers (name, role, ID)
2. **Patients**: All active patients (name, MRN, acuity status)
3. **Categories**: Available task categories with requirements
4. **SLAs**: Service level agreements per category
5. **Policy**: Active policy rules and constraints

Agents CANNOT hallucinate entities - if a name/MRN doesn't exist in DB, they must set the field to `null`.

### Policy-Based Validation

Policies are stored as JSON in the database and injected into prompts at runtime:

```json
{
  "version": "v1.0.0",
  "rules": {
    "qa": {
      "critical_fields": ["description"],
      "reject_on_invalid_ids": true
    }
  },
  "category_requirements": {
    "Lab Follow-up": {
      "required_fields": ["patient_id", "due_date"]
    }
  }
}
```

**To update policies**: Just update the `task_policies` table - no code changes needed.

### Priority Scoring

Deterministic algorithm using weighted factors from `priority_weights` table:

```
priority_score = 50.0 (base)
  + urgency_weight (15-25 based on keywords)
  + category_weight (2-20 based on category)
  + acuity_weight (15-25 for high acuity patients)
  + sla_weight (10-20 if near SLA breach)
  + complexity_weight (-5 to +5)

Clamped to [0, 100]
```

**To adjust scoring**: Update rows in `priority_weights` table.

### Rejection Handling

Tasks can be rejected by the QA agent for:

- Missing critical fields
- Invalid entity references (participant/patient not in DB)
- Policy violations
- Insufficient data quality

Rejections include:
- `rejection_reason`: Human-readable explanation
- `rejection_category`: `missing_data`, `invalid_data`, `policy_violation`, `insufficient_quality`

## 🔧 API Endpoints

### `POST /process_transcript`

Process a transcript through the complete pipeline.

**Request:**
```json
{
  "transcript": "Dr. Chen here. Review Maria Garcia's meds (MRN005678) ASAP.",
  "transcript_id": 123  // optional
}
```

**Success Response (200):**
```json
{
  "status": "completed",
  "task_id": 456,
  "task": {
    "description": "Review medications for Maria Garcia",
    "participant_id": 1,
    "patient_id": 2,
    "category_id": 1,
    "priority_score": 75.5,
    "priority_level": "high",
    ...
  }
}
```

**Rejection Response (422):**
```json
{
  "status": "rejected",
  "rejection_reason": "Invalid patient reference",
  "rejection_category": "invalid_data"
}
```

### `GET /health`

Health check with database connectivity test.

### `GET /stats`

System statistics (task counts by status/priority).

### `GET /docs`

Interactive Swagger documentation.

## 📊 Database Schema

### Key Tables

- **participants**: Healthcare workers (doctors, nurses, etc.)
- **patients**: Patients with MRN, acuity flags
- **task_categories**: Task types (Medication Review, Lab Follow-up, etc.)
- **task_policies**: JSON policy configurations
- **category_sla**: SLA hours per category
- **priority_weights**: Weights for priority scoring
- **transcripts**: Source transcripts
- **tasks**: Final extracted tasks with full lineage

### Task Lineage Tracking

Every task stores complete processing history:

```json
{
  "lineage_metadata": {
    "processing_chain": [
      {
        "agent_name": "extraction",
        "agent_version": "1.0.0",
        "policy_version": "v1.0.0",
        "timestamp": "2025-02-06T10:30:00Z"
      },
      ...
    ]
  }
}
```

## 🎯 Design Principles

1. **Strict Grounding**: No hallucinated entities, all data from DB
2. **Null-on-Ambiguity**: If unclear, set to null (don't guess)
3. **Policy-Driven**: Business rules in DB, not code
4. **Deterministic**: Same input → same output
5. **Transparent**: Full lineage and provenance tracking
6. **Fail-Safe**: Clear rejections with actionable reasons

## 🔄 Updating Policies

Policies are version-controlled in the database:

```sql
-- Add new policy version
INSERT INTO task_policies (policy_version, policy_data, active) 
VALUES ('v1.1.0', '{...}', true);

-- Deactivate old version
UPDATE task_policies SET active = false WHERE policy_version = 'v1.0.0';
```

All new tasks will use the latest active policy.

## 🔍 Monitoring & Debugging

### View Task Processing History

```sql
SELECT 
  task_id,
  description,
  lineage_metadata->'processing_chain' as agents,
  qa_metadata->'checks_performed' as qa_checks
FROM tasks;
```

### Check Rejection Patterns

```sql
-- Note: Rejections aren't saved to tasks table
-- Check API logs or add rejection_log table if needed
```

### Priority Score Breakdown

```sql
SELECT 
  task_id,
  priority_level,
  priority_score,
  score_breakdown
FROM tasks
ORDER BY priority_score DESC;
```

## 🧪 Testing

### Test Pipeline Directly

```bash
cd orchestration
python pipeline.py
```

### Test API

```bash
# Health check
curl http://localhost:8000/health

# Process transcript
curl -X POST http://localhost:8000/process_transcript \
  -H "Content-Type: application/json" \
  -d @test_transcript.json

# View stats
curl http://localhost:8000/stats
```

## 📝 Notes

- **Agent Prompts**: Heavily documented prompts in `/agent_prompts/` - read these to understand agent behavior
- **Schemas**: Strict JSON schemas in `/schemas/` enforce data structure
- **No Hallucination**: Agents must ground to DB or return null
- **Policy Updates**: Update DB, not code - agents read policy at runtime
- **Lineage**: Full audit trail of how each task was created

## 🐛 Troubleshooting

### "Access denied" or AWS credential errors

- Run `python test_aws_bedrock.py` to diagnose AWS setup
- Check AWS credentials in `.env` are correct
- Verify Claude Sonnet 4.5 model access is enabled in Bedrock console
- See `AWS_SETUP.md` for detailed configuration guide

### "Agent returned invalid JSON"

Check agent prompt templates - ensure they explicitly say "ONLY JSON, NO markdown"

### "Database connection failed"

Verify `.env` settings and ensure PostgreSQL is running

### "Task always rejected"

Check QA rules in active policy - may be too strict for test data

### "Priority scores all the same"

Verify `priority_weights` table has data (run `seed.sql`)

## 📚 Further Reading

- LangGraph docs: https://langchain-ai.github.io/langgraph/
- FastAPI docs: https://fastapi.tiangolo.com/
- Claude API: https://docs.anthropic.com/

## 📄 License

MIT License - feel free to use and modify.
