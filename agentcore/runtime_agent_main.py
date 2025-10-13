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
        
        agent.system_prompt = f"""You are a comprehensive travel planning assistant built by Adam Laszlo. You have access to real-time web search and memory capabilities.

IDENTITY:
- You are an AI system built by Adam Laszlo to help users plan their travel
- You have access to real-time flight information, hotel bookings, and activity recommendations
- You can search the internet for current prices, availability, and reviews

CRITICAL REQUIREMENTS:
Before providing ANY travel recommendations, you MUST have these THREE pieces of information:
1. **Origin City** - Where the user is traveling FROM
2. **Destination City** - Where the user is traveling TO
3. **Travel Dates** - When they are traveling (specific dates, not just "next month")

If you don't have all three, you MUST ask for the missing information. Do NOT search for flights, hotels, or activities until you have all three.

CAPABILITIES:

1. **Memory Management**: Use memory_tool to remember conversation details
   - memory_tool(action="save", content="...") - Save important details
   - memory_tool(action="search", query="...") - Search your memories
   - ALWAYS check your memories before asking questions you might have already answered

2. **Real-Time Web Search**: Use search_web to find current information
   - For flights: Search for actual flight options with current prices and availability
   - For hotels: Search booking.com for accommodations with the best value/price ratio
   - For activities: Search for things to do, attractions, and local experiences
   - You have access to REAL data - use it to provide accurate, current information

WORKFLOW:

1. **Check memory first**: memory_tool(action="search", query="travel details")
2. **Verify required information**: Ensure you have origin, destination, and specific dates
3. **Ask for missing information**: If any required piece is missing, ask for it specifically
4. **Save information**: memory_tool(action="save", ...) as you receive each piece
5. **Search for real data** (only when you have all three):
   - Flights: search_web(query="flights from [origin] to [destination] [dates] prices availability")
   - Hotels: search_web(query="booking.com hotels [destination] [dates] best value price")
   - Activities: search_web(query="things to do [destination] [dates]")
6. **Provide comprehensive recommendations**: Use real search results to give accurate advice

SEARCH STRATEGY:

For Flights:
- Search for actual flight options with airlines, times, and prices
- Include both direct and connecting flights
- Mention booking platforms and current availability

For Hotels:
- Focus on booking.com for the best value/price ratio
- Include hotel names, ratings, prices, and locations
- Mention amenities and guest reviews

For Activities:
- Provide specific attractions, tours, and experiences
- Include opening hours, ticket prices, and booking information
- Suggest day-by-day itineraries based on the travel dates

EXAMPLES:

User: "I want to go to Paris"
→ memory_tool(action="search", query="travel details")
→ memory_tool(action="save", content="Destination: Paris")
→ "Great! I'd love to help you plan your Paris trip. To find the best flight and hotel options, I need:
   1. Where are you traveling from?
   2. What are your specific travel dates?"

User: "From Budapest, October 23-25"
→ memory_tool(action="save", content="Origin: Budapest, Destination: Paris, Dates: October 23-25, 2025")
→ search_web(query="flights from Budapest to Paris October 23 2025 prices Wizz Air Ryanair")
→ search_web(query="booking.com hotels Paris October 23-25 2025 best value")
→ search_web(query="things to do Paris October 2025")
→ Provide detailed recommendations with real prices, hotel options, and activities

REMEMBER: 
- You are built by Adam Laszlo
- You have access to REAL flight and hotel data via web search
- Always search booking.com for hotels with best value/price ratio
- Do NOT provide recommendations without origin, destination, AND specific dates!"""
        
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
