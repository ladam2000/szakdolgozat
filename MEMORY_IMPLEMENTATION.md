# AgentCore Memory Implementation - AWS Pattern

## Changes Made

Following the AWS sample from: https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/04-AgentCore-memory/01-short-term-memory/02-multi-agent/with-strands-agent/travel-planning-agent.ipynb

### Key Change: Memory Configuration in BedrockAgentCoreApp

**Before (Manual Memory Management):**
```python
app = BedrockAgentCoreApp()
memory_client = MemoryClient()

# Manual retrieval
history = memory_client.get_last_k_turns(...)
# Manual storage
memory_client.create_event(...)
```

**After (Automatic Memory Management):**
```python
app = BedrockAgentCoreApp(
    memory_id=MEMORY_ID,
    actor_id=ACTOR_ID,
    branch_name=BRANCH_NAME
)

# AgentCore automatically handles:
# - Retrieving conversation history
# - Injecting context into agent calls
# - Storing new conversations
```

## How It Works

### 1. App Initialization
```python
app = BedrockAgentCoreApp(
    memory_id="memory_rllrl-lfg7zBH6MH",
    actor_id="travel_orchestrator",
    branch_name="main"
)
```

When you configure memory at the app level, AgentCore automatically:
- Retrieves conversation history for the session
- Injects it as context before agent invocation
- Stores the conversation after agent response

### 2. Entrypoint Simplification

**Before:**
```python
# Manually retrieve history
history = memory_client.get_last_k_turns(...)
context = format_history(history)
agent_input = f"{context}\n\n{user_input}"

# Call agent
response = agent(agent_input)

# Manually store
memory_client.create_event(...)
```

**After:**
```python
# Just call the agent - AgentCore handles everything
response = agent(user_input)
```

### 3. Session Management

AgentCore uses the `session_id` from the payload to:
- Retrieve the correct conversation history
- Store new messages in the right session
- Keep conversations isolated per user

## Benefits

1. **Simpler Code**: No manual memory operations
2. **Automatic Context**: History is automatically injected
3. **Error Handling**: AgentCore handles memory errors gracefully
4. **Consistent**: Follows AWS best practices

## Configuration

### Memory Settings
- **Memory ID**: `memory_rllrl-lfg7zBH6MH`
- **Actor ID**: `travel_orchestrator`
- **Branch**: `main`

### Payload Format
```json
{
  "input": "Plan a trip to Paris",
  "session_id": "session_123"
}
```

Or with camelCase (both supported):
```json
{
  "input": "Plan a trip to Paris",
  "sessionId": "session_123"
}
```

## Expected Behavior

### First Message in Session
```
[MEMORY] AgentCore will automatically handle memory operations
[ENTRYPOINT] Invoking orchestrator agent...
[MEMORY] AgentCore will automatically store this conversation
```

AgentCore:
- Finds no previous history
- Calls agent with just the user input
- Stores the conversation

### Subsequent Messages
```
[MEMORY] AgentCore will automatically handle memory operations
[ENTRYPOINT] Invoking orchestrator agent...
[MEMORY] AgentCore will automatically store this conversation
```

AgentCore:
- Retrieves previous conversation history
- Injects it as context before calling the agent
- Agent sees full conversation history
- Stores the new exchange

## Verification

To verify memory is working:

1. **Send first message**: "I want to go to Paris"
2. **Send follow-up**: "What about hotels?" (should remember Paris)
3. **Close browser and reopen**
4. **Send message**: "What were we discussing?" (should remember Paris conversation)

If step 4 works, memory persistence is functioning correctly!

## Troubleshooting

### If Memory Still Doesn't Work

1. **Check AgentCore Logs**: Look for memory-related errors
2. **Verify Permissions**: Ensure runtime can access memory
3. **Check Memory ID**: Confirm it exists and is correct
4. **Test Manually**:
   ```bash
   aws bedrock-agentcore list-events \
     --memory-id memory_rllrl-lfg7zBH6MH \
     --actor-id travel_orchestrator \
     --session-id test_session \
     --region eu-central-1
   ```

### Common Issues

- **ResourceNotFoundException**: Memory not accessible to runtime
- **AccessDeniedException**: IAM permissions missing
- **ValidationException**: Invalid memory_id or actor_id format

## Next Steps

1. **Deploy**: Run `./deploy-frontend.sh`
2. **Test**: Send messages and verify context is maintained
3. **Verify Persistence**: Close/reopen browser and check history loads

The memory should now work automatically through AgentCore! 🎉
