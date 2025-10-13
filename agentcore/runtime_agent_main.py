"""AgentCore runtime with memory and Tavily search."""

import sys
import os
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tavily import TavilyClient

# Ensure prints are flushed immediately
sys.stdout.flush()
print("[STARTUP] Initializing travel agent system...", flush=True)

# Memory configuration
MEMORY_ID = "memory_rllrl-lfg7zBH6MH"
REGION = "eu-central-1"

# Create the AgentCore app with memory enabled
print("[MEMORY] Initializing AgentCore app with memory...", flush=True)
app = BedrockAgentCoreApp(
    memory_id=MEMORY_ID,
    region_name=REGION
)
print(f"[MEMORY] Memory ID: {MEMORY_ID}", flush=True)

# Initialize Tavily client
tavily_api_key = os.getenv("TAVILY_API_KEY")
if tavily_api_key:
    tavily_client = TavilyClient(api_key=tavily_api_key)
    print("[SEARCH] Tavily client initialized", flush=True)
else:
    tavily_client = None
    print("[SEARCH] WARNING: TAVILY_API_KEY not set, search will be disabled", flush=True)

# Session-based agents
session_agents = {}


# Search tool
@tool
def search_web(query: str) -> str:
    """
    Search the web for current information.
    
    Use this to find:
    - Flight prices and availability
    - Hotel options and reviews
    - Activities and attractions
    - Weather and events
    - Any real-time travel information
    
    Args:
        query: Search query (e.g., "flights from Budapest to Paris October 2025")
    
    Returns:
        Search results with relevant information
    """
    try:
        if not tavily_client:
            return "Search is not available (TAVILY_API_KEY not configured)"
        
        print(f"[SEARCH] Query: {query}", flush=True)
        
        # Perform search
        response = tavily_client.search(
            query=query,
            max_results=5,
            include_answer=True
        )
        
        # Format results
        results = []
        
        # Add AI-generated answer if available
        if response.get("answer"):
            results.append(f"Summary: {response['answer']}\n")
        
        # Add search results
        for i, result in enumerate(response.get("results", []), 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            content = result.get("content", "")
            
            results.append(f"{i}. {title}")
            if content:
                results.append(f"   {content[:200]}...")
            if url:
                results.append(f"   Source: {url}")
            results.append("")
        
        result_text = "\n".join(results)
        print(f"[SEARCH] Found {len(response.get('results', []))} results", flush=True)
        return result_text if result_text else "No results found"
    
    except Exception as e:
        print(f"[SEARCH] ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return f"Search error: {str(e)}"


def get_or_create_agent(session_id: str):
    """Get or create travel agent for a specific session."""
    if session_id not in session_agents:
        print(f"[AGENT] Creating agent for session: {session_id}", flush=True)
        
        # Create agent with search tool only
        tools = [search_web] if tavily_client else []
        
        agent = Agent(
            name="TravelPlanningAgent",
            model="eu.amazon.nova-micro-v1:0",
            tools=tools
        )
        
        search_info = "Use search_web to find real-time travel information." if tavily_client else "Search is currently unavailable."
        
        agent.system_prompt = f"""I am a travel planning assistant built by Adam Laszlo.

I help you plan trips by gathering three key pieces of information:
1. Origin city (where you're traveling from)
2. Destination city (where you're going)  
3. Travel dates (specific dates)

IMPORTANT: I have access to our full conversation history automatically. I can see everything we've discussed.

When you provide travel details, I will:
- Remember all information from our conversation
- Use search_web to find current flights, hotels, and activities
- Provide personalized recommendations

{search_info}

Let's plan your trip!"""
        
        session_agents[session_id] = agent
        print(f"[AGENT] Agent created with {len(tools)} tools", flush=True)
    
    return session_agents[session_id]


# Define the entrypoint for AgentCore
@app.entrypoint
def travel_agent_entrypoint(payload):
    """
    AgentCore entrypoint for travel planning agent.
    
    Args:
        payload: Dictionary with user input and session_id
    
    Returns:
        String response from the agent
    """
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    print("\n" + "=" * 80, flush=True)
    print("[ENTRYPOINT] *** ENTRYPOINT CALLED ***", flush=True)
    print("=" * 80 + "\n", flush=True)
    sys.stdout.flush()
    
    try:
        print(f"[ENTRYPOINT] Received payload: {payload}", flush=True)
        
        # Extract user input and session_id
        user_input = payload.get("input") or payload.get("prompt", "")
        session_id = payload.get("session_id") or payload.get("sessionId", "default_session")
        
        if not user_input:
            return "Please provide a travel request in the 'input' or 'prompt' field."
        
        print(f"[ENTRYPOINT] User input: {user_input}", flush=True)
        print(f"[ENTRYPOINT] Session ID: {session_id}", flush=True)
        
        # Get or create agent
        agent = get_or_create_agent(session_id)
        
        # Invoke agent
        print("[ENTRYPOINT] Invoking agent...", flush=True)
        response = agent(user_input)
        
        # Extract text
        result = str(response)
        
        print(f"[ENTRYPOINT] Returning response: {len(result)} characters", flush=True)
        return result
        
    except Exception as e:
        print(f"[ENTRYPOINT] ERROR: {type(e).__name__}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return f"I apologize, but I encountered an error: {str(e)}"


# Verify entrypoint
print("[RUNTIME] Entrypoint registered successfully!", flush=True)
print(f"[RUNTIME] Memory ID: {MEMORY_ID}", flush=True)
print(f"[RUNTIME] Region: {REGION}", flush=True)
print(f"[RUNTIME] Memory: Built-in AgentCore memory enabled", flush=True)
print(f"[RUNTIME] Tools: search_web", flush=True)
print("[RUNTIME] Ready to process requests!", flush=True)

# Run the app
if __name__ == "__main__":
    print("[RUNTIME] Starting AgentCore app...", flush=True)
    app.run()
