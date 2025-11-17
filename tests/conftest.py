"""Pytest configuration and shared fixtures."""

import pytest
import json
import os
import sys
from unittest.mock import Mock, MagicMock, patch

# Mock boto3 before importing handler to avoid AWS credential requirements
sys.modules['boto3'] = MagicMock()

# Add lambda directory to path so we can import handler
lambda_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lambda'))
if lambda_dir not in sys.path:
    sys.path.insert(0, lambda_dir)


@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock AgentCore client."""
    client = Mock()
    
    # Create a proper mock response object
    mock_response = Mock()
    mock_response.read = Mock(return_value=b'I can help you plan your trip. Where would you like to go?')
    
    client.invoke_agent_runtime = Mock(return_value={
        'response': mock_response
    })
    return client


@pytest.fixture
def mock_tavily_client():
    """Mock Tavily search client."""
    client = Mock()
    client.search = Mock(return_value={
        'answer': 'Found 3 flights from Barcelona to Athens',
        'results': [
            {
                'title': 'Ryanair Barcelona to Athens',
                'url': 'https://example.com/flight1',
                'content': 'Direct flight for €89'
            }
        ]
    })
    return client


@pytest.fixture
def mock_memory_client():
    """Mock AgentCore memory client."""
    client = Mock()
    client.get_last_k_turns = Mock(return_value=[])
    client.create_event = Mock(return_value={'success': True})
    return client


@pytest.fixture
def sample_lambda_event():
    """Sample Lambda Function URL event."""
    return {
        'requestContext': {
            'http': {
                'method': 'POST'
            }
        },
        'body': json.dumps({
            'message': 'I want to fly from Barcelona to Athens',
            'session_id': 'test-session-123'
        }),
        'isBase64Encoded': False
    }


@pytest.fixture
def sample_lambda_context():
    """Sample Lambda context."""
    context = Mock()
    context.function_name = 'TravelAgentLambda'
    context.memory_limit_in_mb = 512
    context.invoked_function_arn = 'arn:aws:lambda:eu-central-1:123456789012:function:TravelAgentLambda'
    return context


@pytest.fixture
def env_vars():
    """Set up environment variables for testing."""
    original_env = os.environ.copy()
    
    os.environ['AGENT_RUNTIME_ARN'] = 'arn:aws:bedrock-agentcore:eu-central-1:123456789012:runtime/test'
    os.environ['MEMORY_ID'] = 'test-memory-id'
    os.environ['BRANCH_NAME'] = 'main'
    os.environ['REGION'] = 'eu-central-1'
    os.environ['MODEL_ID'] = 'eu.amazon.nova-micro-v1:0'
    os.environ['TAVILY_API_KEY'] = 'test-tavily-key'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
