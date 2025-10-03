"""Multi-agent travel planning system with specialized agents."""

from strands import Agent, tool
from typing import Dict, List, Any
import json


@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for available flights between cities.
    
    Args:
        origin: Departure city
        destination: Arrival city
        date: Travel date (YYYY-MM-DD)
    """
    # Mock flight search
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
    # Mock hotel search
    hotels = [
        {"name": "Grand Hotel", "price": 200, "rating": 4.5, "amenities": ["pool", "wifi"]},
        {"name": "City Inn", "price": 150, "rating": 4.0, "amenities": ["wifi", "breakfast"]},
    ]
    return json.dumps(hotels)


@tool
def search_activities(city: str, date: str) -> str:
    """Search for activities and attractions in a city.
    
    Args:
        city: City name
        date: Activity date (YYYY-MM-DD)
    """
    # Mock activity search
    activities = [
        {"name": "City Tour", "price": 50, "duration": "3 hours", "type": "sightseeing"},
        {"name": "Museum Visit", "price": 25, "duration": "2 hours", "type": "culture"},
    ]
    return json.dumps(activities)


def create_flight_agent(model_client) -> Agent:
    """Create specialized flight booking agent."""
    return Agent(
        name="FlightAgent",
        instructions="""You are a flight booking specialist. Help users find and book flights.
        Use the search_flights tool to find available flights.
        Provide clear information about flight options, prices, and times.
        Ask for origin, destination, and travel dates if not provided.""",
        tools=[search_flights],
        model=model_client,
    )


def create_hotel_agent(model_client) -> Agent:
    """Create specialized hotel booking agent."""
    return Agent(
        name="HotelAgent",
        instructions="""You are a hotel booking specialist. Help users find and book accommodations.
        Use the search_hotels tool to find available hotels.
        Provide information about hotel amenities, prices, and ratings.
        Ask for city, check-in, and check-out dates if not provided.""",
        tools=[search_hotels],
        model=model_client,
    )


def create_activity_agent(model_client) -> Agent:
    """Create specialized activity planning agent."""
    return Agent(
        name="ActivityAgent",
        instructions="""You are an activity and attractions specialist. Help users plan activities.
        Use the search_activities tool to find things to do.
        Suggest activities based on user interests and travel dates.
        Ask for city and dates if not provided.""",
        tools=[search_activities],
        model=model_client,
    )


def create_coordinator_agent(model_client, sub_agents: List[Agent]) -> Agent:
    """Create coordinator agent that delegates to specialized agents."""
    
    @tool
    def delegate_to_flight_agent(query: str) -> str:
        """Delegate flight-related queries to the flight specialist.
        
        Args:
            query: The flight-related question or request
        """
        response = sub_agents[0].run(query)
        return response.content
    
    @tool
    def delegate_to_hotel_agent(query: str) -> str:
        """Delegate hotel-related queries to the hotel specialist.
        
        Args:
            query: The hotel-related question or request
        """
        response = sub_agents[1].run(query)
        return response.content
    
    @tool
    def delegate_to_activity_agent(query: str) -> str:
        """Delegate activity-related queries to the activity specialist.
        
        Args:
            query: The activity-related question or request
        """
        response = sub_agents[2].run(query)
        return response.content
    
    return Agent(
        name="TravelCoordinator",
        instructions="""You are a travel planning coordinator. Help users plan complete trips.
        
        Delegate tasks to specialized agents:
        - Use delegate_to_flight_agent for flight bookings
        - Use delegate_to_hotel_agent for hotel accommodations
        - Use delegate_to_activity_agent for activities and attractions
        
        Coordinate between agents to create comprehensive travel plans.
        Be friendly and helpful. Ask clarifying questions when needed.""",
        tools=[delegate_to_flight_agent, delegate_to_hotel_agent, delegate_to_activity_agent],
        model=model_client,
    )
