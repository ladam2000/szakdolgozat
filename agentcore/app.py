"""AgentCore service with memory, guardrails, and observability."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import boto3
import os
import json
from mangum import Mangum

# AgentCore imports
from agentcore.memory import ShortTermMemory
from agentcore.guardrails import GuardrailsManager
from agentcore.observability import ObservabilityManager

# Strands imports
from strands import Agent

# Local imports
from agents import create_coordinator_agent


app = FastAPI(title="Travel Assistant API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None


# Global state
coordinator_agent = None
memory_manager = None
guardrails_manager = None
observability_manager = None


def initialize_services():
    """Initialize AWS services and agents."""
    global coordinator_agent, memory_manager, guardrails_manager, observability_manager
    
    region = os.environ.get("AWS_REGION", "eu-central-1")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    guardrail_id = os.environ.get("GUARDRAIL_ID")
    guardrail_version = os.environ.get("GUARDRAIL_VERSION", "DRAFT")
    
    # Initialize Bedrock client for guardrails
    bedrock_client = boto3.client("bedrock-runtime", region_name=region)
    
    # Initialize memory manager
    memory_manager = ShortTermMemory(max_messages=20)
    
    # Initialize guardrails if configured
    if guardrail_id:
        guardrails_manager = GuardrailsManager(
            bedrock_client=bedrock_client,
            guardrail_id=guardrail_id,
            guardrail_version=guardrail_version,
        )
    
    # Initialize observability
    observability_manager = ObservabilityManager(
        service_name="travel-assistant",
        enable_tracing=True,
    )
    
    # Create coordinator agent (Strands handles Bedrock internally)
    coordinator_agent = create_coordinator_agent()


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    initialize_services()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "travel-assistant"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat message with multi-agent system."""
    try:
        # Start observability trace
        with observability_manager.trace_request(
            session_id=request.session_id,
            user_id=request.user_id,
        ) as trace:
            
            # Apply input guardrails
            if guardrails_manager:
                input_check = guardrails_manager.check_input(request.message)
                if not input_check["allowed"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Input blocked by guardrails: {input_check['reason']}",
                    )
            
            # Retrieve conversation history
            history = memory_manager.get_history(request.session_id)
            
            # Build context with history
            context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in history[-5:]  # Last 5 messages
            ])
            
            # Prepare message with context
            full_message = request.message
            if context:
                full_message = f"Previous conversation:\n{context}\n\nUser: {request.message}"
            
            # Run coordinator agent
            trace.log("Running coordinator agent")
            response = coordinator_agent.run(full_message)
            
            # Apply output guardrails
            if guardrails_manager:
                output_check = guardrails_manager.check_output(response.content)
                if not output_check["allowed"]:
                    response_text = "I apologize, but I cannot provide that response."
                else:
                    response_text = response.content
            else:
                response_text = response.content
            
            # Store in memory
            memory_manager.add_message(
                session_id=request.session_id,
                role="user",
                content=request.message,
            )
            memory_manager.add_message(
                session_id=request.session_id,
                role="assistant",
                content=response_text,
            )
            
            # Log metrics
            trace.log_metrics({
                "response_length": len(response_text),
                "history_size": len(history),
            })
            
            return ChatResponse(
                response=response_text,
                session_id=request.session_id,
                metadata={
                    "trace_id": trace.trace_id,
                    "agent": "TravelCoordinator",
                },
            )
    
    except Exception as e:
        if observability_manager:
            observability_manager.log_error(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_session(session_id: str):
    """Reset conversation memory for a session."""
    memory_manager.clear_session(session_id)
    return {"status": "success", "message": "Session reset"}


# Lambda handler using Mangum
from mangum import Mangum
handler = Mangum(app, lifespan="off")
