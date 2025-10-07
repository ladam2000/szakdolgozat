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
    model_id = os.environ.get("BEDROCK_MODEL_ID", "eu.amazon.nova-micro-v1:0")
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
    print("[STARTUP] Initializing AgentCore services...")
    try:
        initialize_services()
        print("[STARTUP] Services initialized successfully")
        print(f"[STARTUP] Coordinator agent: {coordinator_agent is not None}")
        print(f"[STARTUP] Memory manager: {memory_manager is not None}")
        print(f"[STARTUP] Guardrails manager: {guardrails_manager is not None}")
        print(f"[STARTUP] Observability manager: {observability_manager is not None}")
    except Exception as e:
        print(f"[STARTUP] ERROR during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    print("[HEALTH] Health check requested")
    return {
        "status": "healthy",
        "service": "travel-assistant",
        "agent_initialized": coordinator_agent is not None,
        "memory_initialized": memory_manager is not None
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat message with multi-agent system."""
    print(f"[CHAT] Received request - Session: {request.session_id}, Message: {request.message[:50]}...")
    
    try:
        # Start observability trace
        with observability_manager.trace_request(
            session_id=request.session_id,
            user_id=request.user_id,
        ) as trace:
            
            print(f"[CHAT] Starting trace: {trace.trace_id}")
            
            # Apply input guardrails
            if guardrails_manager:
                print("[CHAT] Checking input guardrails...")
                input_check = guardrails_manager.check_input(request.message)
                if not input_check["allowed"]:
                    print(f"[CHAT] Input blocked by guardrails: {input_check['reason']}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Input blocked by guardrails: {input_check['reason']}",
                    )
                print("[CHAT] Input guardrails passed")
            
            # Retrieve conversation history
            print(f"[CHAT] Retrieving conversation history...")
            history = memory_manager.get_history(request.session_id)
            print(f"[CHAT] Found {len(history)} messages in history")
            
            # Build context with history
            context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in history[-5:]  # Last 5 messages
            ])
            
            # Prepare message with context
            full_message = request.message
            if context:
                full_message = f"Previous conversation:\n{context}\n\nUser: {request.message}"
                print(f"[CHAT] Added context from {len(history[-5:])} previous messages")
            
            # Run coordinator agent
            print(f"[CHAT] Invoking coordinator agent...")
            trace.log("Running coordinator agent")
            
            try:
                response = coordinator_agent(full_message)
                print(f"[CHAT] Agent response type: {type(response)}")
                print(f"[CHAT] Agent response: {response}")
                
                # Handle different response types
                if hasattr(response, 'content'):
                    response_content = response.content
                elif isinstance(response, dict) and 'content' in response:
                    response_content = response['content']
                else:
                    response_content = str(response)
                    
                print(f"[CHAT] Agent response received: {len(response_content)} characters")
            except Exception as agent_error:
                print(f"[CHAT] ERROR in agent execution: {str(agent_error)}")
                import traceback
                traceback.print_exc()
                raise
            
            # Apply output guardrails
            if guardrails_manager:
                print("[CHAT] Checking output guardrails...")
                output_check = guardrails_manager.check_output(response_content)
                if not output_check["allowed"]:
                    response_text = "I apologize, but I cannot provide that response."
                    print(f"[CHAT] Output blocked by guardrails")
                else:
                    response_text = response_content
                    print("[CHAT] Output guardrails passed")
            else:
                response_text = response_content
            
            print(f"[CHAT] Final response length: {len(response_text)} characters")
            
            # Store in memory
            print("[CHAT] Storing messages in memory...")
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
            
            print(f"[CHAT] Request completed successfully")
            
            return ChatResponse(
                response=response_text,
                session_id=request.session_id,
                metadata={
                    "trace_id": trace.trace_id,
                    "agent": "TravelOrchestrator",
                    "specialized_agents": ["FlightBookingAgent", "HotelBookingAgent", "ActivitiesAgent"],
                },
            )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHAT] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
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
