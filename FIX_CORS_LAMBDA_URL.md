# Fix CORS and Lambda Function URL Issues

## Problem

Browser shows: `TypeError: Failed to fetch`

This is a CORS issue - the browser is blocking the request.

## Root Causes

1. **Lambda Function URL CORS not configured**
2. **Lambda response headers incomplete**
3. **OPTIONS preflight not handled correctly**

## Fixes Applied

### 1. Enhanced Lambda Handler

#### Added Detailed Logging
```python
print(f"Received event: {json.dumps(event)}")
print(f"HTTP Method: {http_method}")
print(f"Raw body: {body_str}")
```

#### Fixed CORS Headers
```python
"Access-Control-Allow-Origin": "*",
"Access-Control-Allow-Headers": "Content-Type,Authorization",
"Access-Control-Allow-Methods": "GET,POST,OPTIONS",
"Access-Control-Allow-Credentials": "false",
```

#### Added Base64 Decoding
```python
if event.get("isBase64Encoded", False):
    body_str = base64.b64decode(body_str).decode('utf-8')
```

### 2. Configure Lambda Function URL CORS

**CRITICAL**: Lambda Function URL needs CORS configuration at the AWS level!

```bash
# Update Lambda Function URL configuration
aws lambda update-function-url-config \
  --function-name travel-assistant-proxy \
  --cors '{
    "AllowOrigins": ["*"],
    "AllowMethods": ["POST", "OPTIONS"],
    "AllowHeaders": ["Content-Type", "Authorization"],
    "MaxAge": 86400
  }'
```

Or using AWS Console:
1. Go to Lambda → Functions → travel-assistant-proxy
2. Click "Configuration" tab
3. Click "Function URL"
4. Click "Edit"
5. Under "Configure cross-origin resource sharing (CORS)":
   - Allow origin: `*`
   - Allow methods: `POST`, `OPTIONS`
   - Allow headers: `Content-Type`, `Authorization`
   - Max age: `86400`
6. Click "Save"

## Deployment Steps

### Step 1: Update Lambda Code

```bash
cd lambda
./deploy-lambda.sh
```

### Step 2: Configure CORS on Function URL

```bash
aws lambda update-function-url-config \
  --function-name travel-assistant-proxy \
  --cors '{
    "AllowOrigins": ["*"],
    "AllowMethods": ["POST", "OPTIONS"],
    "AllowHeaders": ["Content-Type", "Authorization"],
    "MaxAge": 86400
  }'
```

### Step 3: Verify CORS Configuration

```bash
aws lambda get-function-url-config \
  --function-name travel-assistant-proxy
```

Should show:
```json
{
    "Cors": {
        "AllowOrigins": ["*"],
        "AllowMethods": ["POST", "OPTIONS"],
        "AllowHeaders": ["Content-Type", "Authorization"],
        "MaxAge": 86400
    }
}
```

### Step 4: Test from Browser

1. Open CloudFront URL
2. Open browser console (F12)
3. Try sending a message
4. Should NOT see "Failed to fetch" error

## Testing CORS

### Test OPTIONS Request

```bash
curl -X OPTIONS \
  -H "Origin: https://your-cloudfront-domain.cloudfront.net" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -v \
  https://your-lambda-url.lambda-url.eu-central-1.on.aws/
```

Should return:
```
< HTTP/2 200
< access-control-allow-origin: *
< access-control-allow-methods: POST, OPTIONS
< access-control-allow-headers: Content-Type, Authorization
```

### Test POST Request

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Origin: https://your-cloudfront-domain.cloudfront.net" \
  -d '{"message": "hello", "session_id": "test"}' \
  -v \
  https://your-lambda-url.lambda-url.eu-central-1.on.aws/
```

Should return:
```json
{
  "response": "...",
  "session_id": "test"
}
```

## Common Issues

### Issue 1: Still Getting "Failed to fetch"

**Check**: CORS configuration on Lambda Function URL

```bash
aws lambda get-function-url-config --function-name travel-assistant-proxy
```

If `Cors` is empty or missing, configure it:
```bash
aws lambda update-function-url-config \
  --function-name travel-assistant-proxy \
  --cors '{
    "AllowOrigins": ["*"],
    "AllowMethods": ["POST", "OPTIONS"],
    "AllowHeaders": ["Content-Type", "Authorization"],
    "MaxAge": 86400
  }'
```

### Issue 2: OPTIONS returns 403

**Problem**: Lambda Function URL auth mode is set to AWS_IAM

**Fix**: Change to NONE for public access:
```bash
aws lambda update-function-url-config \
  --function-name travel-assistant-proxy \
  --auth-type NONE
```

### Issue 3: POST works in curl but not browser

**Problem**: Browser is sending OPTIONS preflight that's being blocked

**Fix**: Ensure CORS is configured on Lambda Function URL (not just in code)

## Verification Checklist

- [ ] Lambda code updated with enhanced CORS headers
- [ ] Lambda code redeployed
- [ ] Lambda Function URL CORS configured via AWS CLI/Console
- [ ] Lambda Function URL auth type is NONE
- [ ] OPTIONS request returns 200 with CORS headers
- [ ] POST request returns 200 with response
- [ ] Browser console shows no CORS errors
- [ ] Frontend can send messages successfully

## Expected Logs After Fix

### Lambda Logs
```
Received event: {"requestContext": {...}, "body": "{...}", ...}
HTTP Method: POST
Raw body: {"message": "hello", "session_id": "test"}
Parsed - Message: hello, Session: test
Invoking AgentCore Runtime: arn:...
Payload: {"input": "hello", "sessionId": "test"}
Response received: 45 characters
```

### Browser Console
```
✅ No "Failed to fetch" errors
✅ Response appears in chat
✅ Network tab shows 200 OK
```

## Quick Fix Script

```bash
#!/bin/bash
# fix_cors.sh

echo "1. Deploying Lambda..."
cd lambda
./deploy-lambda.sh

echo "2. Configuring CORS on Function URL..."
aws lambda update-function-url-config \
  --function-name travel-assistant-proxy \
  --cors '{
    "AllowOrigins": ["*"],
    "AllowMethods": ["POST", "OPTIONS"],
    "AllowHeaders": ["Content-Type", "Authorization"],
    "MaxAge": 86400
  }'

echo "3. Verifying configuration..."
aws lambda get-function-url-config --function-name travel-assistant-proxy

echo "4. Testing OPTIONS..."
LAMBDA_URL=$(aws lambda get-function-url-config \
  --function-name travel-assistant-proxy \
  --query 'FunctionUrl' \
  --output text)

curl -X OPTIONS \
  -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST" \
  -v \
  "$LAMBDA_URL"

echo ""
echo "✅ Done! Test from browser now."
```

## Summary

The "Failed to fetch" error is a CORS issue. The fix requires:

1. ✅ Update Lambda code with proper CORS headers
2. ⚠️ **CRITICAL**: Configure CORS on Lambda Function URL itself
3. ✅ Ensure auth type is NONE for public access

Without step 2, the browser will block all requests!
