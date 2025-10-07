# Deployment Guide - Orchestrator Pattern Update

## What Changed

The travel agent system has been updated to use the **agents-as-tools** pattern following AWS best practices:

### Before:
- Single agent with 3 tool functions (`search_flights`, `search_hotels`, `search_activities`)
- Tools returned mock JSON data directly
- No proper AgentCore integration

### After:
- **Orchestrator Agent** (Claude Sonnet) coordinates the workflow
- **3 Specialized Agents** (Nova Micro) act as tools:
  - `FlightBookingAgent` - Handles flight searches
  - `HotelBookingAgent` - Handles hotel searches
  - `ActivitiesAgent` - Handles activities and itineraries
- Each specialized agent is a full Strands Agent with its own system prompt
- **Proper AgentCore integration** using `BedrockAgentCoreApp` and `@app.entrypoint`
- Follows [AWS AgentCore samples pattern](https://github.com/awslabs/amazon-bedrock-agentcore-samples)

## Files Updated

1. **`agentcore/runtime_agent_main.py`** ⭐ - AgentCore runtime entry point (CRITICAL)
   - Implements `BedrockAgentCoreApp` pattern
   - Uses `@app.entrypoint` decorator
   - Proper response extraction with `response.message['content'][0]['text']`
   - Follows AWS official example pattern
2. **`agentcore/requirements.txt`** - Added `bedrock-agentcore` dependency
3. `agentcore/agents.py` - Main implementation with orchestrator pattern
4. `agentcore/agent.py` - Standalone version (for reference)
5. `agentcore/app.py` - Updated to handle new response format (if using FastAPI)
6. `README.md` - Updated architecture documentation
7. `AWS_PATTERN_COMPARISON.md` - Detailed comparison with AWS example

**Note**: AgentCore uses `runtime_agent_main.py` as the entry point, not `app.py`.

## Local Testing (Optional but Recommended)

Before deploying, test the orchestrator locally:

```bash
# Install dependencies
pip install strands-agent boto3

# Run test script
python test_orchestrator.py
```

This will verify:
- Agent creation works
- Specialized agents are properly configured
- Tool calls execute correctly
- Models are accessible

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
[STARTUP] Initializing orchestrator agent system...
[AGENT] Creating specialized agents...
[AGENT] Specialized agents created
[AGENT] Creating travel orchestrator agent...
[AGENT] Orchestrator agent created successfully!
[AGENT] Agent name: TravelOrchestrator
[AGENT] Specialized agents: FlightBookingAgent, HotelBookingAgent, ActivitiesAgent
[AGENT] Tools: ['flight_booking_tool', 'hotel_booking_tool', 'activities_tool']
[RUNTIME] Agent ready and waiting for invocations...
```

When processing requests:
```
[FLIGHT AGENT] Processing: <query>
[HOTEL AGENT] Processing: <query>
[ACTIVITIES AGENT] Processing: <query>
```

## Troubleshooting

### Issue: Runtime health check failed or timed out
**Cause**: AgentCore couldn't load the agent properly.

**Solutions**:
1. Check that `runtime_agent_main.py` exports an `agent` variable at module level
2. Verify all required models are available in your region
3. Check CloudWatch logs for initialization errors
4. Ensure the container has proper IAM permissions for Bedrock

### Issue: Still seeing old agent logs
**Solution**: Container is running old code. Rebuild and redeploy:
```bash
# Force rebuild without cache
docker build --no-cache -t travel-agent-agentcore ./agentcore
```

### Issue: Agent not responding
**Solution**: Check that Claude Sonnet model is available in your region:
```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude-sonnet')]"
```

If not available, change the orchestrator model in `runtime_agent_main.py`:
```python
# Option 1: Use Claude Haiku (cheaper, faster)
model="us.anthropic.claude-3-5-haiku-20241022-v1:0"

# Option 2: Use Nova Pro (AWS native)
model="us.amazon.nova-pro-v1:0"
```

### Issue: Tool calls failing
**Solution**: Check that Nova Micro is available for specialized agents:
```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'nova-micro')]"
```

### Issue: Import errors
**Solution**: Verify Strands is installed in the container:
```bash
docker exec -it <container-id> pip list | grep strands
```

### Issue: "unrecognized tool specification" error
**Cause**: Tool functions are not decorated with `@tool`.

**Solution**: Ensure all tool functions have the `@tool` decorator:
```python
from strands import Agent, tool

@tool  # This is required!
def flight_booking_tool(query: str) -> str:
    """Search and book flights."""
    response = flight_agent(query)
    return response.content
```

Without `@tool`, Strands cannot recognize the function as a valid tool.

## Architecture Benefits

1. **Separation of Concerns**: Each agent specializes in one domain
2. **Scalability**: Easy to add new specialized agents
3. **Flexibility**: Orchestrator intelligently decides which agents to call
4. **Cost Optimization**: Use cheaper models (Nova Micro) for specialized tasks
5. **Better Responses**: Specialized agents provide more detailed, contextual responses
