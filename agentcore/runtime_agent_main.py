"""AgentCore runtime main entry point with orchestrator pattern."""

import sys
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
import json

# Ensure prints are flushed immediately
sys.stdout.flush()
print("[STARTUP] Initializing orchestrator agent system...", flush=True)

# Create the AgentCore app
app = BedrockAgentCoreApp()


# Specialized Agent 1: Flight Booking Agent
def create_flight_agent() -> Agent:
    """Create specialized agent for flight bookings."""
    agent = Agent(
        name="FlightBookingAgent",
        model="us.amazon.nova-micro-v1:0",
    )
    
    agent.system_prompt = """You are a flight booking specialist.

Your expertise:
- Search and compare flights between cities
- Find best prices and schedules
- Provide flight recommendations based on preferences
- Handle multi-city itineraries

When responding:
- Always return flight options in JSON format
- Include flight number, price, departure/arrival times
- Consider user preferences (budget, time, airline)
- Suggest alternatives when direct flights aren't available

Example response format:
{
    "flights": [
        {"flight": "AA123", "price": 450, "departure": "08:00", "arrival": "11:30", "airline": "American Airlines"},
        {"flight": "UA456", "price": 520, "departure": "14:00", "arrival": "17:30", "airline": "United"}
    ],
    "recommendation": "AA123 offers the best value for morning departure"
}"""
    
    return agent


# Specialized Agent 2: Hotel Booking Agent
def create_hotel_agent() -> Agent:
    """Create specialized agent for hotel bookings."""
    agent = Agent(
        name="HotelBookingAgent",
        model="us.amazon.nova-micro-v1:0",
    )
    
    agent.system_prompt = """You are a hotel booking specialist.

Your expertise:
- Search hotels in any city
- Compare prices, ratings, and amenities
- Recommend hotels based on budget and preferences
- Provide location insights

When responding:
- Always return hotel options in JSON format
- Include name, price per night, rating, amenities
- Consider proximity to attractions and transportation
- Suggest alternatives for different budgets

Example response format:
{
    "hotels": [
        {"name": "Grand Hotel", "price": 200, "rating": 4.5, "amenities": ["pool", "gym", "wifi"]},
        {"name": "City Inn", "price": 150, "rating": 4.0, "amenities": ["wifi", "breakfast"]}
    ],
    "recommendation": "Grand Hotel for luxury, City Inn for budget-conscious travelers"
}"""
    
    return agent


# Specialized Agent 3: Activities Agent
def create_activities_agent() -> Agent:
    """Create specialized agent for activities and attractions."""
    agent = Agent(
        name="ActivitiesAgent",
        model="us.amazon.nova-micro-v1:0",
    )
    
    agent.system_prompt = """You are a local activities and attractions specialist.

Your expertise:
- Recommend activities and attractions in any city
- Suggest tours, museums, restaurants, entertainment
- Provide timing and pricing information
- Create day-by-day itineraries

When responding:
- Always return activities in JSON format
- Include name, price, duration, description
- Consider user interests and travel style
- Suggest activities for different times of day

Example response format:
{
    "activities": [
        {"name": "City Tour", "price": 50, "duration": "3 hours", "type": "sightseeing"},
        {"name": "Museum Visit", "price": 25, "duration": "2 hours", "type": "culture"}
    ],
    "recommendation": "Start with City Tour in morning, Museum Visit in afternoon"
}"""
    
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
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[flight_booking_tool, hotel_booking_tool, activities_tool],
)

agent.system_prompt = """You are a travel planning orchestrator that coordinates specialized agents.

Your role:
- Understand user travel needs and preferences
- Delegate to specialized agents: flight_booking_tool, hotel_booking_tool, activities_tool
- Synthesize responses from multiple agents into comprehensive travel plans
- Ask clarifying questions when information is missing

Available specialized agents:
1. flight_booking_tool - For flight searches and bookings
2. hotel_booking_tool - For hotel searches and bookings  
3. activities_tool - For activities, attractions, and itineraries

Workflow:
1. Gather essential information (origin, destination, dates, budget, preferences)
2. Call appropriate agent tools with detailed queries
3. Combine results into a cohesive travel plan
4. Provide recommendations and alternatives

Always be helpful, ask for missing details, and create complete travel plans."""

print("[AGENT] Orchestrator agent created successfully!", flush=True)
print(f"[AGENT] Agent name: {agent.name}", flush=True)
print(f"[AGENT] Specialized agents: FlightBookingAgent, HotelBookingAgent, ActivitiesAgent", flush=True)
print(f"[AGENT] Tools: {[tool.__name__ for tool in [flight_booking_tool, hotel_booking_tool, activities_tool]]}", flush=True)


# Define the entrypoint for AgentCore
@app.entrypoint
def travel_orchestrator_entrypoint(payload):
    """
    AgentCore entrypoint for the travel orchestrator.
    
    Args:
        payload: Dictionary with user input (expects 'input' or 'prompt' key)
    
    Returns:
        String response from the orchestrator agent
    """
    try:
        print(f"[ENTRYPOINT] Received payload: {payload}", flush=True)
        
        # Extract user input from payload
        user_input = payload.get("input") or payload.get("prompt", "")
        
        if not user_input:
            print("[ENTRYPOINT] WARNING: No input found in payload", flush=True)
            return "Please provide a travel request in the 'input' or 'prompt' field."
        
        print(f"[ENTRYPOINT] User input: {user_input}", flush=True)
        
        # Invoke the orchestrator agent
        print("[ENTRYPOINT] Invoking orchestrator agent...", flush=True)
        response = agent(user_input)
        print(f"[ENTRYPOINT] Agent response type: {type(response)}", flush=True)
        print(f"[ENTRYPOINT] Agent response: {response}", flush=True)
        
        # Extract text from response following AWS example pattern
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
        
        print(f"[ENTRYPOINT] Returning response: {len(result)} characters", flush=True)
        return result
        
    except Exception as e:
        print(f"[ENTRYPOINT] ERROR: {type(e).__name__}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        # Return error message instead of raising to avoid 500
        return f"I apologize, but I encountered an error: {str(e)}"


# Run the AgentCore app
if __name__ == "__main__":
    print("[RUNTIME] Starting AgentCore app...", flush=True)
    app.run()
