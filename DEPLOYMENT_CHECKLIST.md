# Deployment Checklist - Model Update

## Current Issue

Still getting: `ValidationException: The provided model identifier is invalid`

**Root Cause**: Container is running old code with Claude Sonnet 4 model.

## Verification Steps

### 1. Verify Local Code is Correct

Check that all files have Nova Micro:
```bash
grep -r "claude-sonnet-4" agentcore/
# Should return NO results

grep -r "nova-micro" agentcore/runtime_agent_main.py
# Should show 4 occurrences (orchestrator + 3 specialists)
```

✅ **Verified**: Local code is correct with Nova Micro.

### 2. Check Container Build

The container must be rebuilt to pick up changes:

```bash
# Option 1: Docker build with no cache
docker build --no-cache -t travel-agent-agentcore ./agentcore

# Option 2: AWS CodeBuild
aws codebuild start-build --project-name travel-assistant-build

# Option 3: ECR push (if using ECR)
docker tag travel-agent-agentcore:latest <ecr-uri>:latest
docker push <ecr-uri>:latest
```

### 3. Verify Container Image

Check the image was built recently:
```bash
docker images travel-agent-agentcore
# Check the CREATED timestamp - should be recent
```

### 4. Check AgentCore Runtime

Verify AgentCore is using the new image:

```bash
# Check CloudWatch logs for startup
# Should see: [AGENT] Creating travel orchestrator agent...
# With timestamp matching your rebuild time
```

### 5. Force Container Restart

If using AgentCore, you may need to:

```bash
# Delete and recreate the agent runtime
aws bedrock-agentcore-control delete-agent-runtime \
  --agent-runtime-id <runtime-id>

# Then recreate with new image
aws bedrock-agentcore-control create-agent-runtime \
  --agent-runtime-name travel-agent \
  --container-image <ecr-uri>:latest
```

## Common Issues

### Issue 1: Docker Cache
**Problem**: Docker is using cached layers with old code.

**Solution**: Use `--no-cache` flag:
```bash
docker build --no-cache -t travel-agent-agentcore ./agentcore
```

### Issue 2: Wrong Image Running
**Problem**: AgentCore is still pointing to old image.

**Solution**: Update the agent runtime to use new image URI.

### Issue 3: Code Not Copied
**Problem**: Dockerfile not copying updated file.

**Solution**: Verify Dockerfile copies the right file:
```dockerfile
COPY runtime_agent_main.py .  # ✅ Correct
```

### Issue 4: Multiple Versions
**Problem**: Multiple versions of the file exist.

**Solution**: Verify you're editing the right file:
```bash
find . -name "runtime_agent_main.py" -type f
# Should only show: ./agentcore/runtime_agent_main.py
```

## Step-by-Step Rebuild Process

### Step 1: Clean Everything
```bash
# Remove old Docker images
docker rmi travel-agent-agentcore:latest

# Clear Docker build cache
docker builder prune -af
```

### Step 2: Verify Code
```bash
# Check the model in the file
grep "model=" agentcore/runtime_agent_main.py

# Should show ONLY:
# model="us.amazon.nova-micro-v1:0"
```

### Step 3: Rebuild
```bash
cd agentcore
docker build --no-cache -t travel-agent-agentcore .
```

### Step 4: Verify Build
```bash
# Check the image
docker images travel-agent-agentcore

# Test locally (optional)
docker run -p 8000:8000 travel-agent-agentcore
```

### Step 5: Push to Registry
```bash
# Tag for ECR
docker tag travel-agent-agentcore:latest <account>.dkr.ecr.<region>.amazonaws.com/travel-agent:latest

# Push
docker push <account>.dkr.ecr.<region>.amazonaws.com/travel-agent:latest
```

### Step 6: Update AgentCore
```bash
# Update the agent runtime to use new image
aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id <runtime-id> \
  --container-image <account>.dkr.ecr.<region>.amazonaws.com/travel-agent:latest
```

### Step 7: Wait for Deployment
```bash
# Check status
aws bedrock-agentcore-control describe-agent-runtime \
  --agent-runtime-id <runtime-id>

# Wait until status is READY
```

### Step 8: Verify Logs
```bash
# Check CloudWatch logs
# Look for recent startup with:
# [AGENT] Creating travel orchestrator agent...
# [AGENT] Orchestrator agent created successfully!

# Timestamp should match your rebuild time
```

### Step 9: Test
```bash
# Invoke the agent
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn <arn> \
  --payload '{"input": "Hello"}'
```

## Quick Verification Script

Create this script to verify the deployment:

```bash
#!/bin/bash
# verify_deployment.sh

echo "=== Checking Local Code ==="
echo "Models in runtime_agent_main.py:"
grep "model=" agentcore/runtime_agent_main.py

echo ""
echo "=== Checking for Old Models ==="
OLD_MODELS=$(grep -r "claude-sonnet-4" agentcore/ 2>/dev/null)
if [ -z "$OLD_MODELS" ]; then
    echo "✅ No old models found"
else
    echo "❌ Old models still present:"
    echo "$OLD_MODELS"
fi

echo ""
echo "=== Docker Images ==="
docker images travel-agent-agentcore

echo ""
echo "=== Ready to Deploy ==="
echo "Run: docker build --no-cache -t travel-agent-agentcore ./agentcore"
```

## Expected CloudWatch Logs After Successful Deployment

```
[STARTUP] Initializing orchestrator agent system...
[AGENT] Creating specialized agents...
[AGENT] Specialized agents created
[AGENT] Creating travel orchestrator agent...
[AGENT] Orchestrator agent created successfully!
[AGENT] Agent name: TravelOrchestrator
[AGENT] Specialized agents: FlightBookingAgent, HotelBookingAgent, ActivitiesAgent
[AGENT] Tools: ['flight_booking_tool', 'hotel_booking_tool', 'activities_tool']
[RUNTIME] Starting AgentCore app...
```

Then when invoked:
```
[ENTRYPOINT] Received payload: {'input': 'Hello'}
[ENTRYPOINT] User input: Hello
[ENTRYPOINT] Invoking orchestrator agent...
[ENTRYPOINT] Agent response type: <class 'strands.response.Response'>
[ENTRYPOINT] Returning response: 45 characters
```

**NO ValidationException errors!**

## If Still Getting Errors

1. **Check the timestamp** in CloudWatch logs - is it recent?
2. **Verify the image** - is AgentCore using the new image?
3. **Check IAM permissions** - does the role have bedrock:InvokeModel?
4. **Verify region** - is Nova Micro available in your region?

```bash
# Check Nova Micro availability
aws bedrock list-foundation-models \
  --region <your-region> \
  --query "modelSummaries[?contains(modelId, 'nova-micro')]"
```

## Contact Points

If still having issues, provide:
1. CloudWatch log timestamp of latest startup
2. Docker image build timestamp
3. AgentCore runtime status
4. Output of: `grep "model=" agentcore/runtime_agent_main.py`
