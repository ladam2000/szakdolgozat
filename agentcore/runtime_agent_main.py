"""AgentCore runtime with memory and Tavily search."""

import sys
import os
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from tavily import TavilyClient

# Ensure prints are flushed immediately
sys.stdout.flush()
print("[STARTUP] Initializing travel agent system...", flush=True)

# Memory configuration
MEMORY_ID = "memory_rllrl-lfg7zBH6MH"
BRANCH_NAME = "main"
REGION = "eu-central-1"

# Create the AgentCore app
print("[MEMORY] Initializing AgentCore app...", flush=True)
app = BedrockAgentCoreApp()

# Initialize memory client
print(f"[MEMORY] Initializing MemoryClient for region: {REGION}", flush=True)
memory_client = MemoryClient(region_name=REGION)
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


# Memory tool
@tool
def memory_tool(action: str, content: str = None, query: str = None) -> str:
    """
    Manage conversation memory.
    
    Actions:
    - "save": Store important information (requires content)
    - "search": Search for relevant memories (requires query)
    
    Args:
        action: Either "save" or "search"
        content: Text to save (for save action)
        query: Search query (for search action)
    
    Returns:
        Result of the memory operation
    """
    try:
        # Get session context from tool attribute
        session_id = getattr(memory_tool, '_session_id', 'default_session')
        actor_id = f"travel-user-{session_id}"
        
        print(f"[MEMORY TOOL] Action: {action}, session: {session_id}", flush=True)
        
        if action == "save":
            if not content:
                return "Error: content is required for save action"
            
            # Store in memory
            memory_client.create_event(
                memory_id=MEMORY_ID,
                actor_id=actor_id,
                session_id=session_id,
                messages=[(content, "assistant")]
            )
            print(f"[MEMORY TOOL] Saved: {content[:100]}...", flush=True)
            return f"Successfully saved to memory: {content}"
        
        elif action == "search":
            if not query:
                return "Error: query is required for search action"
            
            # Search memory
            result = memory_client.get_last_k_turns(
                memory_id=MEMORY_ID,
                actor_id=actor_id,
                session_id=session_id,
                k=10,
                branch_name=BRANCH_NAME
            )
            
            events = result.get("events", [])
            if not events:
                return "No previous memories found"
            
            # Extract and format memories
            memories = []
            for event in events:
                payload = event.get("payload", {})
                messages = payload.get("messages", [])
                for msg in messages:
                    content = msg.get("content", "")
                    if isinstance(content, dict):
                        content = content.get("text", str(content))
                    if content and query.lower() in content.lower():
                        memories.append(content)
            
            if memories:
                result_text = "\n".join(memories[:5])  # Return top 5 matches
                print(f"[MEMORY TOOL] Found {len(memories)} memories", flush=True)
                return f"Found memories:\n{result_text}"
            else:
                return f"No memories found matching: {query}"
        
        else:
            return f"Error: Unknown action '{action}'. Use 'save' or 'search'"
    
    except Exception as e:
        print(f"[MEMORY TOOL] ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return f"Memory error: {str(e)}"


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
        
        # Create agent with tools
        tools = [memory_tool, search_web] if tavily_client else [memory_tool]
        
        agent = Agent(
            name="TravelPlanningAgent",
            model="eu.amazon.nova-micro-v1:0",
            tools=tools
        )
        
        search_capability = "and real-time web search" if tavily_client else "(search disabled - no API key)"
        
        agent.system_prompt = f"""I am an AI system built by Adam Laszlo to help you plan your travel.

CRITICAL: ALWAYS start by checking memory with memory_tool(action="search", query="travel details") to see what you already know about this conversation.

REQUIRED INFORMATION:
To provide travel recommendations, I need:
1. Origin city (where you're traveling from)
2. Destination city (where you're going)
3. Travel dates (specific dates)

WORKFLOW:
1. FIRST: memory_tool(action="search", query="travel details") - Check what you already know
2. If you find origin/destination/dates in memory, use them immediately
3. If missing information, ask for it
4. ALWAYS: memory_tool(action="save", content="...") - Save each piece of information as you receive it
5. Once you have all three, immediately search_web and provide recommendations

TOOLS:
- memory_tool(action="search", query="...") - Search your memories FIRST
- memory_tool(action="save", content="...") - Save important details ALWAYS
- search_web(query="...") - Find real-time information

SEARCH APPROACH:
- Flights: search_web(query="flights from [origin] to [destination] [dates]")
- Hotels: search_web(query="booking.com hotels [destination] [dates] best value")
- Activities: search_web(query="things to do [destination] [dates]")

REMEMBER: Check memory FIRST, save information ALWAYS, search when you have all three pieces."""
        
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
        
        # Set session context for tools
        memory_tool._session_id = session_id
        
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
print(f"[RUNTIME] Tools: memory_tool + search_web", flush=True)
print("[RUNTIME] Ready to process requests!", flush=True)

# Run the app
if __name__ == "__main__":
    print("[RUNTIME] Starting AgentCore app...", flush=True)
    app.run()
