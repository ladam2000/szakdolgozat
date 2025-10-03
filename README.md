# Virtual Travel Assistant

A multi-agent travel planning system built with Strands Agent and AWS AgentCore.

## Architecture

- **Multi-Agent System**: Specialized agents for flights, hotels, and activities
- **AgentCore Memory**: Short-term memory for conversation context
- **Guardrails**: Content filtering and safety controls
- **Observability**: Full tracing and monitoring
- **Infrastructure**: CloudFormation with Lambda, S3, CloudFront, API Gateway

## Components

- `agentcore/` - AgentCore service with Strands agents
- `lambda/` - Lambda proxy function
- `frontend/` - Static web interface
- `infrastructure/` - CloudFormation templates

## Setup

1. Deploy infrastructure: `aws cloudformation deploy --template-file infrastructure/template.yaml --stack-name travel-assistant --capabilities CAPABILITY_IAM`
2. Build AgentCore: Use CodeBuild with `buildspec.yml`
3. Deploy frontend to S3 bucket

## Environment Variables

- `AWS_REGION` - AWS region (default: eu-central-1)
- `BEDROCK_MODEL_ID` - Bedrock model (default: us.amazon.nova-micro-v1:0)
