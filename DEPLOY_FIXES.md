# Deploy Fixes - Frontend & Lambda Integration

## Changes Made

### 1. ✅ Lambda Handler (`lambda/handler.py`)
**Fixed payload key**: Changed `inputText` to `input` to match AgentCore entrypoint expectations

### 2. ✅ Frontend (`frontend/app.js`)
**Fixed API paths**: Removed `/chat` and `/reset` paths since Lambda Function URL doesn't support routing

## Deployment Steps

### Step 1: Redeploy Lambda Function

```bash
cd lambda

# Option A: Using deploy script
./deploy-lambda.sh

# Option B: Manual deployment
zip -r function.zip handler.py requirements.txt
aws lambda update-function-code \
  --function-name travel-assistant-proxy \
  --zip-file fileb://function.zip
```

### Step 2: Update Frontend in S3

```bash
cd frontend

# Sync to S3 bucket
aws s3 sync . s3://YOUR-FRONTEND-BUCKET-NAME/ \
  --exclude ".git/*" \
  --exclude "*.md"

# Example:
# aws s3 sync . s3://travel-assistant-frontend/
```

### Step 3: Invalidate CloudFront Cache

```bash
# Get your distribution ID
aws cloudfront list-distributions \
  --query "DistributionList.Items[*].[Id,DomainName]" \
  --output table

# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"

# Example:
# aws cloudfront create-invalidation \
#   --distribution-id E1234567890ABC \
#   --paths "/*"
```

## Verification

### 1. Check Lambda Logs

After deployment, invoke the Lambda and check CloudWatch logs:

```bash
# Test invoke
aws lambda invoke \
  --function-name travel-assistant-proxy \
  --payload '{"body": "{\"message\": \"hello\", \"session_id\": \"test\"}"}' \
  response.json

# Check logs
aws logs tail /aws/lambda/travel-assistant-proxy --follow
```

**Expected logs**:
```
Invoking AgentCore Runtime: arn:...
Session: test, Message: hello
Response received: 45 characters  # ✅ Should be > 0!
```

### 2. Test Frontend

1. Open CloudFront URL in browser
2. Open browser console (F12)
3. Sign in
4. Send message: "Hello"
5. Check for errors in console

**Expected behavior**:
- ✅ No "Failed to fetch" errors
- ✅ Response appears in chat
- ✅ Lambda logs show response > 0 characters

### 3. Test AgentCore Integration

Send a travel query:
```
"Plan a 3-day trip to Paris from London"
```

**Expected**:
- Orchestrator calls flight_booking_tool
- Orchestrator calls hotel_booking_tool
- Orchestrator calls activities_tool
- Returns comprehensive travel plan

## Troubleshooting

### Issue: Still getting "0 characters" response

**Check**:
1. Lambda is using updated code (check last modified time)
2. AgentCore logs show `[ENTRYPOINT] Received payload: {'input': ...}`
3. Payload has `input` key, not `inputText`

**Fix**:
```bash
# Verify Lambda code
aws lambda get-function --function-name travel-assistant-proxy

# Check last update time
aws lambda get-function-configuration \
  --function-name travel-assistant-proxy \
  --query "LastModified"
```

### Issue: CORS errors in browser

**Check**:
1. Lambda returns proper CORS headers
2. CloudFront allows CORS

**Fix**: Lambda already has CORS headers, but verify:
```python
"Access-Control-Allow-Origin": "*",
"Access-Control-Allow-Headers": "Content-Type,Authorization",
"Access-Control-Allow-Methods": "GET,POST,OPTIONS",
```

### Issue: Authentication errors

**Check**:
1. Cognito is configured correctly
2. User pool and client IDs match in `auth.js`

**Note**: Lambda handler doesn't validate auth token currently. If needed, add:
```python
# In lambda_handler, after parsing body:
auth_header = event.get('headers', {}).get('authorization', '')
if not auth_header.startswith('Bearer '):
    return create_response(401, {"error": "Unauthorized"})
```

## Quick Test Script

```bash
#!/bin/bash
# test_deployment.sh

echo "Testing Lambda..."
aws lambda invoke \
  --function-name travel-assistant-proxy \
  --payload '{"body": "{\"message\": \"hello\", \"session_id\": \"test\"}"}' \
  response.json

echo "Response:"
cat response.json
echo ""

echo "Checking logs..."
aws logs tail /aws/lambda/travel-assistant-proxy --since 1m
```

## Summary

✅ Lambda payload fixed: `input` instead of `inputText`
✅ Frontend paths fixed: Direct to Function URL
⏳ Deploy Lambda
⏳ Deploy Frontend to S3
⏳ Invalidate CloudFront cache
⏳ Test end-to-end

After these steps, the integration should work correctly!
