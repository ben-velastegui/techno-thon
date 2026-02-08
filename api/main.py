"""
FastAPI Application for Task Extraction System
Exposes REST API for transcript processing
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.pipeline import run_pipeline

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TranscriptRequest(BaseModel):
    """Request model for transcript processing"""
    transcript: str = Field(
        ..., 
        min_length=10,
        description="The transcript text to process",
        example="Dr. Chen here. I need to review Maria Garcia's medications ASAP."
    )
    transcript_id: Optional[int] = Field(
        None,
        description="Optional transcript ID if already saved in database"
    )


class TaskResponse(BaseModel):
    """Response model for successful task creation"""
    status: str = Field(..., example="completed")
    task_id: int = Field(..., description="Database ID of created task")
    task: Dict[str, Any] = Field(..., description="Complete task object")


class RejectionResponse(BaseModel):
    """Response model for rejected tasks"""
    status: str = Field(..., example="rejected")
    rejection_reason: str = Field(
        ..., 
        description="Human-readable reason for rejection",
        example="Missing task description"
    )
    rejection_category: str = Field(
        ...,
        description="Category of rejection",
        example="missing_data"
    )


class ErrorResponse(BaseModel):
    """Response model for errors"""
    detail: str
    error_type: str


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Task Extraction API",
    description="Extract, validate, and prioritize tasks from healthcare transcripts using LangGraph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Task Extraction API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check with database connectivity"""
    try:
        from orchestration.pipeline import get_db_connection
        
        # Test DB connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "pipeline": "ready"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@app.post(
    "/process_transcript",
    response_model=None,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Task successfully created",
            "model": TaskResponse
        },
        422: {
            "description": "Task rejected due to validation failure",
            "model": RejectionResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def process_transcript(request: TranscriptRequest):
    """
    Process a transcript through the complete extraction pipeline.
    
    **Pipeline Steps:**
    1. Extraction - Extract task from transcript with DB grounding
    2. Normalization - Enrich and normalize extracted data
    3. QA - Validate against policy and quality criteria
    4. Prioritization - Calculate priority score
    5. Save - Persist to database
    
    **Returns:**
    - Success: Task object with ID and complete metadata
    - Rejection: Clear reason why task could not be created
    - Error: System error details
    """
    try:
        # Run pipeline
        result = run_pipeline(
            transcript=request.transcript,
            transcript_id=request.transcript_id
        )
        
        # Handle rejection (return 422 for validation failure)
        if result['status'] == 'rejected':
            return HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "rejected",
                    "rejection_reason": result['rejection_reason'],
                    "rejection_category": result['rejection_category']
                }
            )
        
        # Return success
        return {
            "status": "completed",
            "task_id": result['task_id'],
            "task": result['task']
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": f"Failed to parse agent output: {str(e)}",
                "error_type": "json_parse_error"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": f"Pipeline execution failed: {str(e)}",
                "error_type": "pipeline_error"
            }
        )


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        from orchestration.pipeline import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get task counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM tasks
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())
        
        # Get priority distribution
        cursor.execute("""
            SELECT priority_level, COUNT(*) as count
            FROM tasks
            GROUP BY priority_level
        """)
        priority_counts = dict(cursor.fetchall())
        
        # Get total tasks
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "total_tasks": total_tasks,
            "by_status": status_counts,
            "by_priority": priority_counts
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("🚀 Task Extraction API starting...")
    print("📋 Endpoints available:")
    print("   - POST /process_transcript")
    print("   - GET  /health")
    print("   - GET  /stats")
    print("   - GET  /docs (Swagger UI)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Task Extraction API shutting down...")


# ============================================================================
# MAIN (for uvicorn)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
