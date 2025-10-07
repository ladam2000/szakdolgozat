# Orchestrator Pattern Implementation

## Overview

This travel agent system implements the **agents-as-tools** pattern from Strands Agents, where specialized agents are exposed as tool calls to an orchestrator agent.

## Architecture

```
User Query
    ↓
TravelOrchestrator (Claude Sonnet)
    ↓
    ├─→ flight_booking_tool → FlightBookingAgent (Nova Micro)
    ├─→ hotel_booking_tool → HotelBookingAgent (Nova Micro)
    └─→ activities_tool → ActivitiesAgent (Nova Micro)
    ↓
Synthesized Response
```

## Components

### 1. Orchestrator Agent
- **Name**: TravelOrchestrator
- **Model**: Claude Sonnet 4 (us.anthropic.claude-sonnet-4-20250514-v1:0)
- **Role**: Coordinates travel planning, decides which specialists to call
- **Tools**: 3 specialized agents exposed as tool functions

### 2. Specialized Agents

#### FlightBookingAgent
- **Model**: Nova Micro (us.amazon.nova-micro-v1:0)
- **Expertise**: Flight searches, pricing, schedules, multi-city itineraries
- **Output**: JSON with flight options and recommendations

#### HotelBookingAgent
- **Model**: Nova Micro (us.amazon.nova-micro-v1:0)
- **Expertise**: Hotel searches, pricing, ratings, amenities
- **Output**: JSON with hotel options and recommendations

#### ActivitiesAgent
- **Model**: Nova Micro (us.amazon.nova-micro-v1:0)
- **Expertise**: Activities, attractions, tours, itineraries
- **Output**: JSON with activity options and recommendations

## How It Works

### Example Flow

**User**: "Plan a 3-day trip to Paris from New York, leaving March 15th"

1. **Orchestrator receives query**
   - Analyzes: Need flights, hotels, and activities
   - Identifies: Origin (NYC), Destination (Paris), Duration (3 days), Date (March 15)

2. **Orchestrator calls flight_booking_tool**
   ```python
   flight_booking_tool("Find flights from New York to Paris departing March 15th")
   ```
   - FlightBookingAgent processes request
   - Returns flight options with prices and times

3. **Orchestrator calls hotel_booking_tool**
   ```python
   hotel_booking_tool("Find hotels in Paris for 3 nights starting March 15th")
   ```
   - HotelBookingAgent processes request
   - Returns hotel options with ratings and amenities

4. **Orchestrator calls activities_tool**
   ```python
   activities_tool("Suggest activities in Paris for 3 days")
   ```
   - ActivitiesAgent processes request
   - Returns activity recommendations with timing

5. **Orchestrator synthesizes response**
   - Combines all information
   - Creates comprehensive travel plan
   - Provides recommendations and alternatives

## Benefits

### 1. Separation of Concerns
Each agent focuses on one domain, making them experts in their area.

### 2. Scalability
Easy to add new specialized agents (e.g., car rentals, restaurants, weather).

### 3. Cost Optimization
- Orchestrator uses powerful model (Claude Sonnet) for coordination
- Specialists use cheaper model (Nova Micro) for specific tasks

### 4. Flexibility
Orchestrator intelligently decides which agents to call based on user needs.

### 5. Better Responses
Specialized agents provide more detailed, contextual information than generic tools.

## Code Structure

### runtime_agent_main.py (AgentCore Entry Point)
```python
from strands import Agent, tool

# Create specialized agents
flight_agent = create_flight_agent()
hotel_agent = create_hotel_agent()
activities_agent = create_activities_agent()

# Wrap agents as tools (MUST use @tool decorator)
@tool
def flight_booking_tool(query: str) -> str:
    response = flight_agent(query)
    return response.content

# Create orchestrator with agents as tools
agent = Agent(
    name="TravelOrchestrator",
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[flight_booking_tool, hotel_booking_tool, activities_tool],
)
```

**Important**: Tool functions MUST be decorated with `@tool` from Strands, otherwise you'll get "unrecognized tool specification" errors.

### Key Pattern
1. Create specialized Agent instances
2. Wrap each agent in a tool function
3. Pass tool functions to orchestrator's `tools` parameter
4. Orchestrator calls tools, which internally invoke agents

## Extending the System

### Adding a New Specialized Agent

1. **Create the agent**:
```python
def create_car_rental_agent() -> Agent:
    agent = Agent(
        name="CarRentalAgent",
        model="us.amazon.nova-micro-v1:0",
    )
    agent.system_prompt = """You are a car rental specialist..."""
    return agent
```

2. **Wrap as a tool** (with @tool decorator):
```python
car_rental_agent = create_car_rental_agent()

@tool
def car_rental_tool(query: str) -> str:
    """Search for car rentals."""
    response = car_rental_agent(query)
    return response.content
```

3. **Add to orchestrator**:
```python
agent = Agent(
    name="TravelOrchestrator",
    tools=[
        flight_booking_tool,
        hotel_booking_tool,
        activities_tool,
        car_rental_tool,  # New tool
    ],
)
```

4. **Update orchestrator prompt**:
```python
agent.system_prompt = """...
Available specialized agents:
1. flight_booking_tool - For flight searches
2. hotel_booking_tool - For hotel searches
3. activities_tool - For activities
4. car_rental_tool - For car rentals  # New
..."""
```

## Model Selection

### Orchestrator Model Options
- **Claude Sonnet 4**: Best reasoning, highest cost
- **Claude Haiku**: Fast, good reasoning, lower cost
- **Nova Pro**: AWS native, balanced performance

### Specialist Model Options
- **Nova Micro**: Cheapest, fast, good for structured tasks
- **Nova Lite**: More capable than Micro, still affordable
- **Claude Haiku**: Best for complex specialist tasks

## Performance Considerations

### Latency
- Sequential tool calls: ~2-5 seconds per agent
- Parallel tool calls: Strands may optimize automatically
- Total: 5-15 seconds for complete travel plan

### Cost
- Orchestrator: ~$0.003 per request (Claude Sonnet)
- Each specialist: ~$0.0001 per call (Nova Micro)
- Total: ~$0.0033 per complete travel plan

### Optimization Tips
1. Use Nova Micro for specialists (10x cheaper than Claude)
2. Cache agent instances (don't recreate on each request)
3. Use specific queries to specialists (avoid unnecessary calls)
4. Consider parallel tool execution for independent tasks

## References

- [Strands Agents as Tools Documentation](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agents-as-tools/)
- [AWS Bedrock Models](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
- [AgentCore Runtime Contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-service-contract.html)
