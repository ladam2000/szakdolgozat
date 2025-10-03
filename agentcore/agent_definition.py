"""
Strands Agent definition for Bedrock AgentCore deployment.
This file defines the custom agent that will be hosted by AgentCore.
"""

from strands import Agent, tool
from typing import Dict, List
import json


@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for available flights between cities.
    
    Args:
        origin: Departure city
        destination: Arrival city
        date: Travel date (YYYY-MM-DD)
    """
    flights = [
        {"flight": "AA123", "price": 450, "departure": "08:00", "arrival": "11:30"},
        {"flight": "UA456", "price": 520, "departure": "14:00", "arrival": "17:30"},
    ]
    return json.dumps(flights)


@tool
def search_hotels(city: str, checkin: str, checkout: str) -> str:
    """Search for available hotels in a city.
    
    Args:
        city: City name
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
    """
    hotels = [
        {"name": "Grand Hotel", "price": 200, "rating": 4.5},
        {"name": "City Inn", "price": 150, "rating": 4.0},
    ]
    return json.dumps(hotels)


@tool
def search_activities(city: str, date: str) -> str:
    """Search for activities and attractions in a city.
    
    Args:
        city: City name
        date: Activity date (YYYY-MM-DD)
    """
    activities = [
        {"name": "City Tour", "price": 50, "duration": "3 hours"},
        {"name": "Museum Visit", "price": 25, "duration": "2 hours"},
    ]
    return json.dumps(activities)


def create_travel_agent():
    """Create the main travel planning agent."""
    return Agent(
        name="TravelAssistant",
        instructions="""You are a helpful travel planning assistant.
        
        Help users plan their trips by:
        1. Searching for flights using search_flights
        2. Finding hotels using search_hotels
        3. Recommending activities using search_activities
        
        Ask clarifying questions when needed and provide comprehensive travel plans.""",
        tools=[search_flights, search_hotels, search_activities],
    )


# Export agent for AgentCore
agent = create_travel_agent()
