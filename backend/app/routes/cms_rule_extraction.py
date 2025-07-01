# File: backend/app/services/cms_rule_extraction.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# FIXED: Import the class and create instance locally instead of importing non-existent global instance
from backend.app.services.cms_rule_extraction_FEstate import get_cms_rule_extraction_state, WorkflowStatus
from backend.app.services.cms_rule_extraction_FEorchestrator import CMSRuleExtractionOrchestrator

logger = logging.getLogger(__name__)

# Create orchestrator instance locally
orchestrator = CMSRuleExtractionOrchestrator()

# Use the frontend's expected prefix
router = APIRouter(prefix="/api/rules", tags=["Rule Management API"])

# Request/Response Models - Updated to match frontend expectations
class TriggerRunRequest(BaseModel):
    planId: str = Field(..., description="CMS program identifier")

class CommitRequest(BaseModel):
    planId: str = Field(..., description="CMS program identifier")

class TriggerStatus(BaseModel):
    eligible: bool
    reason: Optional[str] = None
    lastRunDate: Optional[datetime] = None
    cmsLastModified: Optional[datetime] = None
    pendingRun: Optional[Dict[str, Any]] = None

class RuleModel(BaseModel):
    id: str
    description: str
    engine: str
    confidence: int  # 0-100
    status: str
    cms_code: Optional[str] = None
    tags: Optional[List[str]] = None
    source_document: Optional[str] = None
    extracted_text: Optional[str] = None
    rule_logic: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RuleRunGroup(BaseModel):
    engineName: str
    engineType: str
    rules: List[RuleModel]
    processingTime: Optional[int] = None
    modelVersion: Optional[str] = None

class CommitResponse(BaseModel):
    success: bool
    runId: str
    committedAt: datetime
    approvedCount: int
    rejectedCount: int
    generatedFiles: Optional[Dict[str, str]] = None
    message: Optional[str] = None

class RuleRunHistory(BaseModel):
    runId: str
    planId: str
    started: datetime
    completed: Optional[datetime] = None
    status: str
    rulesCount: int
    approvedCount: Optional[int] = None
    rejectedCount: Optional[int] = None

# FRONTEND-COMPATIBLE ENDPOINTS

@router.get("/trigger-eligible")
async def check_trigger_eligibility() -> TriggerStatus:
    """
    Check if a new rule run can be triggered
    Frontend expects: GET /api/rules/trigger-eligible
    """
    try:
        # Check for any active runs
        state_service = get_cms_rule_extraction_state()
        active_runs = state_service.active_runs
        
        # If there are active runs in progress, not eligible
        for run_id, run_state in active_runs.items():  # FIXED: Use run_state instead of state
            if run_state["status"] in ["started", "extracting", "generating", "publishing"]:
                return TriggerStatus(
                    eligible=False,
                    reason="Another rule extraction is currently in progress",
                    pendingRun={
                        "runId": run_id,
                        "status": run_state["status"],
                        "startedAt": run_state["created_at"]
                    }
                )
        
        return TriggerStatus(
            eligible=True,
            reason=None,
            lastRunDate=datetime.now(),
            cmsLastModified=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to check trigger eligibility: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Eligibility check failed: {str(e)}")

@router.post("/run")
async def trigger_rule_run(request: TriggerRunRequest) -> Dict[str, str]:
    """
    Start rule extraction workflow (ASYNC)
    Frontend expects: POST /api/rules/run with { planId }
    """
    try:
        logger.info(f"Starting ASYNC rule extraction for plan: {request.planId}")
        
        # Validate planId (map frontend planId to backend program)
        plan_to_program_map: Dict[str, str] = {
            'edps-institutional': 'edps-institutional',
            'edps-professional': 'edps-professional', 
            'medicare-advantage': 'medicare-advantage',
            'medicaid-managed': 'medicaid-managed'
        }
        
        program = plan_to_program_map.get(request.planId)
        if not program:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid planId. Must be one of: {list(plan_to_program_map.keys())}"
            )
        
        # Create workflow run
        state_service = get_cms_rule_extraction_state()
        run_id = state_service.create_run(program)
        
        # Start extraction pipeline DIRECTLY (no background tasks)
        import asyncio
        asyncio.create_task(orchestrator.start_rule_extraction(run_id, program))
        
        return {
            "runId": run_id,
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger rule run: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rule run trigger failed: {str(e)}")

@router.get("/progress-stream/{run_id}")
async def stream_progress(run_id: str):
    """
    SSE endpoint for real-time progress updates
    Frontend expects: EventSource connection to this endpoint
    """
    try:
        state_service = get_cms_rule_extraction_state()
        if run_id not in state_service.active_runs:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        return StreamingResponse(
            state_service.stream_progress(run_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stream progress for {run_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Progress streaming failed: {str(e)}")

@router.get("/review")
async def get_pending_rules(plan: str) -> List[RuleRunGroup]:
    """
    Get extracted rules ready for review
    Frontend expects: GET /api/rules/review?plan={planId}
    """
    try:
        # Get active runs from state
        state_service = get_cms_rule_extraction_state()
        active_runs = state_service.active_runs
        
        # Find most recent run for this plan
        target_run: Optional[Dict[str, Any]] = None
        for _, run_state in active_runs.items():  # FIXED: Use _ since run_id is not needed
            if run_state.get("program") == plan and run_state["status"] in ["reviewing", "completed"]:
                target_run = run_state
                break
        
        if not target_run:
            # Return mock data for testing
            return [
                RuleRunGroup(
                    engineName="DeepSeek",
                    engineType="primary",
                    rules=[
                        RuleModel(
                            id="TRC004",
                            description="Validate patient admission date must be within reporting period",
                            engine="DeepSeek",
                            confidence=95,
                            status="pending",
                            tags=["high-risk"]
                        )
                    ],
                    processingTime=2500,
                    modelVersion="v2.1.0"
                ),
                RuleRunGroup(
                    engineName="Mistral",
                    engineType="fallback", 
                    rules=[
                        RuleModel(
                            id="TRC005",
                            description="Check discharge status code against CMS allowed values",
                            engine="Mistral",
                            confidence=78,
                            status="pending",
                            tags=["manual_stub"]
                        )
                    ],
                    processingTime=1800,
                    modelVersion="v1.3.2"
                )
            ]
        
        # Convert backend rules to frontend format grouped by engine
        extracted_rules: List[Dict[str, Any]] = target_run["extracted_rules"]
        groups_by_engine: Dict[str, List[RuleModel]] = {}
        
        for rule in extracted_rules:
            engine = rule.get("engine", "Unknown")
            if engine not in groups_by_engine:
                groups_by_engine[engine] = []
            
            groups_by_engine[engine].append(RuleModel(
                id=rule["id"],
                description=rule["description"],
                engine=rule["engine"],
                confidence=rule["confidence"],
                status=rule["status"],
                tags=rule.get("tags", [])
            ))
        
        # Convert to RuleRunGroup format
        rule_groups: List[RuleRunGroup] = []
        for engine, rules in groups_by_engine.items():
            engine_type = "primary" if engine == "DeepSeek" else "fallback"
            rule_groups.append(RuleRunGroup(
                engineName=engine,
                engineType=engine_type,
                rules=rules,
                processingTime=2000,  # Could calculate from timestamps
                modelVersion="v1.0.0"
            ))
        
        return rule_groups
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pending rules for plan {plan}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rules retrieval failed: {str(e)}")

@router.post("/approve")
async def approve_rule(request: Dict[str, str]) -> RuleModel:
    """
    Approve a specific rule
    Frontend expects: POST /api/rules/approve with { ruleId }
    """
    try:
        rule_id = request.get("ruleId")
        if not rule_id:
            raise HTTPException(status_code=400, detail="ruleId is required")
        
        # For now, return a mock approved rule
        # In production, you'd update the rule status in your state/database
        return RuleModel(
            id=rule_id,
            description="Rule approved successfully",
            engine="DeepSeek",
            confidence=95,
            status="approved",
            tags=["approved"]
        )
        
    except Exception as e:
        logger.error(f"Failed to approve rule {request.get('ruleId')}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rule approval failed: {str(e)}")

@router.post("/reject") 
async def reject_rule(request: Dict[str, str]) -> RuleModel:
    """
    Reject a specific rule
    Frontend expects: POST /api/rules/reject with { ruleId }
    """
    try:
        rule_id = request.get("ruleId")
        if not rule_id:
            raise HTTPException(status_code=400, detail="ruleId is required")
        
        # For now, return a mock rejected rule
        # In production, you'd update the rule status in your state/database
        return RuleModel(
            id=rule_id,
            description="Rule rejected successfully",
            engine="DeepSeek", 
            confidence=95,
            status="rejected",
            tags=["rejected"]
        )
        
    except Exception as e:
        logger.error(f"Failed to reject rule {request.get('ruleId')}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rule rejection failed: {str(e)}")

@router.post("/commit")
async def commit_rules(request: CommitRequest) -> CommitResponse:
    """
    Commit approved rules through the complete pipeline (ASYNC)
    Frontend expects: POST /api/rules/commit with { planId }
    """
    try:
        logger.info(f"Committing rules for plan: {request.planId}")
        
        # Get current rule decisions from sessionStorage simulation
        # In production, you'd get this from the frontend request or state
        mock_decisions: Dict[str, Dict[str, Any]] = {
            "TRC004": {"status": "approved", "tags": ["high-risk"]},
            "TRC005": {"status": "approved", "tags": ["manual_stub"]},
            "TRC006": {"status": "rejected", "tags": []}
        }
        
        # Find active run for this plan
        state_service = get_cms_rule_extraction_state()
        active_runs = state_service.active_runs
        run_id: Optional[str] = None
        
        for rid, run_state in active_runs.items():
            if run_state.get("program") == request.planId:
                run_id = rid
                break
        
        if not run_id:
            # Create a mock run for testing
            run_id = state_service.create_run(request.planId)
            state_service.update_step(run_id, 2, "Rules ready for review", WorkflowStatus.REVIEWING)
        
        # Execute pipeline steps 3-6 using our ASYNC orchestrator
        generated_artifacts: Dict[str, str] = await orchestrator.commit_rule_decisions(
            run_id, 
            mock_decisions
        )
        
        # Count approved/rejected
        approved_count = len([d for d in mock_decisions.values() if d["status"] == "approved"])
        rejected_count = len([d for d in mock_decisions.values() if d["status"] == "rejected"])
        
        return CommitResponse(
            success=True,
            runId=run_id,
            committedAt=datetime.now(),
            approvedCount=approved_count,
            rejectedCount=rejected_count,
            generatedFiles={
                "cms_rules_yml": generated_artifacts.get("cms_rules.yml", ""),
                "trc_rules_json": generated_artifacts.get("trc_rules.json", ""),
                "program_rules_json": generated_artifacts.get("rule_catalog.json", "")
            },
            message="Rules committed and files generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to commit rules for plan {request.planId}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rule commit failed: {str(e)}")

@router.get("/history")
async def get_rule_history(plan: str) -> List[RuleRunHistory]:
    """
    Get historical rule runs for a plan
    Frontend expects: GET /api/rules/history?plan={planId}
    """
    try:
        # Get history from our state tracker
        state_service = get_cms_rule_extraction_state()
        runs = state_service.get_history(plan)
        
        # Convert to frontend format
        history: List[RuleRunHistory] = []
        for run in runs:
            history.append(RuleRunHistory(
                runId=run["run_id"],
                planId=run["program"],
                started=datetime.fromisoformat(run["created_at"]),
                completed=datetime.now() if run["status"] == "completed" else None,
                status=run["status"],
                rulesCount=len(run.get("extracted_rules", [])),
                approvedCount=0,  # Could calculate from decisions
                rejectedCount=0
            ))
        
        return history
        
    except Exception as e:
        logger.error(f"Failed to get rule history for plan {plan}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

# Health Check
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for rule management service"""
    try:
        return {
            "status": "healthy",
            "service": "rule-management", 
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")