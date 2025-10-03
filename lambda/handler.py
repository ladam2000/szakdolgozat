"""Lambda proxy function that calls Bedrock AgentCore."""

import json
import os
import boto3
from typing import Dict, Any

# Initialize Bedrock Agent Runtime client
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Get Agent configuration from environment
AGENT_ID = os.environ.get("AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle API Gateway requests and invoke Bedrock Agent.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        # Parse request
        body = json.loads(event.get("body", "{}"))
        message = body.get("message", "")
        session_id = body.get("session_id", "default-session")
        
        if not message:
            return create_response(400, {"error": "Missing message"})
        
        print(f"Invoking agent {AGENT_ID} with message: {message}")
        
        # Invoke Bedrock Agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=message
        )
        
        # Collect response chunks
        result = ""
        for event_chunk in response.get('completion', []):
            if 'chunk' in event_chunk:
                chunk_data = event_chunk['chunk']
                if 'bytes' in chunk_data:
                    result += chunk_data['bytes'].decode('utf-8')
        
        return create_response(200, {
            "response": result,
            "session_id": session_id
        })
    
    except Exception as e:
        print(f"Error invoking agent: {str(e)}")
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
