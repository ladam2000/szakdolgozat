"""AgentCore runtime main entry point with orchestrator pattern and memory."""

import sys
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
import json

# Ensure prints are flushed immediately
sys.stdout.flush()
print("[STARTUP] Initializing orchestrator agent system...", flush=True)

# Memory configuration
MEMORY_ID = "memory_rllrl-lfg7zBH6MH"
ACTOR_ID = "travel_orchestrator"
BRANCH_NAME = "main"

# Create the AgentCore app
app = BedrockAgentCoreApp()

# Initialize memory client
print("[MEMORY] Initializing memory client...", flush=True)
memory_client = MemoryClient()
print(f"[MEMORY] Memory ID: {MEMORY_ID}", flush=True)


# Specialized Agent 1: Flight Booking Agent
def create_flight_agent() -> Agent:
    """Create specialized agent for flight bookings."""
    agent = Agent(
        name="FlightBookingAgent",
        model="eu.amazon.nova-micro-v1:0",
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
def create_hotel_agent() -> Agent:
    """Create specialized agent for hotel bookings."""
    agent = Agent(
        name="HotelBookingAgent",
        model="eu.amazon.nova-micro-v1:0",
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
def create_activities_agent() -> Agent:
    """Create specialized agent for activities and attractions."""
    agent = Agent(
        name="ActivitiesAgent",
        model="eu.amazon.nova-micro-v1:0",
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


# Create specialized agents
print("[AGENT] Creating specialized agents...", flush=True)
flight_agent = create_flight_agent()
hotel_agent = create_hotel_agent()
activities_agent = create_activities_agent()
print("[AGENT] Specialized agents created", flush=True)


# Convert agents to tools for the orchestrator
@tool
def flight_booking_tool(query: str) -> str:
    """Search and book flights.
    
    Args:
        query: Flight search request (origin, destination, dates, preferences)
    """
    try:
        print(f"[FLIGHT AGENT] Processing: {query}", flush=True)
        response = flight_agent(query)
        print(f"[FLIGHT AGENT] Response type: {type(response)}", flush=True)
        
        # Extract text from Strands response
        if hasattr(response, 'message') and 'content' in response.message:
            result = response.message['content'][0]['text']
        elif hasattr(response, 'content'):
            result = response.content
        elif isinstance(response, dict) and 'content' in response:
            result = response['content']
        else:
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
        response = hotel_agent(query)
        print(f"[HOTEL AGENT] Response type: {type(response)}", flush=True)
        
        # Extract text from Strands response
        if hasattr(response, 'message') and 'content' in response.message:
            result = response.message['content'][0]['text']
        elif hasattr(response, 'content'):
            result = response.content
        elif isinstance(response, dict) and 'content' in response:
            result = response['content']
        else:
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
        response = activities_agent(query)
        print(f"[ACTIVITIES AGENT] Response type: {type(response)}", flush=True)
        
        # Extract text from Strands response
        if hasattr(response, 'message') and 'content' in response.message:
            result = response.message['content'][0]['text']
        elif hasattr(response, 'content'):
            result = response.content
        elif isinstance(response, dict) and 'content' in response:
            result = response['content']
        else:
            result = str(response)
        
        print(f"[ACTIVITIES AGENT] Returning: {len(result)} characters", flush=True)
        return result
    except Exception as e:
        print(f"[ACTIVITIES AGENT] ERROR: {str(e)}", flush=True)
        return f"Error searching activities: {str(e)}"


# Create the orchestrator agent with specialized agents as tools
print("[AGENT] Creating travel orchestrator agent...", flush=True)

agent = Agent(
    name="TravelOrchestrator",
    model="eu.amazon.nova-micro-v1:0",
    tools=[flight_booking_tool, hotel_booking_tool, activities_tool],
)

agent.system_prompt = """You are a travel planning orchestrator that coordinates specialized agents.

IMPORTANT: This is a demonstration system. You coordinate agents that provide travel guidance and recommendations, but do NOT have access to real booking systems or live data.

Your role:
- Understand user travel needs and preferences
- Delegate to specialized agents: flight_booking_tool, hotel_booking_tool, activities_tool
- Synthesize responses from multiple agents into comprehensive travel guidance
- Ask clarifying questions when information is missing
- Always remind users to verify information and book through official channels

Available specialized agents:
1. flight_booking_tool - Provides flight search guidance and typical options
2. hotel_booking_tool - Provides hotel recommendations and what to look for
3. activities_tool - Suggests activities and attractions with general information

Workflow:
1. Gather essential information (origin, destination, dates, budget, preferences)
2. Call appropriate agent tools with detailed queries
3. Combine results into a cohesive travel planning guide
4. Provide recommendations and alternatives
5. Remind users to check official booking sites for current prices and availability

Always be helpful, provide realistic guidance, and make it clear this is advisory information, not actual bookings."""

print("[AGENT] Orchestrator agent created successfully!", flush=True)
print(f"[AGENT] Agent name: {agent.name}", flush=True)
print(f"[AGENT] Specialized agents: FlightBookingAgent, HotelBookingAgent, ActivitiesAgent", flush=True)
print(f"[AGENT] Tools: {[tool.__name__ for tool in [flight_booking_tool, hotel_booking_tool, activities_tool]]}", flush=True)


# Define the entrypoint for AgentCore
@app.entrypoint
def travel_orchestrator_entrypoint(payload):
    """
    AgentCore entrypoint for the travel orchestrator with memory support.
    
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
        
        # Retrieve conversation history from memory
        print("[MEMORY] Retrieving conversation history...", flush=True)
        context = ""
        try:
            print(f"[MEMORY] Calling get_last_k_turns with memory_id={MEMORY_ID}, actor_id={ACTOR_ID}, session_id={session_id}", flush=True)
            
            # Call with correct parameter names (snake_case)
            response = memory_client.get_last_k_turns(
                memory_id=MEMORY_ID,
                actor_id=ACTOR_ID,
                session_id=session_id,
                k=10,  # Get last 10 conversation turns
                branch_name=BRANCH_NAME
            )
            
            # Extract events from response
            events = response.get("events", [])
            print(f"[MEMORY] Retrieved {len(events)} conversation events", flush=True)
            
            # Format history for context
            if events and len(events) > 0:
                context = "\n\nPrevious conversation:\n"
                for event in events:
                    payload = event.get("payload", {})
                    messages = payload.get("messages", [])
                    for msg in messages:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        context += f"{role}: {content}\n"
                print(f"[MEMORY] Context length: {len(context)} characters", flush=True)
                print(f"[MEMORY] Context preview: {context[:200]}...", flush=True)
            else:
                print("[MEMORY] No previous conversation history found", flush=True)
        except Exception as e:
            error_msg = str(e)
            print(f"[MEMORY] ERROR retrieving history: {type(e).__name__}: {error_msg}", flush=True)
            if "ResourceNotFoundException" in str(type(e)) or "Memory not found" in error_msg:
                print(f"[MEMORY] Memory {MEMORY_ID} not found or not accessible", flush=True)
                print(f"[MEMORY] Please ensure:", flush=True)
                print(f"[MEMORY]   1. Memory exists: arn:aws:bedrock-agentcore:eu-central-1:206631439304:memory/{MEMORY_ID}", flush=True)
                print(f"[MEMORY]   2. AgentCore runtime has permission to access the memory", flush=True)
                print(f"[MEMORY]   3. Memory is associated with the AgentCore runtime", flush=True)
            import traceback
            traceback.print_exc()
            context = ""
        
        # Prepare input with context
        agent_input = user_input
        if context:
            agent_input = f"{context}\n\nCurrent request: {user_input}"
        
        # Invoke the orchestrator agent
        print("[ENTRYPOINT] Invoking orchestrator agent...", flush=True)
        response = agent(agent_input)
        print(f"[ENTRYPOINT] Agent response type: {type(response)}", flush=True)
        
        # Extract text from response
        if hasattr(response, 'message') and 'content' in response.message:
            print("[ENTRYPOINT] Extracting from response.message['content']", flush=True)
            result = response.message['content'][0]['text']
        elif hasattr(response, 'content'):
            print("[ENTRYPOINT] Extracting from response.content", flush=True)
            result = response.content
        elif isinstance(response, dict) and 'content' in response:
            print("[ENTRYPOINT] Extracting from response['content']", flush=True)
            result = response['content']
        else:
            print("[ENTRYPOINT] Converting response to string", flush=True)
            result = str(response)
        
        # Store conversation in memory
        print("[MEMORY] Storing conversation in memory...", flush=True)
        try:
            from datetime import datetime
            import uuid
            
            print(f"[MEMORY] Calling create_event with memory_id={MEMORY_ID}, actor_id={ACTOR_ID}, session_id={session_id}", flush=True)
            print(f"[MEMORY] User message length: {len(user_input)}, Assistant message length: {len(result)}", flush=True)
            
            # Call create_event with correct parameter names (snake_case)
            response = memory_client.create_event(
                memory_id=MEMORY_ID,
                actor_id=ACTOR_ID,
                session_id=session_id,
                messages=[
                    (user_input, "user"),
                    (result, "assistant")
                ]
            )
            
            event_id = response.get("event", {}).get("eventId", "unknown")
            print(f"[MEMORY] Conversation stored successfully with event ID: {event_id}", flush=True)
        except Exception as e:
            error_msg = str(e)
            print(f"[MEMORY] ERROR storing conversation: {type(e).__name__}: {error_msg}", flush=True)
            if "ResourceNotFoundException" in str(type(e)) or "Memory not found" in error_msg:
                print(f"[MEMORY] Memory {MEMORY_ID} not found or not accessible", flush=True)
                print(f"[MEMORY] Continuing without memory storage...", flush=True)
            import traceback
            traceback.print_exc()
        
        print(f"[ENTRYPOINT] Returning response: {len(result)} characters", flush=True)
        return result
        
    except Exception as e:
        print(f"[ENTRYPOINT] ERROR: {type(e).__name__}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        # Return error message instead of raising to avoid 500
        return f"I apologize, but I encountered an error: {str(e)}"


# Test the entrypoint to verify it's registered and working
print("[RUNTIME] Testing entrypoint registration...", flush=True)
try:
    print(f"[RUNTIME] Entrypoint function: {travel_orchestrator_entrypoint}", flush=True)
    print("[RUNTIME] Entrypoint registered successfully!", flush=True)
    
    # Try a test call to verify it works
    print("[RUNTIME] Running test invocation...", flush=True)
    test_result = travel_orchestrator_entrypoint({"input": "test", "session_id": "test_startup"})
    print(f"[RUNTIME] Test invocation successful! Response length: {len(test_result)}", flush=True)
except Exception as e:
    print(f"[RUNTIME] ERROR during test: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()

# Run the AgentCore app
if __name__ == "__main__":
    print("[RUNTIME] Starting AgentCore app...", flush=True)
    app.run()
