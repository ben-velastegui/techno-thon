"""
LangGraph Task Extraction Pipeline
Implements: Extraction -> Normalization -> QA -> Prioritization -> Save
"""

import os
import json
from datetime import datetime, timedelta
from typing import TypedDict, Optional, Dict, Any, List, Literal
from typing_extensions import Annotated

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_aws import ChatBedrock

# Database imports (using psycopg2 for simplicity)
import psycopg2
from psycopg2.extras import RealDictCursor, Json


# ============================================================================
# STATE DEFINITION
# ============================================================================

class PipelineState(TypedDict):
    """Strongly typed state for the entire pipeline"""
    # Input
    transcript: str
    transcript_id: Optional[int]
    
    # Database context (injected at start)
    db_context: Dict[str, Any]
    policy_snapshot: Dict[str, Any]
    priority_weights: List[Dict[str, Any]]
    
    # Agent outputs
    extracted_task: Optional[Dict[str, Any]]
    normalized_task: Optional[Dict[str, Any]]
    qa_result: Optional[Dict[str, Any]]
    final_task: Optional[Dict[str, Any]]
    
    # Control flow
    rejection_reason: Optional[str]
    rejection_category: Optional[str]
    
    # Lineage
    lineage_metadata: Dict[str, Any]
    
    # Final result
    saved_task_id: Optional[int]
    status: Literal["pending", "rejected", "completed"]


# ============================================================================
# DATABASE TOOLS
# ============================================================================

def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "task_extraction"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )


def fetch_db_context() -> Dict[str, Any]:
    """Fetch all necessary database context for grounding"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Fetch participants
    cursor.execute("SELECT participant_id, name, role, department FROM participants WHERE active = true")
    participants = cursor.fetchall()
    
    # Fetch patients
    cursor.execute("SELECT patient_id, name, mrn, high_acuity, critical_status FROM patients WHERE active = true")
    patients = cursor.fetchall()
    
    # Fetch categories
    cursor.execute("SELECT category_id, category_name, description, requires_patient, requires_participant FROM task_categories WHERE active = true")
    categories = cursor.fetchall()
    
    # Fetch SLAs
    cursor.execute("""
        SELECT tc.category_name, cs.sla_hours, cs.escalation_hours 
        FROM category_sla cs 
        JOIN task_categories tc ON cs.category_id = tc.category_id
    """)
    slas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        "participants": [dict(p) for p in participants],
        "patients": [dict(p) for p in patients],
        "categories": [dict(c) for c in categories],
        "slas": [dict(s) for s in slas]
    }


def fetch_active_policy() -> Dict[str, Any]:
    """Fetch the active policy configuration"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT policy_version, policy_data FROM task_policies WHERE active = true ORDER BY effective_date DESC LIMIT 1")
    policy = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if policy:
        return {
            "policy_version": policy['policy_version'],
            **policy['policy_data']
        }
    return {"policy_version": "none", "rules": {}}


def fetch_priority_weights() -> List[Dict[str, Any]]:
    """Fetch priority weights for scoring"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT weight_name, weight_category, weight_value, description FROM priority_weights WHERE active = true")
    weights = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return [dict(w) for w in weights]


def save_task_to_db(task: Dict[str, Any], transcript_id: Optional[int] = None) -> int:
    """Save final task to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tasks (
            transcript_id, participant_id, patient_id, category_id,
            description, due_date, expected_completion_date,
            priority_score, priority_level,
            source_spans, enriched_fields, score_breakdown,
            lineage_metadata, qa_metadata, prioritization_metadata,
            status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING task_id
    """, (
        transcript_id,
        task.get('participant_id'),
        task.get('patient_id'),
        task.get('category_id'),
        task['description'],
        task.get('due_date'),
        task.get('enriched_fields', {}).get('expected_completion_date'),
        task['priority_score'],
        task['priority_level'],
        Json(task.get('source_spans', {})),
        Json(task.get('enriched_fields', {})),
        Json(task.get('score_breakdown', {})),
        Json(task['lineage_metadata']),
        Json(task['qa_metadata']),
        Json(task['prioritization_metadata']),
        'pending'
    ))
    
    task_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    
    return task_id


# ============================================================================
# AGENT NODES
# ============================================================================

# Initialize LLM (using Claude Sonnet 4.5 via AWS Bedrock)
llm = ChatBedrock(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",  # Claude Sonnet 4.5 on Bedrock
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    model_kwargs={
        "temperature": 0,  # Deterministic
        "max_tokens": 4000
    }
)


def load_prompt(prompt_name: str, **kwargs) -> str:
    """Load and format agent prompt"""
    prompt_path = f"/mnt/user-data/uploads/agent_prompts/{prompt_name}.txt"
    if not os.path.exists(prompt_path):
        # Fallback to local path if not in uploads
        prompt_path = f"agent_prompts/{prompt_name}.txt"
    
    with open(prompt_path, 'r') as f:
        template = f.read()
    
    return template.format(**kwargs)


def extraction_node(state: PipelineState) -> PipelineState:
    """Extract task from transcript with strict database grounding"""
    print("🔍 Running extraction agent...")
    
    # Build prompt
    prompt = load_prompt(
        "extraction",
        db_context=json.dumps(state['db_context'], indent=2),
        policy=json.dumps(state['policy_snapshot'], indent=2),
        transcript=state['transcript']
    )
    
    # Call LLM
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Parse JSON response
    extracted = json.loads(response.content)
    
    # Add extraction metadata
    if 'lineage_metadata' not in extracted:
        extracted['lineage_metadata'] = {'processing_chain': []}
    
    extracted['lineage_metadata']['processing_chain'].append({
        'agent_name': 'extraction',
        'agent_version': '1.0.0',
        'policy_version': state['policy_snapshot']['policy_version'],
        'timestamp': datetime.utcnow().isoformat()
    })
    
    state['extracted_task'] = extracted
    return state


def normalization_node(state: PipelineState) -> PipelineState:
    """Normalize and enrich extracted task"""
    print("🔧 Running normalization agent...")
    
    # Build prompt
    prompt = load_prompt(
        "normalization",
        db_context=json.dumps(state['db_context'], indent=2),
        policy=json.dumps(state['policy_snapshot'], indent=2),
        extraction_output=json.dumps(state['extracted_task'], indent=2)
    )
    
    # Call LLM
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Parse JSON response
    normalized = json.loads(response.content)
    
    # Add normalization metadata
    normalized['lineage_metadata']['processing_chain'].append({
        'agent_name': 'normalization',
        'agent_version': '1.0.0',
        'policy_version': state['policy_snapshot']['policy_version'],
        'timestamp': datetime.utcnow().isoformat()
    })
    
    state['normalized_task'] = normalized
    return state


def qa_node(state: PipelineState) -> PipelineState:
    """Validate task and decide accept/reject"""
    print("✅ Running QA agent...")
    
    # Build prompt
    prompt = load_prompt(
        "qa",
        db_context=json.dumps(state['db_context'], indent=2),
        policy=json.dumps(state['policy_snapshot'], indent=2),
        normalized_task=json.dumps(state['normalized_task'], indent=2)
    )
    
    # Call LLM
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Parse JSON response
    qa_result = json.loads(response.content)
    
    state['qa_result'] = qa_result
    
    # Handle rejection
    if qa_result.get('qa_decision') == 'rejected':
        state['rejection_reason'] = qa_result.get('rejection_reason')
        state['rejection_category'] = qa_result.get('rejection_category')
        state['status'] = 'rejected'
    else:
        # Task accepted, pass validated task forward
        state['final_task'] = qa_result.get('validated_task', state['normalized_task'])
        state['final_task']['qa_metadata'] = qa_result.get('qa_metadata', {})
    
    return state


def prioritization_node(state: PipelineState) -> PipelineState:
    """Calculate priority score for validated task"""
    print("📊 Running prioritization agent...")
    
    # Build prompt
    prompt = load_prompt(
        "prioritization",
        db_context=json.dumps(state['db_context'], indent=2),
        policy=json.dumps(state['policy_snapshot'], indent=2),
        priority_weights=json.dumps(state['priority_weights'], indent=2),
        validated_task=json.dumps(state['final_task'], indent=2)
    )
    
    # Call LLM
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Parse JSON response
    prioritized = json.loads(response.content)
    
    state['final_task'] = prioritized
    state['status'] = 'completed'
    
    return state


def save_node(state: PipelineState) -> PipelineState:
    """Save final task to database"""
    print("💾 Saving task to database...")
    
    task_id = save_task_to_db(state['final_task'], state.get('transcript_id'))
    state['saved_task_id'] = task_id
    
    print(f"✅ Task saved with ID: {task_id}")
    return state


def rejection_node(state: PipelineState) -> PipelineState:
    """Handle rejected tasks (no-op, just log)"""
    print(f"❌ Task rejected: {state['rejection_reason']}")
    return state


# ============================================================================
# CONDITIONAL ROUTING
# ============================================================================

def qa_router(state: PipelineState) -> Literal["prioritization", "rejection"]:
    """Route based on QA decision"""
    if state.get('status') == 'rejected':
        return "rejection"
    return "prioritization"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_pipeline_graph() -> StateGraph:
    """Build the LangGraph state machine"""
    
    # Initialize graph
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("normalization", normalization_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("prioritization", prioritization_node)
    workflow.add_node("save", save_node)
    workflow.add_node("rejection", rejection_node)
    
    # Define edges
    workflow.set_entry_point("extraction")
    workflow.add_edge("extraction", "normalization")
    workflow.add_edge("normalization", "qa")
    
    # Conditional routing after QA
    workflow.add_conditional_edges(
        "qa",
        qa_router,
        {
            "prioritization": "prioritization",
            "rejection": "rejection"
        }
    )
    
    workflow.add_edge("prioritization", "save")
    workflow.add_edge("save", END)
    workflow.add_edge("rejection", END)
    
    return workflow.compile()


# ============================================================================
# PIPELINE EXECUTION
# ============================================================================

def run_pipeline(transcript: str, transcript_id: Optional[int] = None) -> Dict[str, Any]:
    """Execute the complete pipeline for a transcript"""
    
    # Initialize state
    initial_state: PipelineState = {
        'transcript': transcript,
        'transcript_id': transcript_id,
        'db_context': fetch_db_context(),
        'policy_snapshot': fetch_active_policy(),
        'priority_weights': fetch_priority_weights(),
        'extracted_task': None,
        'normalized_task': None,
        'qa_result': None,
        'final_task': None,
        'rejection_reason': None,
        'rejection_category': None,
        'lineage_metadata': {},
        'saved_task_id': None,
        'status': 'pending'
    }
    
    # Build and run graph
    graph = build_pipeline_graph()
    final_state = graph.invoke(initial_state)
    
    # Return result
    if final_state['status'] == 'rejected':
        return {
            'status': 'rejected',
            'rejection_reason': final_state['rejection_reason'],
            'rejection_category': final_state['rejection_category']
        }
    else:
        return {
            'status': 'completed',
            'task_id': final_state['saved_task_id'],
            'task': final_state['final_task']
        }


# ============================================================================
# TESTING / CLI
# ============================================================================

if __name__ == "__main__":
    # Test with sample transcript
    test_transcript = "Dr. Chen here. I need to review Maria Garcia's medications ASAP. Her MRN is MRN005678. She mentioned some side effects during her last visit. This is urgent and should be done by tomorrow."
    
    print("=" * 80)
    print("TASK EXTRACTION PIPELINE - TEST RUN")
    print("=" * 80)
    
    result = run_pipeline(test_transcript)
    
    print("\n" + "=" * 80)
    print("FINAL RESULT:")
    print("=" * 80)
    print(json.dumps(result, indent=2))
