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


def lambda_handler(event: Dict[str, Any], context: Any):
    """Handle API Gateway requests and invoke AgentCore Runtime.
    
    Based on: https://github.com/marklaszlo9/agentcore-sample/blob/main/lambda/agentcore_proxy.py
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    # Handle CORS preflight
    request_context = event.get('requestContext', {})
    http_method = request_context.get('http', {}).get('method', event.get('httpMethod', ''))
    
    if http_method == 'OPTIONS':
        return create_response(200, {})
    
    try:
        # Parse request
        body = json.loads(event.get("body", "{}"))
        message = body.get("message", "")
        session_id = body.get("session_id", "default-session")
        
        if not message:
            return create_response(400, {"error": "Missing message"})
        
        print(f"Invoking AgentCore Runtime: {AGENT_RUNTIME_ARN}")
        print(f"Session: {session_id}, Message: {message}")
        
        # Generate trace ID
        trace_id = str(uuid.uuid4())[:8]
        
        # Prepare payload as JSON bytes
        payload = json.dumps({
            "inputText": message,
            "sessionId": session_id
        }).encode('utf-8')
        
        # Invoke AgentCore Runtime
        response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            traceId=trace_id,
            payload=payload
        )
        
        # Parse response - handle streaming
        result = ""
        
        # The response body is an EventStream
        event_stream = response.get('body')
        if event_stream:
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
        
        print(f"Response received: {len(result)} characters")
        
        return create_response(200, {
            "response": result,
            "session_id": session_id
        })
    
    except Exception as e:
        print(f"Error invoking AgentCore Runtime: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {"error": str(e)})


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create API Gateway response.
    
    Args:
        status_code: HTTP status code
        body: Response body
        
    Returns:
        API Gateway response
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body),
    }
