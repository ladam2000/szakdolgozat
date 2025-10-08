"""AgentCore runtime main entry point with orchestrator pattern and memory."""

import sys
import logging
from datetime import datetime
from strands import Agent, tool
from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
import json

# Ensure prints are flushed immediately
sys.stdout.flush()
print("[STARTUP] Initializing orchestrator agent system...", flush=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("agentcore-memory")

# Memory configuration
MEMORY_ID = "memory_rllrl-lfg7zBH6MH"
BRANCH_NAME = "main"

# Create the AgentCore app
print("[MEMORY] Initializing AgentCore app...", flush=True)
app = BedrockAgentCoreApp()

# Initialize memory client
memory_client = MemoryClient()
print(f"[MEMORY] Memory ID: {MEMORY_ID}", flush=True)
print(f"[MEMORY] Branch: {BRANCH_NAME}", flush=True)


# Memory Hook Provider (from AWS reference)
class ShortTermMemoryHook(HookProvider):
    def __init__(self, memory_client: MemoryClient, memory_id: str):
        self.memory_client = memory_client
        self.memory_id = memory_id
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load recent conversation history when agent starts"""
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return
            
            # Get last 5 conversation turns
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=5,
                branch_name=BRANCH_NAME
            )
            
            if recent_turns and recent_turns.get("events"):
                # Format conversation history for context
                context_messages = []
                for event_data in recent_turns["events"]:
                    payload = event_data.get("payload", {})
                    messages = payload.get("messages", [])
                    for message in messages:
                        role = message.get('role', '').lower()
                        content = message.get('content', '')
                        if isinstance(content, dict):
                            content = content.get('text', str(content))
                        context_messages.append(f"{role.title()}: {content}")
                
                if context_messages:
                    context = "\n".join(context_messages)
                    logger.info(f"Context from memory: {context[:200]}...")
                    
                    # Add context to agent's system prompt
                    event.agent.system_prompt += f"\n\nRecent conversation history:\n{context}\n\nContinue the conversation naturally based on this context."
                    
                    logger.info(f"✅ Loaded {len(context_messages)} recent messages")
            else:
                logger.info("No previous conversation history found")
                
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
    
    def on_message_added(self, event: MessageAddedEvent):
        """Store conversation turns in memory"""
        messages = event.agent.messages
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return
            
            # Store the last message
            if messages:
                last_message = messages[-1]
                content = last_message.get("content", [{}])[0].get("text", "")
                role = last_message.get("role", "")
                
                self.memory_client.create_event(
                    memory_id=self.memory_id,
                    actor_id=actor_id,
                    session_id=session_id,
                    messages=[(content, role)]
                )
                logger.info(f"✅ Stored message in memory: {role}")
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
    
    def register_hooks(self, registry: HookRegistry) -> None:
        # Register memory hooks
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)


# Specialized Agent 1: Flight Booking Agent
def create_flight_agent(actor_id: str, session_id: str) -> Agent:
    """Create specialized agent for flight bookings with memory."""
    memory_hooks = ShortTermMemoryHook(memory_client, MEMORY_ID)
    
    agent = Agent(
        name="FlightBookingAgent",
        model="eu.amazon.nova-micro-v1:0",
        hooks=[memory_hooks],
        state={"actor_id": actor_id, "session_id": session_id}
    )
    
    agent.system_prompt = """You are a flight booking specialist assistant.

IMPORTANT: You are a demonstration assistant and do NOT have access to real flight booking systems or live flight data.

Your role:
- Help users understand what to look for when booking flights
- Provide general guidance on flight search strategies
- Explain typical flight options and pricing considerations
- Suggest what factors to consider (timing, airlines, connections)

When responding:
- Be clear that you're providing example information, not real bookings
- Explain what users should look for when searching flights
- Provide realistic example scenarios based on the requested route
- Suggest checking actual booking sites for current availability and prices

Example response:
"For flights from New York to Paris, you'll typically find:
- Direct flights: Usually 7-8 hours, prices range from $400-$800 depending on season
- Airlines to check: Air France, Delta, United, American Airlines
- Best times to book: 2-3 months in advance for better prices
- Consider: Morning vs evening departures, baggage policies, layover options

I recommend checking sites like Google Flights, Kayak, or airline websites directly for current availability and exact pricing."

Always remind users to verify information on actual booking platforms."""
    
    return agent


# Specialized Agent 2: Hotel Booking Agent
def create_hotel_agent(actor_id: str, session_id: str) -> Agent:
    """Create specialized agent for hotel bookings with memory."""
    memory_hooks = ShortTermMemoryHook(memory_client, MEMORY_ID)
    
    agent = Agent(
        name="HotelBookingAgent",
        model="eu.amazon.nova-micro-v1:0",
        hooks=[memory_hooks],
        state={"actor_id": actor_id, "session_id": session_id}
    )
    
    agent.system_prompt = """You are a hotel booking specialist assistant.

IMPORTANT: You are a demonstration assistant and do NOT have access to real hotel booking systems or live hotel data.

Your role:
- Help users understand what to look for when booking hotels
- Provide general guidance on hotel selection criteria
- Explain typical hotel options and pricing in different cities
- Suggest what factors to consider (location, amenities, ratings)

When responding:
- Be clear that you're providing example information, not real bookings
- Explain what users should look for when searching hotels
- Provide realistic guidance based on the requested city
- Suggest checking actual booking sites for current availability and prices

Example response:
"For hotels in Paris, here's what to consider:
- Location: Near Eiffel Tower, Louvre, or Marais district for tourists
- Price ranges: Budget €80-120/night, Mid-range €150-250/night, Luxury €300+/night
- Popular areas: 7th arrondissement (Eiffel Tower), 1st arrondissement (Louvre)
- Amenities to look for: WiFi, breakfast included, air conditioning
- Booking sites to check: Booking.com, Hotels.com, Expedia, or hotel websites directly

I recommend reading recent reviews and comparing prices across multiple platforms for the best deals."

Always remind users to verify information on actual booking platforms."""
    
    return agent


# Specialized Agent 3: Activities Agent
def create_activities_agent(actor_id: str, session_id: str) -> Agent:
    """Create specialized agent for activities and attractions with memory."""
    memory_hooks = ShortTermMemoryHook(memory_client, MEMORY_ID)
    
    agent = Agent(
        name="ActivitiesAgent",
        model="eu.amazon.nova-micro-v1:0",
        hooks=[memory_hooks],
        state={"actor_id": actor_id, "session_id": session_id}
    )
    
    agent.system_prompt = """You are a local activities and attractions specialist assistant.

IMPORTANT: You are a demonstration assistant providing general travel guidance, not real-time booking or ticketing.

Your role:
- Recommend popular activities and attractions in cities
- Provide general information about tours, museums, and entertainment
- Suggest typical timing and approximate pricing
- Help create day-by-day itinerary ideas

When responding:
- Provide well-known, real attractions and activities
- Give approximate pricing and typical opening hours
- Suggest realistic itineraries based on the destination
- Recommend checking official websites for current information

Example response:
"For activities in Paris, here are some popular options:

Must-see attractions:
- Eiffel Tower: €25-30, allow 2-3 hours, book tickets online in advance
- Louvre Museum: €17, plan for 3-4 hours, closed Tuesdays
- Notre-Dame Cathedral: Free exterior viewing (interior closed for restoration)
- Arc de Triomphe: €13, 30-45 minutes

Day trip ideas:
- Versailles Palace: €20, full day trip, take RER C train
- Montmartre walking tour: Free to explore, 2-3 hours

I recommend checking official websites and booking platforms like GetYourGuide or Viator for current prices and availability."

Always provide real, well-known attractions and remind users to verify current information."""
    
    return agent


# Store session-specific agents (will be created per session)
session_agents = {}
session_orchestrators = {}

def get_or_create_agents(session_id: str):
    """Get or create agents for a specific session."""
    if session_id not in session_agents:
        flight_actor_id = f"flight-{session_id}"
        hotel_actor_id = f"hotel-{session_id}"
        activities_actor_id = f"activities-{session_id}"
        
        session_agents[session_id] = {
            'flight': create_flight_agent(flight_actor_id, session_id),
            'hotel': create_hotel_agent(hotel_actor_id, session_id),
            'activities': create_activities_agent(activities_actor_id, session_id)
        }
        print(f"[AGENT] Created specialized agents for session: {session_id}", flush=True)
    
    return session_agents[session_id]


def get_or_create_orchestrator(session_id: str):
    """Get or create orchestrator agent with memory for a specific session."""
    if session_id not in session_orchestrators:
        orchestrator_actor_id = f"orchestrator-{session_id}"
        
        # Create memory hooks for orchestrator
        orchestrator_memory_hooks = ShortTermMemoryHook(memory_client, MEMORY_ID)
        
        orchestrator = Agent(
            name="TravelOrchestrator",
            model="eu.amazon.nova-micro-v1:0",
            tools=[flight_booking_tool, hotel_booking_tool, activities_tool],
            hooks=[orchestrator_memory_hooks],
            state={"actor_id": orchestrator_actor_id, "session_id": session_id}
        )
        
        orchestrator.system_prompt = """You are a travel planning orchestrator that coordinates specialized agents.

CRITICAL: You MUST delegate to specialized agents for ANY travel-related requests. Do NOT answer directly.

Your role:
- Immediately identify which specialized agent(s) to call based on user request
- Delegate to: flight_booking_tool, hotel_booking_tool, activities_tool
- Pass the user's full request to the appropriate tool(s)
- Synthesize responses from agents into a cohesive answer

Delegation rules:
- ANY mention of flights, airlines, flying → ALWAYS call flight_booking_tool
- ANY mention of hotels, accommodation, lodging → ALWAYS call hotel_booking_tool  
- ANY mention of activities, attractions, things to do → ALWAYS call activities_tool
- For complete trip planning → Call multiple tools as needed

Examples:
- User: "I want to go to Paris" → Call flight_booking_tool("User wants to go to Paris, needs flight information")
- User: "Find hotels in Tokyo" → Call hotel_booking_tool("User needs hotels in Tokyo")
- User: "Plan a trip to Rome" → Call all three tools with the request
- User: "What about flights?" → Call flight_booking_tool with the full conversation context

IMPORTANT: The specialized agents have memory and will remember previous conversation context. 
Always delegate to them - they will provide better, context-aware responses than you can."""
        
        session_orchestrators[session_id] = orchestrator
        print(f"[AGENT] Created orchestrator with memory for session: {session_id}", flush=True)
    
    return session_orchestrators[session_id]


# Convert agents to tools for the orchestrator
@tool
def flight_booking_tool(query: str) -> str:
    """Search and book flights.
    
    Args:
        query: Flight search request (origin, destination, dates, preferences)
    """
    try:
        print(f"[FLIGHT AGENT] Processing: {query}", flush=True)
        # Get session_id from context (will be set in entrypoint)
        session_id = getattr(flight_booking_tool, '_session_id', 'default_session')
        agents = get_or_create_agents(session_id)
        
        response = agents['flight'](query)
        print(f"[FLIGHT AGENT] Response type: {type(response)}", flush=True)
        
        # Extract text from Strands response
        result = str(response)
        
        print(f"[FLIGHT AGENT] Returning: {len(result)} characters", flush=True)
        return result
    except Exception as e:
        print(f"[FLIGHT AGENT] ERROR: {str(e)}", flush=True)
        return f"Error searching flights: {str(e)}"


@tool
def hotel_booking_tool(query: str) -> str:
    """Search and book hotels.
    
    Args:
        query: Hotel search request (city, dates, preferences, budget)
    """
    try:
        print(f"[HOTEL AGENT] Processing: {query}", flush=True)
        # Get session_id from context (will be set in entrypoint)
        session_id = getattr(hotel_booking_tool, '_session_id', 'default_session')
        agents = get_or_create_agents(session_id)
        
        response = agents['hotel'](query)
        print(f"[HOTEL AGENT] Response type: {type(response)}", flush=True)
        
        # Extract text from Strands response
        result = str(response)
        
        print(f"[HOTEL AGENT] Returning: {len(result)} characters", flush=True)
        return result
    except Exception as e:
        print(f"[HOTEL AGENT] ERROR: {str(e)}", flush=True)
        return f"Error searching hotels: {str(e)}"


@tool
def activities_tool(query: str) -> str:
    """Find activities and attractions.
    
    Args:
        query: Activities request (city, dates, interests, preferences)
    """
    try:
        print(f"[ACTIVITIES AGENT] Processing: {query}", flush=True)
        # Get session_id from context (will be set in entrypoint)
        session_id = getattr(activities_tool, '_session_id', 'default_session')
        agents = get_or_create_agents(session_id)
        
        response = agents['activities'](query)
        print(f"[ACTIVITIES AGENT] Response type: {type(response)}", flush=True)
        
        # Extract text from Strands response
        result = str(response)
        
        print(f"[ACTIVITIES AGENT] Returning: {len(result)} characters", flush=True)
        return result
    except Exception as e:
        print(f"[ACTIVITIES AGENT] ERROR: {str(e)}", flush=True)
        return f"Error searching activities: {str(e)}"


# Orchestrator agents will be created per session with memory hooks
print("[AGENT] Orchestrator agent factory ready", flush=True)
print("[AGENT] Specialized agents: FlightBookingAgent, HotelBookingAgent, ActivitiesAgent", flush=True)
print(f"[AGENT] Tools: {[tool.__name__ for tool in [flight_booking_tool, hotel_booking_tool, activities_tool]]}", flush=True)


# Define the entrypoint for AgentCore
@app.entrypoint
def travel_orchestrator_entrypoint(payload):
    """
    AgentCore entrypoint for the travel orchestrator with memory support via Strands hooks.
    
    Args:
        payload: Dictionary with user input and session_id
    
    Returns:
        String response from the orchestrator agent
    """
    # Force immediate output
    import sys
    import os
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    print("\n" + "=" * 80, flush=True)
    print("[ENTRYPOINT] *** ENTRYPOINT CALLED ***", flush=True)
    print("=" * 80 + "\n", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    
    try:
        print(f"[ENTRYPOINT] Received payload: {payload}", flush=True)
        print(f"[ENTRYPOINT] Payload type: {type(payload)}", flush=True)
        print(f"[ENTRYPOINT] Payload keys: {list(payload.keys()) if isinstance(payload, dict) else 'Not a dict'}", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Extract user input and session_id from payload
        # Handle both snake_case and camelCase for compatibility
        user_input = payload.get("input") or payload.get("prompt", "")
        session_id = payload.get("session_id") or payload.get("sessionId", "default_session")
        
        if not user_input:
            print("[ENTRYPOINT] WARNING: No input found in payload", flush=True)
            return "Please provide a travel request in the 'input' or 'prompt' field."
        
        print(f"[ENTRYPOINT] User input: {user_input}", flush=True)
        print(f"[ENTRYPOINT] Session ID: {session_id}", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Set session_id in tool context for specialized agents
        flight_booking_tool._session_id = session_id
        hotel_booking_tool._session_id = session_id
        activities_tool._session_id = session_id
        
        # Get or create orchestrator with memory for this session
        orchestrator = get_or_create_orchestrator(session_id)
        
        # Invoke the orchestrator agent
        # Memory is handled automatically by Strands hooks in orchestrator AND specialized agents
        print("[ENTRYPOINT] Invoking orchestrator agent...", flush=True)
        print("[MEMORY] Memory operations handled by Strands hooks (orchestrator + specialized agents)", flush=True)
        response = orchestrator(user_input)
        print(f"[ENTRYPOINT] Agent response type: {type(response)}", flush=True)
        
        # Extract text from response
        result = str(response)
        
        print(f"[ENTRYPOINT] Returning response: {len(result)} characters", flush=True)
        return result
        
    except Exception as e:
        print(f"[ENTRYPOINT] ERROR: {type(e).__name__}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        # Return error message instead of raising to avoid 500
        return f"I apologize, but I encountered an error: {str(e)}"


# Verify entrypoint is registered
print("[RUNTIME] Entrypoint registered successfully!", flush=True)
print(f"[RUNTIME] Memory ID: {MEMORY_ID}", flush=True)
print("[RUNTIME] Actor IDs: Dynamically created per session (flight-*, hotel-*, activities-*)", flush=True)
print("[RUNTIME] Ready to process requests!", flush=True)

# Run the AgentCore app
if __name__ == "__main__":
    print("[RUNTIME] Starting AgentCore app...", flush=True)
    app.run()
