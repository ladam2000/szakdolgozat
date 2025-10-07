# Deployment Guide - Orchestrator Pattern Update

## What Changed

The travel agent system has been updated to use the **agents-as-tools** pattern:

### Before:
- Single agent with 3 tool functions (`search_flights`, `search_hotels`, `search_activities`)
- Tools returned mock JSON data directly

### After:
- **Orchestrator Agent** (Claude Sonnet) coordinates the workflow
- **3 Specialized Agents** (Nova Micro) act as tools:
  - `FlightBookingAgent` - Handles flight searches
  - `HotelBookingAgent` - Handles hotel searches
  - `ActivitiesAgent` - Handles activities and itineraries
- Each specialized agent is a full Strands Agent with its own system prompt

## Files Updated

1. `agentcore/agents.py` - Main implementation with orchestrator pattern
2. `agentcore/agent.py` - Standalone version (for reference)
3. `agentcore/app.py` - Updated to handle new response format
4. `README.md` - Updated architecture documentation

## How to Deploy

### Option 1: Rebuild Container (Recommended)
```bash
# Rebuild the AgentCore container
docker build -t travel-agent-agentcore ./agentcore

# Or trigger CodeBuild if using AWS
aws codebuild start-build --project-name travel-assistant-build
```

### Option 2: Hot Reload (if supported)
If your AgentCore service supports hot reload, simply restart the service:
```bash
# Restart the service to pick up new code
systemctl restart agentcore
# or
docker restart agentcore-container
```

## Testing the New System

### Test Query 1: Simple Travel Request
```json
{
  "message": "I want to travel from New York to Paris next week",
  "session_id": "test-123"
}
```

Expected behavior:
- Orchestrator asks for specific dates
- May call flight_booking_tool to show options

### Test Query 2: Complete Travel Plan
```json
{
  "message": "Plan a 3-day trip to Tokyo from San Francisco, departing March 15th",
  "session_id": "test-123"
}
```

Expected behavior:
- Orchestrator calls `flight_booking_tool` for flights
- Orchestrator calls `hotel_booking_tool` for hotels
- Orchestrator calls `activities_tool` for things to do
- Returns comprehensive travel plan

### Test Query 3: Specific Request
```json
{
  "message": "Find me hotels in London for March 20-23",
  "session_id": "test-123"
}
```

Expected behavior:
- Orchestrator calls only `hotel_booking_tool`
- Returns hotel recommendations

## Logs to Watch For

After deployment, you should see:
```
[AGENT] Creating travel orchestrator agent...
[AGENT] Orchestrator agent created successfully with 3 specialized agents as tools
```

When processing requests:
```
[CHAT] Invoking coordinator agent...
[FLIGHT AGENT] Processing: <query>
[HOTEL AGENT] Processing: <query>
[ACTIVITIES AGENT] Processing: <query>
```

## Troubleshooting

### Issue: Still seeing old agent logs
**Solution**: Container is running old code. Rebuild and redeploy.

### Issue: Agent not responding
**Solution**: Check that Claude Sonnet model is available in your region:
```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude-sonnet')]"
```

### Issue: Tool calls failing
**Solution**: Check that Nova Micro is available for specialized agents:
```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'nova-micro')]"
```

## Architecture Benefits

1. **Separation of Concerns**: Each agent specializes in one domain
2. **Scalability**: Easy to add new specialized agents
3. **Flexibility**: Orchestrator intelligently decides which agents to call
4. **Cost Optimization**: Use cheaper models (Nova Micro) for specialized tasks
5. **Better Responses**: Specialized agents provide more detailed, contextual responses
