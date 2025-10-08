# AgentCore Memory Implementation - AWS Pattern with Strands Hooks

## Changes Made

Following the AWS sample from: https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/04-AgentCore-memory/01-short-term-memory/02-multi-agent/with-strands-agent/travel-planning-agent.ipynb

### Key Change: Using Strands Hooks for Memory Management

**Before (Manual Memory Management in Entrypoint):**
```python
# Manual retrieval in entrypoint
history = memory_client.get_last_k_turns(...)
context = format_history(history)
agent_input = f"{context}\n\n{user_input}"

# Call agent
response = agent(agent_input)

# Manual storage
memory_client.create_event(...)
```

**After (Automatic Memory via Strands Hooks):**
```python
# Create memory hook provider
class ShortTermMemoryHook(HookProvider):
    def on_agent_initialized(self, event):
        # Automatically load conversation history
        # Inject into agent's system prompt
        
    def on_message_added(self, event):
        # Automatically store new messages

# Attach hooks to agents
agent = Agent(
    hooks=[ShortTermMemoryHook(memory_client, MEMORY_ID)],
    state={"actor_id": actor_id, "session_id": session_id}
)

# Just call the agent - hooks handle everything
response = agent(user_input)
```

## How It Works

### 1. Memory Hook Provider

The `ShortTermMemoryHook` class implements two key lifecycle hooks:

```python
class ShortTermMemoryHook(HookProvider):
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load conversation history when agent starts"""
        # Get actor_id and session_id from agent.state
        # Retrieve last K turns from memory
        # Inject history into agent's system prompt
        
    def on_message_added(self, event: MessageAddedEvent):
        """Store new messages in memory"""
        # Get the latest message
        # Store it in memory with actor_id and session_id
```

### 2. Agent Creation with Memory

Each specialized agent is created with:
- Memory hooks attached
- State containing `actor_id` and `session_id`

```python
memory_hooks = ShortTermMemoryHook(memory_client, MEMORY_ID)

agent = Agent(
    name="FlightBookingAgent",
    model="eu.amazon.nova-micro-v1:0",
    hooks=[memory_hooks],
    state={"actor_id": "flight-session123", "session_id": "session123"}
)
```

### 3. Automatic Memory Operations

When you call an agent:
1. **on_agent_initialized** hook fires:
   - Retrieves conversation history from memory
   - Injects it into the agent's system prompt
   
2. Agent processes the request with full context

3. **on_message_added** hook fires:
   - Stores the new message in memory
   - Associates it with the correct actor_id and session_id

### 4. Session Management

Each session gets its own set of specialized agents:
- `flight-{session_id}` - Flight booking agent
- `hotel-{session_id}` - Hotel booking agent  
- `activities-{session_id}` - Activities agent

All agents in a session share the same `session_id` but have unique `actor_id` values, allowing:
- Isolated conversations per session
- Specialized memory per agent type
- Shared context across the session

## Benefits

1. **Lifecycle Integration**: Memory operations tied to agent lifecycle events
2. **Automatic Context**: History automatically injected before agent runs
3. **Automatic Storage**: New messages automatically stored after agent responds
4. **Per-Agent Memory**: Each specialized agent maintains its own conversation history
5. **Consistent**: Follows AWS reference implementation exactly

## Configuration

### Memory Settings
- **Memory ID**: `memory_rllrl-lfg7zBH6MH`
- **Branch**: `main`
- **Actor IDs**: Dynamically created per session:
  - `flight-{session_id}` for flight agent
  - `hotel-{session_id}` for hotel agent
  - `activities-{session_id}` for activities agent

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

### How Actor IDs Work

Each session creates unique actor IDs for specialized agents:
- Session `abc123` creates: `flight-abc123`, `hotel-abc123`, `activities-abc123`
- Session `xyz789` creates: `flight-xyz789`, `hotel-xyz789`, `activities-xyz789`

This ensures:
- Each session has isolated conversations
- Each specialized agent maintains its own memory within the session
- Memory is properly scoped and doesn't leak between sessions

## Expected Behavior

### First Message in Session
```
[ENTRYPOINT] Session ID: session_123
[MEMORY] Memory operations handled by Strands hooks
[AGENT] Created specialized agents for session: session_123
[FLIGHT AGENT] Processing: Find flights to Paris
INFO - No previous conversation history found
INFO - ✅ Stored message in memory: user
INFO - ✅ Stored message in memory: assistant
```

What happens:
1. Orchestrator receives user input
2. Delegates to flight agent (creates agent with hooks)
3. `on_agent_initialized` hook: No history found (first message)
4. Agent processes request
5. `on_message_added` hook: Stores conversation in memory

### Subsequent Messages in Same Session
```
[ENTRYPOINT] Session ID: session_123
[MEMORY] Memory operations handled by Strands hooks
[FLIGHT AGENT] Processing: What about hotels?
INFO - Context from memory: User: Find flights to Paris...
INFO - ✅ Loaded 2 recent messages
INFO - ✅ Stored message in memory: user
INFO - ✅ Stored message in memory: assistant
```

What happens:
1. Orchestrator receives follow-up
2. Delegates to hotel agent (reuses or creates agent)
3. `on_agent_initialized` hook: Retrieves previous conversation
4. Hook injects history into agent's system prompt
5. Agent processes with full context (remembers Paris!)
6. `on_message_added` hook: Stores new exchange

## Verification

To verify memory is working:

1. **Send first message**: "I want to go to Paris"
   - Should get flight recommendations
   
2. **Send follow-up**: "What about hotels?" (should remember Paris)
   - Should recommend Paris hotels without asking destination again
   
3. **Send another**: "And activities?" (should still remember Paris)
   - Should suggest Paris activities
   
4. **Close browser and reopen with same session**
5. **Send message**: "What were we discussing?" 
   - Should remember the entire Paris conversation

If steps 2-5 work, memory is functioning correctly!

### Checking Memory in AWS Console

You can verify memory storage:

```bash
aws bedrock-agentcore list-events \
  --memory-id memory_rllrl-lfg7zBH6MH \
  --actor-id flight-session_123 \
  --session-id session_123 \
  --region eu-central-1
```

Replace `session_123` with your actual session ID from the browser.

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
