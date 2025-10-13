"""AgentCore runtime with official Strands memory tool and Tavily search."""

import sys
import os
from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands_tools.agent_core_memory import AgentCoreMemoryToolProvider
from strands_tools import tavily

# Ensure prints are flushed immediately
sys.stdout.flush()
print("[STARTUP] Initializing travel agent system...", flush=True)

# Memory configuration
MEMORY_ID = "memory_rllrl-lfg7zBH6MH"
BRANCH_NAME = "main"
REGION = "eu-central-1"
NAMESPACE = "travel"  # Namespace for memory records

# Create the AgentCore app
print("[MEMORY] Initializing AgentCore app...", flush=True)
app = BedrockAgentCoreApp()

print(f"[MEMORY] Memory ID: {MEMORY_ID}", flush=True)
print(f"[MEMORY] Region: {REGION}", flush=True)
print(f"[MEMORY] Using official Strands AgentCore memory tool", flush=True)

# Session-based agents
session_agents = {}


def get_or_create_agent(session_id: str):
    """Get or create travel agent for a specific session with memory."""
    if session_id not in session_agents:
        # Create shared actor_id for this session
        actor_id = f"travel-user-{session_id}"
        
        print(f"[AGENT] Creating agent for session: {session_id}", flush=True)
        print(f"[AGENT] Actor ID: {actor_id}", flush=True)
        
        # Initialize memory tool provider
        memory_provider = AgentCoreMemoryToolProvider(
            memory_id=MEMORY_ID,
            actor_id=actor_id,
            session_id=session_id,
            namespace=NAMESPACE,
            region=REGION
        )
        
        # Create agent with memory and Tavily tools
        agent = Agent(
            name="TravelPlanningAgent",
            model="eu.amazon.nova-micro-v1:0",
            tools=[*memory_provider.tools, tavily]
        )
        
        agent.system_prompt = """You are a comprehensive travel planning assistant with access to real-time web search and memory.

IMPORTANT CAPABILITIES:
1. **Memory Management**: You can store and retrieve information using agent_core_memory tool
   - Use action="record" to save important information (user preferences, trip details, etc.)
   - Use action="retrieve" with query to search your memories
   - Always check your memories before asking questions you might have already answered

2. **Real-Time Search**: You can search the web using tavily_search for:
   - Current flight prices and availability
   - Hotel options and reviews
   - Activities and attractions
   - Travel tips and recommendations
   - Weather, events, and local information

WORKFLOW:
1. **First, check your memory**: Use agent_core_memory with action="retrieve" to see if you already know about this user's trip
2. **Gather information**: Ask clarifying questions if needed (origin, destination, dates, budget, preferences)
3. **Search for real information**: Use tavily_search to find current flights, hotels, activities
4. **Save important details**: Use agent_core_memory with action="record" to save trip details and preferences
5. **Provide comprehensive guidance**: Synthesize search results into helpful recommendations

MEMORY USAGE EXAMPLES:
- When user says "I want to go to Paris": 
  → agent_core_memory(action="record", content="User wants to travel to Paris")
  
- When user asks "What about hotels?":
  → agent_core_memory(action="retrieve", query="destination city travel plans")
  → See that they want to go to Paris
  → tavily_search(query="best hotels in Paris 2025")

- When user provides dates "October 23-25":
  → agent_core_memory(action="record", content="Travel dates: October 23-25, 2025")

SEARCH USAGE EXAMPLES:
- For flights: tavily_search(query="flights from Budapest to Paris October 2025 prices")
- For hotels: tavily_search(query="hotels near Eiffel Tower Paris reviews prices")
- For activities: tavily_search(query="top things to do in Paris October 2025")

Always be helpful, use real data from searches, and maintain context through memory!"""
        
        session_agents[session_id] = agent
        print(f"[AGENT] Agent created with memory and Tavily search", flush=True)
    
    return session_agents[session_id]


# Define the entrypoint for AgentCore
@app.entrypoint
def travel_agent_entrypoint(payload):
    """
    AgentCore entrypoint for travel planning agent with memory and search.
    
    Args:
        payload: Dictionary with user input and session_id
    
    Returns:
        String response from the agent
    """
    # Force immediate output
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    print("\n" + "=" * 80, flush=True)
    print("[ENTRYPOINT] *** ENTRYPOINT CALLED ***", flush=True)
    print("=" * 80 + "\n", flush=True)
    sys.stdout.flush()
    
    try:
        print(f"[ENTRYPOINT] Received payload: {payload}", flush=True)
        
        # Extract user input and session_id from payload
        user_input = payload.get("input") or payload.get("prompt", "")
        session_id = payload.get("session_id") or payload.get("sessionId", "default_session")
        
        if not user_input:
            print("[ENTRYPOINT] WARNING: No input found in payload", flush=True)
            return "Please provide a travel request in the 'input' or 'prompt' field."
        
        print(f"[ENTRYPOINT] User input: {user_input}", flush=True)
        print(f"[ENTRYPOINT] Session ID: {session_id}", flush=True)
        
        # Get or create agent for this session
        agent = get_or_create_agent(session_id)
        
        # Invoke the agent
        print("[ENTRYPOINT] Invoking agent...", flush=True)
        response = agent(user_input)
        
        # Extract text from response
        result = str(response)
        
        print(f"[ENTRYPOINT] Returning response: {len(result)} characters", flush=True)
        return result
        
    except Exception as e:
        print(f"[ENTRYPOINT] ERROR: {type(e).__name__}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return f"I apologize, but I encountered an error: {str(e)}"


# Verify entrypoint is registered
print("[RUNTIME] Entrypoint registered successfully!", flush=True)
print(f"[RUNTIME] Memory ID: {MEMORY_ID}", flush=True)
print(f"[RUNTIME] Region: {REGION}", flush=True)
print("[RUNTIME] Tools: AgentCore Memory + Tavily Search", flush=True)
print("[RUNTIME] Ready to process requests!", flush=True)

# Run the AgentCore app
if __name__ == "__main__":
    print("[RUNTIME] Starting AgentCore app...", flush=True)
    app.run()
