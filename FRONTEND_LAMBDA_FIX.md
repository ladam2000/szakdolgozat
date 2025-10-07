# Frontend & Lambda Integration Fix

## Issues Found

### 1. Payload Key Mismatch ✅ FIXED
**Problem**: Lambda sends `inputText`, but AgentCore entrypoint expects `input` or `prompt`

**Fix Applied**: Updated Lambda handler to send `input` instead of `inputText`

```python
# Before
payload = json.dumps({
    "inputText": message,  # ❌ Wrong key
    "sessionId": session_id
})

# After
payload = json.dumps({
    "input": message,  # ✅ Correct key
    "sessionId": session_id
})
```

### 2. Frontend API Path Issue
**Problem**: Frontend calls `/chat` endpoint, but Lambda Function URL doesn't have routing

**Current**:
```javascript
const response = await fetch(`${API_URL}/chat`, {  // ❌ /chat doesn't exist
```

**Should be**:
```javascript
const response = await fetch(API_URL, {  // ✅ Direct to function URL
```

### 3. Response Format Mismatch
**Problem**: Lambda returns `{"response": "...", "session_id": "..."}` but frontend expects this format

**Status**: ✅ This is correct, no change needed

## Fixes Required

### Fix 1: Update Lambda Handler (DONE ✅)
File: `lambda/handler.py`
- Changed `inputText` to `input` in payload

### Fix 2: Update Frontend API Calls
File: `frontend/app.js`

Need to update the fetch calls to not include `/chat` or `/reset` paths since Lambda Function URL doesn't support routing.

## Solution Options

### Option A: Update Frontend (Simplest)
Remove `/chat` and `/reset` paths from frontend:

```javascript
// Change this:
const response = await fetch(`${API_URL}/chat`, {

// To this:
const response = await fetch(API_URL, {
```

### Option B: Add API Gateway (More Complex)
Deploy an API Gateway with proper routing:
- `POST /chat` → Lambda
- `POST /reset` → Lambda (or separate function)

### Option C: Update Lambda to Handle Routing
Add path routing logic to Lambda handler:

```python
def lambda_handler(event, context):
    path = event.get('rawPath', '/')
    
    if path == '/chat':
        return handle_chat(event, context)
    elif path == '/reset':
        return handle_reset(event, context)
    else:
        return create_response(404, {"error": "Not found"})
```

## Recommended Fix

**Use Option A** - Update frontend to remove paths since you're using Lambda Function URL.

## Files to Update

### 1. lambda/handler.py ✅ DONE
```python
payload = json.dumps({
    "input": message,  # Changed from inputText
    "sessionId": session_id
})
```

### 2. frontend/app.js (TODO)
```javascript
// Line ~113 - Change:
const response = await fetch(`${API_URL}/chat`, {
// To:
const response = await fetch(API_URL, {

// Line ~163 - Change:
await fetch(`${API_URL}/reset`, {
// To:
await fetch(API_URL, {
// And add a "reset" flag in the body
```

## Testing After Fix

1. **Redeploy Lambda**:
```bash
cd lambda
./deploy-lambda.sh
```

2. **Update Frontend**:
```bash
# Update app.js as shown above
# Then sync to S3
aws s3 sync frontend/ s3://your-bucket-name/
```

3. **Test**:
- Open CloudFront URL
- Sign in
- Send message: "Hello"
- Should receive response from agent

## Expected Logs After Fix

**Lambda logs should show**:
```
Invoking AgentCore Runtime: arn:...
Session: session_xxx, Message: hello
Response received: 45 characters  # ✅ Not 0!
```

**AgentCore logs should show**:
```
[ENTRYPOINT] Received payload: {'input': 'hello', 'sessionId': 'session_xxx'}
[ENTRYPOINT] User input: hello
[ENTRYPOINT] Invoking orchestrator agent...
[ENTRYPOINT] Returning response: 45 characters
```

## Current Status

✅ Lambda payload fixed (`input` instead of `inputText`)
⏳ Frontend needs update (remove `/chat` and `/reset` paths)
⏳ Redeploy Lambda
⏳ Update frontend in S3

## Quick Fix Commands

```bash
# 1. Redeploy Lambda with fix
cd lambda
./deploy-lambda.sh

# 2. Update frontend (after editing app.js)
cd frontend
# Edit app.js to remove /chat and /reset paths
aws s3 sync . s3://your-frontend-bucket/

# 3. Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```
