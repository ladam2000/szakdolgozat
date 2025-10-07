# AWS AgentCore Pattern Comparison

## Reference
Based on: [AWS Bedrock AgentCore Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/01-AgentCore-runtime/01-hosting-agent/01-strands-with-bedrock-model/runtime_with_strands_and_bedrock_models.ipynb)

## Key Differences Between Our Old Code and AWS Pattern

### 1. App Initialization

**AWS Pattern (Correct):**
```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
```

**Our Old Code (Incorrect):**
```python
# No app initialization - just created agent directly
```

### 2. Entrypoint Definition

**AWS Pattern (Correct):**
```python
@app.entrypoint
def strands_agent_bedrock(payload):
    """Invoke the agent with a payload"""
    user_input = payload.get("prompt")
    print("User input:", user_input)
    response = agent(user_input)
    return response.message['content'][0]['text']
```

**Our Old Code (Incorrect):**
```python
# No entrypoint decorator - agent was just exported as module variable
agent = Agent(...)
```

### 3. Response Extraction

**AWS Pattern (Correct):**
```python
response = agent(user_input)
return response.message['content'][0]['text']
```

**Our Old Code (Incorrect):**
```python
response = agent(query)
return response.get("content", "") if isinstance(response, dict) else str(response)
```

### 4. Runtime Execution

**AWS Pattern (Correct):**
```python
if __name__ == "__main__":
    app.run()
```

**Our Old Code (Incorrect):**
```python
if __name__ == "__main__":
    while True:
        time.sleep(60)
        print("[RUNTIME] Still alive...")
```

### 5. Dependencies

**AWS Pattern (Correct):**
```
strands-agents
bedrock-agentcore
```

**Our Old Code (Missing):**
```
strands-agents
# bedrock-agentcore was missing!
```

## Our Updated Implementation

Now following the AWS pattern:

```python
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Initialize app
app = BedrockAgentCoreApp()

# Create specialized agents
flight_agent = create_flight_agent()
hotel_agent = create_hotel_agent()
activities_agent = create_activities_agent()

# Create tools with @tool decorator
@tool
def flight_booking_tool(query: str) -> str:
    """Search and book flights."""
    response = flight_agent(query)
    if hasattr(response, 'message') and 'content' in response.message:
        return response.message['content'][0]['text']
    return str(response)

# Create orchestrator agent
agent = Agent(
    name="TravelOrchestrator",
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[flight_booking_tool, hotel_booking_tool, activities_tool],
)

# Define entrypoint
@app.entrypoint
def travel_orchestrator_entrypoint(payload):
    """AgentCore entrypoint for the travel orchestrator."""
    user_input = payload.get("input") or payload.get("prompt", "")
    print(f"User input: {user_input}")
    
    response = agent(user_input)
    
    # Extract text following AWS pattern
    if hasattr(response, 'message') and 'content' in response.message:
        return response.message['content'][0]['text']
    return str(response)

# Run the app
if __name__ == "__main__":
    app.run()
```

## Why These Changes Matter

### 1. BedrockAgentCoreApp
- Provides proper integration with AgentCore runtime
- Handles health checks automatically
- Manages request/response lifecycle
- Provides proper error handling

### 2. @app.entrypoint Decorator
- Registers the function as the AgentCore invocation handler
- Ensures proper payload handling
- Enables AgentCore to find and invoke the agent
- Required for AgentCore runtime contract

### 3. Correct Response Extraction
- Strands returns structured response objects
- `response.message['content'][0]['text']` is the standard way to extract text
- Ensures compatibility with Strands response format

### 4. app.run() Instead of While Loop
- `app.run()` starts the AgentCore server properly
- Handles HTTP requests from AgentCore
- Manages graceful shutdown
- While loop was just keeping process alive, not serving requests

## Testing the Updated Code

### Payload Format
AgentCore sends payloads like:
```json
{
  "input": "Plan a trip to Paris",
  "prompt": "Plan a trip to Paris"  // Alternative key
}
```

Our entrypoint handles both:
```python
user_input = payload.get("input") or payload.get("prompt", "")
```

### Expected Flow
1. AgentCore sends HTTP request with payload
2. `BedrockAgentCoreApp` receives request
3. Calls `@app.entrypoint` decorated function
4. Function extracts user input from payload
5. Invokes orchestrator agent
6. Orchestrator calls specialized agent tools
7. Response extracted and returned
8. AgentCore receives response

## Benefits of Following AWS Pattern

1. ✅ **Proper Health Checks** - AgentCore can verify runtime is ready
2. ✅ **Standard Integration** - Works with AgentCore's expected contract
3. ✅ **Better Error Handling** - App framework handles errors gracefully
4. ✅ **Correct Response Format** - Extracts text properly from Strands responses
5. ✅ **Production Ready** - Follows AWS best practices
6. ✅ **Maintainable** - Consistent with AWS documentation and examples

## References

- [AWS AgentCore Samples Repository](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
- [AgentCore Runtime Service Contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-service-contract.html)
- [Strands Agents Documentation](https://strandsagents.com/)
