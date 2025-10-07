"""Travel agent system with orchestrator and specialized agents as tools."""

from strands import Agent, tool
import json


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


# Create specialized agents (singleton instances)
_flight_agent = None
_hotel_agent = None
_activities_agent = None


def get_flight_agent():
    """Get or create flight agent singleton."""
    global _flight_agent
    if _flight_agent is None:
        _flight_agent = create_flight_agent()
    return _flight_agent


def get_hotel_agent():
    """Get or create hotel agent singleton."""
    global _hotel_agent
    if _hotel_agent is None:
        _hotel_agent = create_hotel_agent()
    return _hotel_agent


def get_activities_agent():
    """Get or create activities agent singleton."""
    global _activities_agent
    if _activities_agent is None:
        _activities_agent = create_activities_agent()
    return _activities_agent


# Convert agents to tools for the orchestrator
@tool
def flight_booking_tool(query: str) -> str:
    """Search and book flights.
    
    Args:
        query: Flight search request (origin, destination, dates, preferences)
    """
    print(f"[FLIGHT AGENT] Processing: {query}")
    agent = get_flight_agent()
    response = agent(query)
    return response.get("content", "") if isinstance(response, dict) else str(response)


@tool
def hotel_booking_tool(query: str) -> str:
    """Search and book hotels.
    
    Args:
        query: Hotel search request (city, dates, preferences, budget)
    """
    print(f"[HOTEL AGENT] Processing: {query}")
    agent = get_hotel_agent()
    response = agent(query)
    return response.get("content", "") if isinstance(response, dict) else str(response)


@tool
def activities_tool(query: str) -> str:
    """Find activities and attractions.
    
    Args:
        query: Activities request (city, dates, interests, preferences)
    """
    print(f"[ACTIVITIES AGENT] Processing: {query}")
    agent = get_activities_agent()
    response = agent(query)
    return response.get("content", "") if isinstance(response, dict) else str(response)


def create_coordinator_agent() -> Agent:
    """Create travel orchestrator agent with specialized agents as tools."""
    print("[AGENT] Creating travel orchestrator agent...")
    
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
    
    print("[AGENT] Orchestrator agent created successfully with 3 specialized agents as tools")
    return agent
