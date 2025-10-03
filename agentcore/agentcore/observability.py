"""Observability and tracing for AgentCore."""

from typing import Dict, Any, Optional
import time
import json
import uuid
from contextlib import contextmanager


class ObservabilityManager:
    """Manages tracing and observability for agent operations."""
    
    def __init__(self, service_name: str, enable_tracing: bool = True):
        """Initialize observability manager.
        
        Args:
            service_name: Name of the service
            enable_tracing: Whether to enable tracing
        """
        self.service_name = service_name
        self.enable_tracing = enable_tracing
        self.traces = []
    
    @contextmanager
    def trace_request(self, session_id: str, user_id: Optional[str] = None):
        """Context manager for tracing a request.
        
        Args:
            session_id: Session identifier
            user_id: Optional user identifier
            
        Yields:
            Trace object
        """
        trace = Trace(
            service_name=self.service_name,
            session_id=session_id,
            user_id=user_id,
            enabled=self.enable_tracing,
        )
        
        try:
            yield trace
        finally:
            trace.end()
            if self.enable_tracing:
                self.traces.append(trace.to_dict())
                self._log_trace(trace)
    
    def _log_trace(self, trace: "Trace") -> None:
        """Log trace information.
        
        Args:
            trace: Trace object to log
        """
        print(f"[TRACE] {json.dumps(trace.to_dict())}")
    
    def log_error(self, error: str) -> None:
        """Log an error.
        
        Args:
            error: Error message
        """
        print(f"[ERROR] {error}")
    
    def get_traces(self) -> list:
        """Get all recorded traces."""
        return self.traces


class Trace:
    """Represents a single trace for a request."""
    
    def __init__(
        self,
        service_name: str,
        session_id: str,
        user_id: Optional[str] = None,
        enabled: bool = True,
    ):
        """Initialize trace.
        
        Args:
            service_name: Name of the service
            session_id: Session identifier
            user_id: Optional user identifier
            enabled: Whether tracing is enabled
        """
        self.trace_id = str(uuid.uuid4())
        self.service_name = service_name
        self.session_id = session_id
        self.user_id = user_id
        self.enabled = enabled
        self.start_time = time.time()
        self.end_time = None
        self.logs = []
        self.metrics = {}
    
    def log(self, message: str) -> None:
        """Add a log entry to the trace.
        
        Args:
            message: Log message
        """
        if self.enabled:
            self.logs.append({
                "timestamp": time.time(),
                "message": message,
            })
    
    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        """Add metrics to the trace.
        
        Args:
            metrics: Dictionary of metric name to value
        """
        if self.enabled:
            self.metrics.update(metrics)
    
    def end(self) -> None:
        """Mark the trace as ended."""
        self.end_time = time.time()
    
    def duration(self) -> float:
        """Get trace duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            "trace_id": self.trace_id,
            "service_name": self.service_name,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration(),
            "logs": self.logs,
            "metrics": self.metrics,
        }
