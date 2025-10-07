# Debugging AgentCore Response Issue

## Current Problem

Lambda logs show: `Response received: 0 characters`

This means AgentCore is being invoked but the response isn't being parsed correctly.

## Changes Made

### Enhanced Response Parsing

Updated `lambda/handler.py` to handle multiple response formats:

1. **Primary**: Check for `response` field (list of strings)
2. **Fallback 1**: Try event stream with chunks
3. **Fallback 2**: Try reading body directly
4. **Added detailed logging** to see response structure

### New Logging

```python
print(f"Payload: {payload.decode('utf-8')}")  # See what we're sending
print(f"Response keys: {list(response.keys())}")  # See response structure
print(f"Full response structure: {type(response)}")  # See response type
print(f"Raw response: {response}")  # See full response if empty
```

## Testing Steps

### 1. Redeploy Lambda

```bash
cd lambda
./deploy-lambda.sh
```

### 2. Test Invocation

```bash
# Test with AWS CLI
aws lambda invoke \
  --function-name travel-assistant-proxy \
  --payload '{"body": "{\"message\": \"hello\", \"session_id\": \"test\"}"}' \
  --log-type Tail \
  response.json \
  --query 'LogResult' \
  --output text | base64 -d
```

### 3. Check CloudWatch Logs

Look for these new log entries:

```
Payload: {"input": "hello", "sessionId": "test"}
Response keys: ['response', 'ResponseMetadata']  # or ['body', ...]
Full response structure: <class 'dict'>
```

## Expected Response Formats

### Format 1: Direct Response (Most Likely)
```python
{
    'response': ['Hello! How can I help you plan your trip?'],
    'ResponseMetadata': {...}
}
```

### Format 2: Event Stream
```python
{
    'body': <EventStream object>,
    'ResponseMetadata': {...}
}
```

### Format 3: Simple String
```python
{
    'body': b'Hello! How can I help you plan your trip?',
    'ResponseMetadata': {...}
}
```

## Troubleshooting

### If Still Getting 0 Characters

**Check AgentCore Logs**:
```bash
# Find the log group
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/bedrock-agentcore"

# Tail the logs
aws logs tail /aws/bedrock-agentcore/runtime/YOUR_RUNTIME_ID --follow
```

**Look for**:
```
[ENTRYPOINT] Received payload: {'input': 'hello', 'sessionId': 'test'}
[ENTRYPOINT] User input: hello
[ENTRYPOINT] Invoking orchestrator agent...
[ENTRYPOINT] Returning response: 45 characters
```

### If AgentCore Logs Show Response But Lambda Gets 0

This means the response format is different than expected.

**Solution**: Check the Lambda logs for:
```
Response keys: [...]
```

Then update the Lambda handler to parse that specific format.

### Common Issues

#### Issue 1: Response is in 'output' field
```python
# Add to Lambda handler:
if 'output' in response:
    result = response['output']
```

#### Issue 2: Response is in 'text' field
```python
# Add to Lambda handler:
if 'text' in response:
    result = response['text']
```

#### Issue 3: Response is in 'content' field
```python
# Add to Lambda handler:
if 'content' in response:
    result = response['content']
```

## Manual Test

### Test AgentCore Directly

```python
import boto3
import json

client = boto3.client('bedrock-agentcore')

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:eu-central-1:206631439304:runtime/hosted_agent_rkxzc-Yq2wttGAF4',
    traceId='test-123',
    payload=json.dumps({
        "input": "hello",
        "sessionId": "test"
    }).encode('utf-8')
)

print("Response keys:", list(response.keys()))
print("Response:", response)
```

Run this locally or in a Lambda test to see the exact response structure.

## Expected Fix

After redeployment with enhanced logging, the Lambda logs should show:

```
Invoking AgentCore Runtime: arn:...
Session: test, Message: hello
Payload: {"input": "hello", "sessionId": "test"}
Response keys: ['response', 'ResponseMetadata']
Full response structure: <class 'dict'>
Response received: 45 characters  # ✅ Not 0!
```

## If Response Format is Different

Based on the logs, update the Lambda handler:

```python
# Example: If response is in 'output' field
if 'output' in response:
    result = response['output']
elif 'response' in response:
    response_list = response['response']
    if isinstance(response_list, list):
        result = ''.join(response_list)
    else:
        result = str(response_list)
# ... etc
```

## Next Steps

1. ✅ Redeploy Lambda with enhanced logging
2. ⏳ Test invocation
3. ⏳ Check CloudWatch logs for response structure
4. ⏳ Update Lambda handler if needed based on actual response format
5. ⏳ Test from frontend

The enhanced logging will tell us exactly what format AgentCore is returning!
