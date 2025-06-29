import json
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    STARTED = "started"
    EXTRACTING = "extracting"
    REVIEWING = "reviewing" 
    GENERATING = "generating"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"

class CMSRuleExtractionState:
    def __init__(self) -> None:
        # FIXED: Use dynamic path resolution instead of relative path
        self.base_dir = Path(__file__).resolve().parents[3]  # Project root
        self.storage_dir = self.base_dir / "data" / "workflow_runs"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.active_runs: Dict[str, Dict[str, Any]] = {}
        self.progress_streams: Dict[str, List[asyncio.Queue[Dict[str, Any]]]] = {}  # SSE streams
        self.cleanup_interval: int = 3600  # 1 hour cleanup
        self.cleanup_task: Optional[asyncio.Task[None]] = None  # Track cleanup task
        
        # FIXED: Don't start async task in __init__
        # Will be started lazily when needed
    
    def _ensure_cleanup_task(self) -> None:
        """Start cleanup task if not already running"""
        if self.cleanup_task is None or self.cleanup_task.done():
            try:
                self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
                logger.info("Started periodic cleanup task")
            except RuntimeError as e:
                logger.warning(f"Could not start cleanup task (no event loop): {e}")
    
    def create_run(self, program: str) -> str:
        run_id = f"rr-{datetime.now().strftime('%Y%m%d')}-{self._get_next_seq():03d}"
        
        run_state: Dict[str, Any] = {
            "run_id": run_id,
            "program": program,
            "status": WorkflowStatus.STARTED.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_step": 1,
            "step_name": "Initializing",
            "extracted_rules": [],
            "progress": 0.0,
            "ai_engine": None,
            "error": None
        }
        
        self.active_runs[run_id] = run_state
        self.progress_streams[run_id] = []
        self._save_state(run_id)
        self._broadcast_progress(run_id)
        
        # FIXED: Start cleanup task lazily when first run is created
        self._ensure_cleanup_task()
        
        return run_id
    
    def update_step(self, run_id: str, step: int, step_name: str, status: Optional[WorkflowStatus] = None, ai_engine: Optional[str] = None) -> None:
        if run_id not in self.active_runs:
            return
        
        self.active_runs[run_id].update({
            "current_step": step,
            "step_name": step_name,
            "progress": (step / 7) * 100,
            "updated_at": datetime.now().isoformat(),
            "ai_engine": ai_engine
        })
        
        if status:
            self.active_runs[run_id]["status"] = status.value
            
        self._save_state(run_id)
        self._broadcast_progress(run_id)
    
    def update_ai_progress(self, run_id: str, ai_engine: str, step_name: str) -> None:
        """Update progress with specific AI engine information"""
        if run_id not in self.active_runs:
            return
            
        # Map AI engines to steps
        step_mapping = {
            "deepseek": (2, "DeepSeek model running"),
            "local_llm": (3, "Mistral fallback"), 
            "flan_t5": (4, "FLAN-T5 processing"),
            "non_ai": (4, "Heuristic fallback"),
            "compilation": (6, "Rule compilation")
        }
        
        step, default_name = step_mapping.get(ai_engine.lower(), (5, step_name))
        
        self.active_runs[run_id].update({
            "current_step": step,
            "step_name": default_name,
            "progress": (step / 7) * 100,
            "updated_at": datetime.now().isoformat(),
            "ai_engine": ai_engine
        })
        
        self._save_state(run_id)
        self._broadcast_progress(run_id)
    
    def set_extracted_rules(self, run_id: str, rules: List[Dict[str, Any]]) -> None:
        if run_id in self.active_runs:
            self.active_runs[run_id]["extracted_rules"] = rules
            self.active_runs[run_id]["updated_at"] = datetime.now().isoformat()
            self._save_state(run_id)
            self._broadcast_progress(run_id)
    
    def set_error(self, run_id: str, error: str) -> None:
        """Set error state and broadcast"""
        if run_id in self.active_runs:
            self.active_runs[run_id].update({
                "status": WorkflowStatus.FAILED.value,
                "error": error,
                "updated_at": datetime.now().isoformat()
            })
            self._save_state(run_id)
            self._broadcast_progress(run_id)
    
    def get_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self.active_runs.get(run_id)
    
    def complete_run(self, run_id: str) -> None:
        if run_id in self.active_runs:
            self.active_runs[run_id]["status"] = WorkflowStatus.COMPLETED.value
            self.active_runs[run_id]["updated_at"] = datetime.now().isoformat()
            self._broadcast_progress(run_id)
            
            # Archive to history
            history_dir = self.storage_dir / "history"
            history_dir.mkdir(exist_ok=True)
            
            try:
                with open(history_dir / f"{run_id}.json", 'w', encoding='utf-8') as f:
                    json.dump(self.active_runs[run_id], f, indent=2)
                logger.info(f"Archived run {run_id} to history")
            except OSError as e:
                logger.error(f"Failed to archive run {run_id}: {e}")
            
            # Schedule cleanup after delay with fallback
            try:
                asyncio.create_task(self._cleanup_run_after_delay(run_id, 300))  # 5 minutes
            except RuntimeError:
                logger.warning(f"No event loop available for async cleanup of {run_id}, using timer fallback")
                # Fallback: use threading timer for cleanup
                timer = threading.Timer(300.0, self._sync_cleanup_run, args=[run_id])
                timer.start()
    
    def get_history(self, program: Optional[str] = None) -> List[Dict[str, Any]]:
        history_dir = self.storage_dir / "history"
        if not history_dir.exists():
            return []
        
        runs: List[Dict[str, Any]] = []
        for file in history_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data: Dict[str, Any] = json.load(f)
                    if not program or data.get("program") == program:
                        runs.append(data)
            except (json.JSONDecodeError, OSError) as e:
                # FIXED: Use logger instead of print, specific exception types
                logger.warning(f"Error reading history file {file}: {e}")
                continue
        
        return sorted(runs, key=lambda x: x["created_at"], reverse=True)
    
    def cancel_run(self, run_id: str) -> None:
        """Cancel an active workflow run"""
        if run_id in self.active_runs:
            self.active_runs[run_id].update({
                "status": WorkflowStatus.FAILED.value,
                "step_name": "Workflow cancelled by user",
                "error": "Cancelled by user",
                "updated_at": datetime.now().isoformat()
            })
            self._save_state(run_id)
            self._broadcast_progress(run_id)
    
    # SSE Support Methods
    def add_progress_stream(self, run_id: str) -> asyncio.Queue[Dict[str, Any]]:
        """Add a new SSE client for progress updates"""
        if run_id not in self.progress_streams:
            self.progress_streams[run_id] = []
        
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=100)  # Prevent memory leaks
        self.progress_streams[run_id].append(queue)
        
        # Send current state immediately
        if run_id in self.active_runs:
            try:
                queue.put_nowait(self._format_progress_event(run_id))
            except asyncio.QueueFull:
                logger.warning(f"Progress queue full for {run_id}")
        
        return queue
    
    def remove_progress_stream(self, run_id: str, queue: asyncio.Queue[Dict[str, Any]]) -> None:
        """Remove SSE client when connection closes"""
        if run_id in self.progress_streams:
            try:
                self.progress_streams[run_id].remove(queue)
                if not self.progress_streams[run_id]:
                    del self.progress_streams[run_id]
            except ValueError:
                logger.warning(f"Queue not found in progress streams for {run_id}")
    
    async def stream_progress(self, run_id: str) -> AsyncGenerator[str, None]:
        """SSE generator for progress updates"""
        queue = self.add_progress_stream(run_id)
        
        try:
            while True:
                try:
                    # Wait for progress update with timeout
                    progress_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    
                    # Stop streaming if run is completed or failed
                    if progress_data.get("status") in ["completed", "failed"]:
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for {run_id}")
        except Exception as e:
            logger.error(f"Error in SSE stream for {run_id}: {e}")
        finally:
            self.remove_progress_stream(run_id, queue)
    
    def _broadcast_progress(self, run_id: str) -> None:
        """Broadcast progress update to all SSE clients"""
        if run_id not in self.progress_streams:
            return
        
        progress_data = self._format_progress_event(run_id)
        
        # Send to all connected clients
        queues_to_remove: List[asyncio.Queue[Dict[str, Any]]] = []
        for progress_queue in self.progress_streams[run_id]:
            try:
                progress_queue.put_nowait(progress_data)
            except asyncio.QueueFull:
                # Mark slow/stuck clients for removal
                logger.warning(f"Removing slow client for {run_id}")
                queues_to_remove.append(progress_queue)
        
        # Remove slow clients
        for queue_to_remove in queues_to_remove:
            try:
                self.progress_streams[run_id].remove(queue_to_remove)
            except ValueError:
                pass
    
    def _format_progress_event(self, run_id: str) -> Dict[str, Any]:
        """Format progress data for SSE"""
        if run_id not in self.active_runs:
            return {}
        
        state = self.active_runs[run_id]
        return {
            "runId": run_id,
            "status": state["status"],
            "currentStep": state["current_step"],
            "totalSteps": 7,
            "stepName": state["step_name"],
            "progress": state["progress"],
            "aiEngine": state.get("ai_engine"),
            "timestamp": state["updated_at"],
            "error": state.get("error")
        }
    
    def _sync_cleanup_run(self, run_id: str) -> None:
        """Synchronous fallback cleanup for when no event loop is available"""
        try:
            if run_id in self.active_runs:
                if self.active_runs[run_id]["status"] in ["completed", "failed"]:
                    logger.info(f"Sync cleanup removing run: {run_id}")
                    del self.active_runs[run_id]
                    if run_id in self.progress_streams:
                        del self.progress_streams[run_id]
        except Exception as e:
            logger.error(f"Error in sync cleanup for {run_id}: {e}")
    
    async def _cleanup_run_after_delay(self, run_id: str, delay_seconds: int) -> None:
        """Clean up a specific run after delay"""
        try:
            await asyncio.sleep(delay_seconds)
            if run_id in self.active_runs:
                if self.active_runs[run_id]["status"] in ["completed", "failed"]:
                    logger.info(f"Cleaning up completed run: {run_id}")
                    del self.active_runs[run_id]
                    if run_id in self.progress_streams:
                        del self.progress_streams[run_id]
        except asyncio.CancelledError:
            logger.info(f"Cleanup cancelled for {run_id}")
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of old runs"""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                
                cutoff_time = datetime.now() - timedelta(hours=2)
                runs_to_remove: List[str] = []
                
                for run_id, run_state in self.active_runs.items():
                    try:
                        updated_at = datetime.fromisoformat(run_state["updated_at"])
                        if updated_at < cutoff_time and run_state["status"] in ["completed", "failed"]:
                            runs_to_remove.append(run_id)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid timestamp in run {run_id}: {e}")
                        runs_to_remove.append(run_id)  # Clean up invalid entries
                
                for cleanup_run_id in runs_to_remove:
                    logger.info(f"Periodic cleanup removing run: {cleanup_run_id}")
                    del self.active_runs[cleanup_run_id]
                    if cleanup_run_id in self.progress_streams:
                        del self.progress_streams[cleanup_run_id]
                        
        except asyncio.CancelledError:
            logger.info("Periodic cleanup task cancelled")
    
    def _get_next_seq(self) -> int:
        today = datetime.now().strftime('%Y%m%d')
        existing = list(self.storage_dir.glob(f"**/rr-{today}-*.json"))
        return len(existing) + 1
    
    def _save_state(self, run_id: str) -> None:
        try:
            with open(self.storage_dir / f"{run_id}.json", 'w', encoding='utf-8') as f:
                json.dump(self.active_runs[run_id], f, indent=2)
        except OSError as e:
            # FIXED: Use logger instead of print, specific exception type
            logger.error(f"Error saving state for {run_id}: {e}")

# FIXED: Pure lazy initialization without backward compatibility
_cms_rule_extraction_state: Optional[CMSRuleExtractionState] = None

def get_cms_rule_extraction_state() -> CMSRuleExtractionState:
    """Get the global state instance (lazy initialization)"""
    global _cms_rule_extraction_state
    if _cms_rule_extraction_state is None:
        _cms_rule_extraction_state = CMSRuleExtractionState()
    return _cms_rule_extraction_state