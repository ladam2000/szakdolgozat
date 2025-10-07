# Virtual Travel Assistant

A multi-agent travel planning system using the **agents-as-tools** pattern with Strands Agent and AWS AgentCore.

## Architecture

This system implements the agents-as-tools pattern where:
- **Orchestrator Agent**: Coordinates travel planning and delegates to specialized agents
- **Specialized Agents as Tools**: 
  - Flight Booking Agent - Searches and recommends flights
  - Hotel Booking Agent - Finds and compares hotels
  - Activities Agent - Suggests attractions and itineraries

All agents use **Claude Sonnet 4.5** (`eu.anthropic.claude-sonnet-4-5-20250929-v1:0`) for powerful, intelligent responses.

## Key Features

- **Agents as Tools Pattern**: Specialized agents exposed as tool calls to the orchestrator
- **AgentCore Memory**: Conversation context and session management
- **Guardrails**: Content filtering and safety controls
- **Observability**: Full tracing and monitoring
- **Infrastructure**: CloudFormation with Lambda, S3, CloudFront, API Gateway

## Components

- `agentcore/agent.py` - Orchestrator and specialized agents implementation
- `agentcore/app.py` - AgentCore service with FastAPI
- `lambda/` - Lambda proxy function
- `frontend/` - Static web interface
- `infrastructure/` - CloudFormation templates

## How It Works

1. User asks: "Plan a trip to Paris for 3 days"
2. Orchestrator analyzes the request
3. Orchestrator calls specialized agents as tools:
   - `flight_booking_tool("flights to Paris")` 
   - `hotel_booking_tool("hotels in Paris for 3 nights")`
   - `activities_tool("things to do in Paris")`
4. Orchestrator synthesizes responses into a complete travel plan

## Setup

1. Deploy infrastructure: `aws cloudformation deploy --template-file infrastructure/template.yaml --stack-name travel-assistant --capabilities CAPABILITY_IAM`
2. Build AgentCore: Use CodeBuild with `buildspec.yml`
3. Deploy frontend to S3 bucket

## Environment Variables

- `AWS_REGION` - AWS region (default: eu-central-1)
- `BEDROCK_MODEL_ID` - Bedrock model for all agents (default: eu.anthropic.claude-sonnet-4-5-20250929-v1:0)
