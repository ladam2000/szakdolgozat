"""AgentCore runtime main entry point."""

import sys
from strands import Agent, tool
import json

# Ensure prints are flushed immediately
sys.stdout.flush()
print("[STARTUP] Initializing agent...", flush=True)


@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for available flights.
    
    Args:
        origin: Departure city
        destination: Arrival city  
        date: Travel date (YYYY-MM-DD)
    """
    print(f"[TOOL] Searching flights: {origin} -> {destination} on {date}")
    flights = [
        {"flight": "AA123", "price": 450, "departure": "08:00", "arrival": "11:30"},
        {"flight": "UA456", "price": 520, "departure": "14:00", "arrival": "17:30"},
    ]
    return json.dumps(flights)


@tool
def search_hotels(city: str, checkin: str, checkout: str) -> str:
    """Search for hotels.
    
    Args:
        city: City name
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
    """
    print(f"[TOOL] Searching hotels in {city}: {checkin} to {checkout}")
    hotels = [
        {"name": "Grand Hotel", "price": 200, "rating": 4.5},
        {"name": "City Inn", "price": 150, "rating": 4.0},
    ]
    return json.dumps(hotels)


@tool
def search_activities(city: str, date: str) -> str:
    """Search for activities.
    
    Args:
        city: City name
        date: Activity date (YYYY-MM-DD)
    """
    print(f"[TOOL] Searching activities in {city} on {date}")
    activities = [
        {"name": "City Tour", "price": 50, "duration": "3 hours"},
        {"name": "Museum Visit", "price": 25, "duration": "2 hours"},
    ]
    return json.dumps(activities)


# Create and export the agent
print("[AGENT] Creating travel coordinator agent...", flush=True)

agent = Agent(
    name="TravelCoordinator",
    tools=[search_flights, search_hotels, search_activities],
)

print("[AGENT] Setting system prompt...", flush=True)

agent.system_prompt = """You are a helpful travel planning assistant.

Help users plan their trips by:
- Searching for flights using search_flights
- Finding hotels using search_hotels
- Recommending activities using search_activities

Ask clarifying questions when needed (origin, destination, dates, etc).
Provide comprehensive travel plans with all the information."""

print("[AGENT] Agent created and ready!", flush=True)
print(f"[AGENT] Agent name: {agent.name}", flush=True)
print(f"[AGENT] Tools: {[tool.__name__ for tool in [search_flights, search_hotels, search_activities]]}", flush=True)

# Keep the process running so AgentCore can invoke the agent
if __name__ == "__main__":
    import time
    print("[RUNTIME] Agent ready and waiting for invocations...", flush=True)
    print("[RUNTIME] Container will stay alive for AgentCore to invoke", flush=True)
    while True:
        time.sleep(60)
        print("[RUNTIME] Still alive...", flush=True)
