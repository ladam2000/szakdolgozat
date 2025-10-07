# Virtual Travel Assistant

A multi-agent travel planning system using the **agents-as-tools** pattern with AWS Strands Agent and AgentCore.

## Architecture

This system implements the agents-as-tools pattern:

- **Orchestrator Agent**: Coordinates travel planning and delegates to specialized agents
- **Specialized Agents as Tools**:
  - Flight Booking Agent - Searches and recommends flights
  - Hotel Booking Agent - Finds and compares hotels
  - Activities Agent - Suggests attractions and itineraries

All agents use **Amazon Nova Micro** (`eu.amazon.nova-micro-v1:0`) for fast, cost-effective execution.

## Project Structure

```
├── agentcore/
│   ├── runtime_agent_main.py    # Orchestrator + specialized agents
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile              # Container configuration
├── lambda/
│   ├── handler.py              # Lambda proxy function
│   ├── requirements.txt        # Lambda dependencies
│   └── template.yaml          # Lambda CloudFormation
├── frontend/
│   ├── index.html             # Web interface
│   ├── app.js                 # Frontend logic
│   ├── styles.css             # Styling
│   └── auth.js                # AWS Cognito authentication
├── infrastructure/
│   └── template.yaml          # Main CloudFormation template
├── buildspec.yml              # CodeBuild configuration for AgentCore
├── deploy-frontend.sh         # Deployment script
└── README.md                  # This file
```

## How It Works

1. User asks: "Plan a trip to Paris for 3 days"
2. Orchestrator analyzes the request
3. Orchestrator calls specialized agents as tools:
   - `flight_booking_tool("flights to Paris")`
   - `hotel_booking_tool("hotels in Paris for 3 nights")`
   - `activities_tool("things to do in Paris")`
4. Orchestrator synthesizes responses into a complete travel plan

## Deployment

### Prerequisites

- AWS CLI configured
- AgentCore runtime deployed
- CloudFormation stack deployed

### Deploy

```bash
./deploy-frontend.sh
```

This script will:
1. Update Lambda function code
2. Upload frontend files to S3
3. Invalidate CloudFront cache
4. Display the application URL

## Configuration

- **Model**: `eu.amazon.nova-micro-v1:0` (in `agentcore/runtime_agent_main.py`)
- **Region**: `eu-central-1` (in deployment scripts)
- **Authentication**: AWS Cognito (in `frontend/auth.js`)

## Features

- Multi-agent orchestration with specialized travel agents
- Real-time conversation with session management
- Markdown formatting for travel plans
- User authentication with AWS Cognito
- Responsive web interface
- CORS-enabled Lambda Function URL integration
