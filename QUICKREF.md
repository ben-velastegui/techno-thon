# Quick Reference - Task Extraction System

## 🚀 Quick Start (5 minutes)

```bash
# 1. Setup
./setup.sh

# 2. Edit .env and add AWS credentials
nano .env  # Add: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

# 3. Activate environment
source venv/bin/activate

# 4. Test pipeline
python test_pipeline.py

# 5. Start API
cd api && uvicorn main:app --reload
```

## 📡 API Usage

### Process a transcript
```bash
curl -X POST http://localhost:8000/process_transcript \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Dr. Chen needs to review medications for Maria Garcia (MRN005678) ASAP"
  }'
```

### Health check
```bash
curl http://localhost:8000/health
```

### System stats
```bash
curl http://localhost:8000/stats
```

## 🗄️ Database Queries

### View all tasks
```sql
SELECT task_id, description, priority_level, priority_score 
FROM tasks 
ORDER BY priority_score DESC;
```

### View task lineage
```sql
SELECT task_id, lineage_metadata 
FROM tasks 
WHERE task_id = 1;
```

### Update policy
```sql
INSERT INTO task_policies (policy_version, policy_data, active) 
VALUES ('v1.1.0', '{"version":"v1.1.0",...}', true);
```

### Adjust priority weights
```sql
UPDATE priority_weights 
SET weight_value = 30.0 
WHERE weight_name = 'urgent_keyword';
```

## 🔧 Common Operations

### Add a new participant
```sql
INSERT INTO participants (name, role, department, email) 
VALUES ('Dr. Jane Doe', 'Physician', 'Oncology', 'jane.doe@hospital.org');
```

### Add a new patient
```sql
INSERT INTO patients (name, mrn, high_acuity) 
VALUES ('John Smith', 'MRN012345', false);
```

### Add a new category
```sql
INSERT INTO task_categories (category_name, description, requires_patient) 
VALUES ('Imaging Review', 'Review imaging results', true);

INSERT INTO category_sla (category_id, sla_hours) 
VALUES ((SELECT category_id FROM task_categories WHERE category_name = 'Imaging Review'), 36);
```

## 📊 Pipeline Flow

```
1. EXTRACTION
   - Input: Raw transcript
   - Output: Extracted task with source spans
   - Grounding: participants, patients, categories from DB
   
2. NORMALIZATION
   - Input: Extracted task
   - Output: Enriched task with SLA, computed fields
   - Grounding: SLA table, category requirements
   
3. QA
   - Input: Normalized task
   - Output: Accept/Reject decision
   - Grounding: Policy rules from task_policies table
   
4. PRIORITIZATION
   - Input: Validated task
   - Output: Task with priority score (0-100)
   - Grounding: priority_weights table
   
5. SAVE
   - Input: Prioritized task
   - Output: Task ID
   - Action: INSERT into tasks table
```

## 🎯 Key Concepts

### Database Grounding
- Agents can ONLY reference entities in the database
- If entity not found → set field to null
- No hallucination allowed

### Null-on-Ambiguity
- Unclear participant? → participant_id = null
- Unclear patient? → patient_id = null
- Unclear category? → category_id = null

### Policy-Driven Validation
- All validation rules stored in task_policies table
- Update policy without changing code
- Policy versioning for audit trail

### Deterministic Scoring
- Priority calculation is pure math
- No AI judgment in scoring
- Same input = same priority score

## 🐛 Troubleshooting

### API returns 500 error
- Check database connection in .env
- Ensure PostgreSQL is running
- Check API logs

### Tasks always rejected
- Check active policy requirements
- View QA metadata in response
- May need to adjust policy rules

### Priority scores seem wrong
- Check priority_weights table values
- Review score_breakdown in task output
- Adjust weights as needed

### Agent prompts not loading
- Ensure agent_prompts/ directory exists
- Check file permissions
- Verify paths in pipeline.py

## 📚 File Locations

- Agent prompts: `/agent_prompts/*.txt`
- Schemas: `/schemas/*.json`
- Pipeline: `/orchestration/pipeline.py`
- API: `/api/main.py`
- Database: `database.sql` + `seed.sql`

## 🔐 Environment Variables

Required:
- `AWS_ACCESS_KEY_ID` - Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret access key
- `AWS_REGION` - AWS region (default: us-east-1)

Database:
- `DB_HOST` - Default: localhost
- `DB_PORT` - Default: 5432
- `DB_NAME` - Default: task_extraction
- `DB_USER` - Default: postgres
- `DB_PASSWORD` - Default: postgres

## 💡 Tips

1. **Test First**: Run `python test_pipeline.py` before production use
2. **Read Prompts**: Agent behavior is in `/agent_prompts/*.txt`
3. **Watch Logs**: API logs show each pipeline step
4. **Update Policy**: Change DB, not code
5. **Track Lineage**: Every task has complete audit trail
