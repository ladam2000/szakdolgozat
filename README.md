# Virtual Travel Assistant

AI-powered travel planning assistant built with AWS Bedrock AgentCore, Cognito authentication, and Tavily search.

## Features

- 🔐 **Secure Authentication** - AWS Cognito user management
- 💬 **Conversational AI** - Natural language travel planning
- 🔍 **Real-time Search** - Live flight, hotel, and activity information via Tavily
- 💾 **Memory** - Remembers conversation context within sessions
- 🌐 **Modern UI** - Clean, responsive interface with markdown support

## Architecture

```
┌─────────────┐
│   Frontend  │ (S3 + CloudFront)
│  React SPA  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Lambda    │ (Function URL)
│   Handler   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  AgentCore  │ (Bedrock)
│   Runtime   │
└──────┬──────┘
       │
       ├─► Memory (AgentCore Memory)
       └─► Search (Tavily API)
```

## Components

### Frontend (`frontend/`)
- **index.html** - Main application page
- **app.js** - Application logic and API integration
- **auth.js** - Cognito authentication handling
- **styles.css** - UI styling

### Lambda Handler (`lambda/handler.py`)
- Receives requests from frontend
- Invokes AgentCore runtime
- Handles authentication and CORS

### AgentCore Runtime (`agentcore/runtime_agent_main.py`)
- Strands-based agent with memory
- Tavily search integration
- Conversation history management

### Infrastructure (`infrastructure/`)
- CloudFormation templates
- AWS resource definitions

## Deployment

### Prerequisites
- AWS CLI configured
- AWS account with appropriate permissions
- Tavily API key (for search functionality)

### Deploy

```bash
# Deploy frontend and Lambda
./deploy-frontend.sh
```

This will:
1. Update Lambda function code
2. Upload frontend files to S3
3. Invalidate CloudFront cache

### Environment Variables

**Lambda:**
- `AGENT_RUNTIME_ARN` - AgentCore runtime ARN

**AgentCore Runtime:**
- `TAVILY_API_KEY` - Tavily search API key

## Configuration

### Cognito
- User Pool: `eu-central-1_uKRxqbEX5`
- Client ID: `6kmkgdkls92qfthrbglelcsdjm`
- Domain: `travel-assistant.auth.eu-central-1.amazoncognito.com`

### AgentCore
- Memory ID: `memory_rllrl-lfg7zBH6MH`
- Region: `eu-central-1`
- Model: `eu.amazon.nova-micro-v1:0`

### Frontend
- CloudFront: `https://dbziso5b0wjgl.cloudfront.net`
- Lambda URL: `https://fbiwuqkkwu6yqutfmr25anrnuy0hwfnl.lambda-url.eu-central-1.on.aws/`

## Usage

1. Navigate to https://dbziso5b0wjgl.cloudfront.net
2. Sign in with Cognito credentials
3. Ask about flights, hotels, or activities
4. Agent will search and provide recommendations

### Example Queries

- "I want to fly from Barcelona to Athens, December 5-8"
- "What hotels are near Omonia Square in Athens?"
- "What can I do in Athens in December?"

## Development

### Local Testing

Frontend can be tested locally by opening `frontend/index.html` in a browser, but API calls will go to production Lambda.

### Code Structure

```
.
├── frontend/           # Frontend application
│   ├── index.html
│   ├── app.js
│   ├── auth.js
│   └── styles.css
├── lambda/            # Lambda handler
│   └── handler.py
├── agentcore/         # AgentCore runtime
│   └── runtime_agent_main.py
├── infrastructure/    # CloudFormation templates
└── deploy-frontend.sh # Deployment script
```

## Features in Detail

### Memory Management
- Uses AgentCore Memory for conversation persistence
- Maintains context within sessions
- Stores last 5 conversation turns

### Search Integration
- Tavily API for real-time information
- Searches flights, hotels, and activities
- Returns formatted results with links

### Authentication
- AWS Cognito for user management
- OAuth 2.0 / OIDC flow
- Secure token-based authentication

## Troubleshooting

### Links Not Clickable
- Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
- Clear browser cache

### Authentication Issues
- Check Cognito configuration
- Verify redirect URIs match

### Search Not Working
- Verify TAVILY_API_KEY is set in AgentCore runtime
- Check CloudWatch logs for errors

## License

MIT

## Support

For issues or questions, check CloudWatch logs:
- Lambda: `/aws/lambda/TravelAgentLambda`
- AgentCore: Check Bedrock AgentCore logs
