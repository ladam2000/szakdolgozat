"""Lambda proxy function that calls AgentCore Runtime."""

import json
import os
import uuid
import boto3
from typing import Dict, Any

# Initialize Bedrock AgentCore client
agent_core_client = boto3.client('bedrock-agentcore')

# Get AgentCore Runtime ARN from environment
AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN")

# Memory configuration (for health check only)
MEMORY_ID = "memory_rllrl-lfg7zBH6MH"


def lambda_handler(event: Dict[str, Any], context: Any):
    """Handle Lambda Function URL requests and invoke AgentCore Runtime.
    
    Args:
        event: Lambda Function URL event
        context: Lambda context
        
    Returns:
        Lambda Function URL response
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Handle CORS preflight for Lambda Function URL
    request_context = event.get('requestContext', {})
    http_method = request_context.get('http', {}).get('method', '')
    
    # Also check direct httpMethod for API Gateway compatibility
    if not http_method:
        http_method = event.get('httpMethod', 'POST')
    
    print(f"HTTP Method: {http_method}")
    
    if http_method == 'OPTIONS':
        print("Handling OPTIONS request")
        return create_response(200, {})
    
    # Handle GET requests (health check only)
    if http_method == 'GET':
        path = event.get('rawPath', event.get('path', '/'))
        if path == '/health':
            return create_response(200, {
                "status": "healthy",
                "agent_runtime_arn": AGENT_RUNTIME_ARN,
                "memory_id": MEMORY_ID
            })
        # Return error for other GET requests
        return create_response(400, {"error": "Only POST requests are supported"})
    
    try:
        # Parse request body
        body_str = event.get("body", "{}")
        print(f"Raw body: {body_str}")
        
        # Handle base64 encoded body
        if event.get("isBase64Encoded", False):
            import base64
            body_str = base64.b64decode(body_str).decode('utf-8')
            print(f"Decoded body: {body_str}")
        
        body = json.loads(body_str)
        message = body.get("message", "")
        session_id = body.get("session_id", "default-session")
        
        print(f"Parsed - Message: {message}, Session: {session_id}")
        
        if not message:
            print("ERROR: Missing message in request")
            return create_response(400, {"error": "Missing message"})
        
        print(f"Invoking AgentCore Runtime: {AGENT_RUNTIME_ARN}")
        print(f"Session: {session_id}, Message: {message}")
        
        # Generate trace ID
        trace_id = str(uuid.uuid4())[:8]
        
        # Prepare payload as JSON bytes
        # AgentCore entrypoint expects 'input' and 'session_id' keys
        # Note: Using both sessionId and session_id for compatibility
        payload = json.dumps({
            "input": message,
            "sessionId": session_id,
            "session_id": session_id
        }).encode('utf-8')
        
        print(f"Payload: {payload.decode('utf-8')}")
        
        # Invoke AgentCore Runtime
        response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            traceId=trace_id,
            payload=payload
        )
        
        # Parse response
        result = ""
        
        # AgentCore returns response in 'response' field
        if 'response' in response:
            response_data = response['response']
            
            # Check if it's a StreamingBody object
            if hasattr(response_data, 'read'):
                # It's a streaming body, read it
                result = response_data.read().decode('utf-8')
                # Try to parse as JSON in case it's JSON-encoded
                try:
                    result = json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    pass  # It's not JSON, use as-is
            elif isinstance(response_data, list):
                # It's a list of strings
                result = ''.join(response_data)
            elif isinstance(response_data, str):
                # It's already a string
                result = response_data
            else:
                # Convert to string as fallback
                result = str(response_data)
        # Fallback: try to read from body as event stream
        elif 'body' in response:
            event_stream = response['body']
            try:
                for event_data in event_stream:
                    # Handle different event types
                    if 'chunk' in event_data:
                        chunk_bytes = event_data['chunk'].get('bytes', b'')
                        if chunk_bytes:
                            result += chunk_bytes.decode('utf-8')
                    elif 'internalServerException' in event_data:
                        raise Exception(f"Internal server error: {event_data['internalServerException']}")
                    elif 'throttlingException' in event_data:
                        raise Exception(f"Throttling error: {event_data['throttlingException']}")
            except Exception as e:
                print(f"Error reading event stream: {e}")
                # Try reading body directly
                if hasattr(event_stream, 'read'):
                    result = event_stream.read().decode('utf-8')
        
        print(f"Response received: {len(result)} characters")
        print(f"Response keys: {list(response.keys())}")
        print(f"Full response structure: {type(response)}")
        print(f"Result content: {result[:200] if result else 'EMPTY'}")  # First 200 chars
        
        if not result:
            print("WARNING: Empty result from AgentCore")
            print(f"Raw response['response']: {response.get('response', 'NOT FOUND')}")
        
        # Clean up the response
        cleaned_result = result
        
        # Remove <thinking> tags and their content
        import re
        cleaned_result = re.sub(r'<thinking>.*?</thinking>\s*', '', cleaned_result, flags=re.DOTALL)
        
        # Remove any leading/trailing whitespace
        cleaned_result = cleaned_result.strip()
        
        print(f"Cleaned result: {len(cleaned_result)} characters")
        
        final_response = create_response(200, {
            "response": cleaned_result if cleaned_result else "No response from agent",
            "session_id": session_id
        })
        
        print(f"Returning response with status: {final_response['statusCode']}")
        print(f"Response body length: {len(final_response['body'])}")
        
        return final_response
    
    except Exception as e:
        print(f"Error invoking AgentCore Runtime: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {"error": str(e)})


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create Lambda Function URL response.
    
    Args:
        status_code: HTTP status code
        body: Response body
        
    Returns:
        Lambda Function URL response
    """
    # Lambda Function URL handles CORS automatically, so we only need Content-Type
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
        "isBase64Encoded": False,
    }
