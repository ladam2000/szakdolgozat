# Troubleshooting 500 Error from Runtime

## Current Status

✅ Agent initializes successfully:
```
[STARTUP] Initializing orchestrator agent system...
[AGENT] Creating specialized agents...
[AGENT] Specialized agents created
[AGENT] Creating travel orchestrator agent...
[AGENT] Orchestrator agent created successfully!
[RUNTIME] Starting AgentCore app...
```

❌ Getting 500 error when invoking

## Possible Causes

### 1. Payload Format Issue
**Problem**: AgentCore might be sending a different payload format than expected.

**Check**: Look for `[ENTRYPOINT] Received payload:` in CloudWatch logs after invoking.

**Expected formats**:
```json
{"input": "Plan a trip to Paris"}
// or
{"prompt": "Plan a trip to Paris"}
```

### 2. Model Access Issue
**Problem**: IAM role might not have permission to invoke Bedrock models.

**Models used**:
- Orchestrator: `us.anthropic.claude-sonnet-4-20250514-v1:0`
- Specialists: `us.amazon.nova-micro-v1:0`

**Check IAM permissions**:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": [
    "arn:aws:bedrock:*::foundation-model/us.anthropic.claude-sonnet-4-20250514-v1:0",
    "arn:aws:bedrock:*::foundation-model/us.amazon.nova-micro-v1:0"
  ]
}
```

### 3. Model Not Available in Region
**Problem**: Models might not be available in your region.

**Check available models**:
```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude-sonnet-4')]"

aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'nova-micro')]"
```

### 4. Response Format Issue
**Problem**: Strands response format might be different than expected.

**What to look for in logs**:
```
[ENTRYPOINT] Agent response type: <class '...'>
[ENTRYPOINT] Agent response: ...
```

### 5. Timeout Issue
**Problem**: Agent taking too long to respond (orchestrator calling multiple agents).

**Check**: Lambda timeout settings (should be at least 60 seconds).

## Debugging Steps

### Step 1: Check CloudWatch Logs for Detailed Error
Look for these log entries after invoking:
```
[ENTRYPOINT] Received payload: ...
[ENTRYPOINT] User input: ...
[ENTRYPOINT] Invoking orchestrator agent...
[ENTRYPOINT] Agent response type: ...
[ENTRYPOINT] ERROR: ...  # This will show the actual error
```

### Step 2: Test with Simple Query
Try a very simple query that shouldn't trigger tool calls:
```json
{"input": "Hello"}
```

If this works, the issue is with tool execution.

### Step 3: Check Model Permissions
Verify the execution role has Bedrock permissions:
```bash
aws iam get-role-policy --role-name <execution-role-name> --policy-name <policy-name>
```

### Step 4: Try Alternative Models
If Claude Sonnet 4 isn't available, update to use available models:

**Option 1: Use Claude Haiku (more widely available)**
```python
agent = Agent(
    name="TravelOrchestrator",
    model="us.anthropic.claude-3-5-haiku-20241022-v1:0",  # Changed
    tools=[...],
)
```

**Option 2: Use Nova Pro (AWS native)**
```python
agent = Agent(
    name="TravelOrchestrator",
    model="us.amazon.nova-pro-v1:0",  # Changed
    tools=[...],
)
```

### Step 5: Simplify for Testing
Temporarily remove the orchestrator pattern to test basic functionality:

```python
# Simplified version for testing
@app.entrypoint
def travel_orchestrator_entrypoint(payload):
    user_input = payload.get("input") or payload.get("prompt", "")
    # Return simple response without calling agent
    return f"Received your request: {user_input}. Agent system is working!"
```

If this works, the issue is with the agent invocation.

## Common Error Messages and Solutions

### "AccessDeniedException"
**Solution**: Add Bedrock permissions to execution role.

### "ValidationException: The provided model identifier is invalid"
**Solution**: Model not available in region. Use alternative model or different region.

### "ThrottlingException"
**Solution**: Too many requests. Add retry logic or request quota increase.

### "ServiceQuotaExceededException"
**Solution**: Request quota increase for Bedrock models.

### "TimeoutError"
**Solution**: Increase Lambda timeout or optimize agent prompts.

## Updated Code with Better Error Handling

The latest version of `runtime_agent_main.py` includes:

1. ✅ Try-catch blocks in entrypoint
2. ✅ Try-catch blocks in all tool functions
3. ✅ Detailed logging at each step
4. ✅ Graceful error messages instead of exceptions
5. ✅ Payload validation

## Next Steps

1. **Redeploy with updated error handling**:
   ```bash
   docker build --no-cache -t travel-agent-agentcore ./agentcore
   ```

2. **Invoke again and check CloudWatch logs** for detailed error messages

3. **Look for these specific log entries**:
   - `[ENTRYPOINT] Received payload:` - Shows what AgentCore sent
   - `[ENTRYPOINT] ERROR:` - Shows the actual error
   - `[FLIGHT/HOTEL/ACTIVITIES AGENT] ERROR:` - Shows tool errors

4. **Share the error logs** if you need help debugging further

## Quick Fixes to Try

### Fix 1: Use More Available Models
```python
# In runtime_agent_main.py, change:
model="us.anthropic.claude-3-5-haiku-20241022-v1:0"  # More widely available
```

### Fix 2: Add Model Access Request
If models aren't available:
```bash
# Request model access in AWS Console
# Bedrock > Model access > Request access
```

### Fix 3: Check Region
Ensure you're deploying in a region where these models are available:
- us-east-1 (N. Virginia) - Most models available
- us-west-2 (Oregon) - Good availability
- eu-central-1 (Frankfurt) - Limited availability

## Expected Successful Logs

After fixing, you should see:
```
[ENTRYPOINT] Received payload: {'input': 'Plan a trip to Paris'}
[ENTRYPOINT] User input: Plan a trip to Paris
[ENTRYPOINT] Invoking orchestrator agent...
[ENTRYPOINT] Agent response type: <class 'strands.response.Response'>
[ENTRYPOINT] Extracting from response.message['content']
[ENTRYPOINT] Returning response: 523 characters
```

And potentially:
```
[FLIGHT AGENT] Processing: Find flights to Paris...
[HOTEL AGENT] Processing: Find hotels in Paris...
[ACTIVITIES AGENT] Processing: Suggest activities in Paris...
```
