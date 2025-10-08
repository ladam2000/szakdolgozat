# AgentCore Memory Setup Guide

## Issue

The AgentCore runtime cannot access the memory:
```
ResourceNotFoundException: Memory not found: memory_rllrl-lfg7zBH6MH
```

## Memory Details

- **Memory ID**: `memory_rllrl-lfg7zBH6MH`
- **Memory ARN**: `arn:aws:bedrock-agentcore:eu-central-1:206631439304:memory/memory_rllrl-lfg7zBH6MH`
- **AgentCore Runtime ARN**: `arn:aws:bedrock-agentcore:eu-central-1:206631439304:runtime/hosted_agent_rkxzc-Yq2wttGAF4`

## Solution

### Option 1: Associate Memory with AgentCore Runtime

The memory needs to be associated with the AgentCore runtime. Use the AWS CLI:

```bash
aws bedrock-agentcore associate-memory \
  --runtime-arn arn:aws:bedrock-agentcore:eu-central-1:206631439304:runtime/hosted_agent_rkxzc-Yq2wttGAF4 \
  --memory-arn arn:aws:bedrock-agentcore:eu-central-1:206631439304:memory/memory_rllrl-lfg7zBH6MH \
  --region eu-central-1
```

### Option 2: Update IAM Permissions

Ensure the AgentCore runtime's execution role has permissions to access the memory:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:GetMemory",
        "bedrock-agentcore:ListEvents",
        "bedrock-agentcore:CreateEvent",
        "bedrock-agentcore:GetEvent"
      ],
      "Resource": "arn:aws:bedrock-agentcore:eu-central-1:206631439304:memory/memory_rllrl-lfg7zBH6MH"
    }
  ]
}
```

### Option 3: Create a New Memory

If the memory doesn't exist or can't be accessed, create a new one:

```bash
aws bedrock-agentcore create-memory \
  --memory-name "travel-assistant-memory" \
  --region eu-central-1
```

Then update the `MEMORY_ID` in `agentcore/runtime_agent_main.py` with the new memory ID.

### Option 4: Disable Memory (Temporary)

If you want to test without memory, comment out the memory operations:

In `agentcore/runtime_agent_main.py`, set:
```python
MEMORY_ID = None  # Disable memory
```

And add a check:
```python
if MEMORY_ID:
    # Memory operations
else:
    print("[MEMORY] Memory disabled, skipping...")
```

## Verify Memory Access

After applying the fix, test memory access:

```bash
aws bedrock-agentcore list-events \
  --memory-id memory_rllrl-lfg7zBH6MH \
  --actor-id travel_orchestrator \
  --session-id test_session \
  --region eu-central-1
```

If this works, the AgentCore runtime should also be able to access it.

## Check Current Associations

List memories associated with the runtime:

```bash
aws bedrock-agentcore list-memories \
  --runtime-arn arn:aws:bedrock-agentcore:eu-central-1:206631439304:runtime/hosted_agent_rkxzc-Yq2wttGAF4 \
  --region eu-central-1
```

## Next Steps

1. Try Option 1 (associate memory) first
2. If that doesn't work, check IAM permissions (Option 2)
3. As a last resort, create a new memory (Option 3)
4. For testing, you can temporarily disable memory (Option 4)

After fixing, redeploy:
```bash
./deploy-frontend.sh
```

The logs should then show:
```
[MEMORY] Retrieved 0 conversation events
[MEMORY] No previous conversation history found
[MEMORY] Conversation stored successfully with event ID: evt_...
```
