# Virtual Travel Assistant

AI-powered travel planning assistant that helps users plan trips with real-time flight, hotel, and activity recommendations.

## Overview

This application combines AWS Bedrock AgentCore for conversational AI, AWS Cognito for authentication, and Tavily API for real-time travel information search. The agent maintains conversation context and provides personalized travel recommendations.

## Features

- 🔐 **Secure Authentication** - AWS Cognito user pool with OAuth 2.0
- 💬 **Conversational AI** - Natural language understanding powered by Amazon Nova
- 🔍 **Real-time Search** - Live travel information via Tavily API
- 💾 **Session Memory** - Maintains conversation context within sessions
- 🌐 **Responsive UI** - Clean interface with markdown rendering and clickable links
- ✈️ **Travel Planning** - Flights, hotels, and activities in one conversation

## Architecture

```
┌──────────────────┐
│   CloudFront     │ ← https://dbziso5b0wjgl.cloudfront.net
│   Distribution   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   S3 Bucket      │
│   Frontend Files │
└──────────────────┘

┌──────────────────┐
│   AWS Cognito    │
│   User Pool      │
└──────────────────┘

┌──────────────────┐
│   Lambda         │ ← Function URL
│   Handler        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   AgentCore      │
│   Runtime        │
└────────┬─────────┘
         │
         ├─► AgentCore Memory (conversation history)
         ├─► Amazon Nova Micro (LLM)
         └─► Tavily API (search)
```

## Technology Stack

### Frontend
- Vanilla JavaScript (ES6 modules)
- OIDC Client for Cognito authentication
- Markdown rendering for rich responses
- Hosted on S3 + CloudFront

### Backend
- **Lambda Handler** (Python 3.11)
  - Receives requests from frontend
  - Invokes AgentCore runtime
  - Handles authentication validation

- **AgentCore Runtime** (Python 3.11)
  - Strands framework for agent orchestration
  - Amazon Nova Micro model
  - AgentCore Memory for conversation persistence
  - Tavily search tool integration

### AWS Services
- **Bedrock AgentCore** - Agent runtime and memory
- **Lambda** - Serverless compute
- **Cognito** - User authentication
- **S3** - Static file hosting
- **CloudFront** - CDN and HTTPS
- **CloudFormation** - Infrastructure as code

## Project Structure

```
.
├── frontend/
│   ├── index.html              # Main application page
│   ├── app.js                  # Application logic and API calls
│   ├── auth.js                 # Cognito authentication
│   └── styles.css              # UI styling
│
├── lambda/
│   └── handler.py              # Lambda function handler
│
├── agentcore/
│   └── runtime_agent_main.py   # AgentCore runtime with Strands
│
├── infrastructure/
│   └── template.yaml           # CloudFormation template
│
├── deploy-frontend.sh          # Deployment script
├── buildspec.yml              # AWS CodeBuild configuration
└── README.md                  # This file
```

## Setup and Deployment

### Prerequisites

1. **AWS Account** with permissions for:
   - Lambda
   - Bedrock AgentCore
   - S3
   - CloudFront
   - Cognito
   - CloudFormation

2. **AWS CLI** configured with credentials

3. **Tavily API Key** - Get from [tavily.com](https://tavily.com)

### Configuration

#### 1. Cognito Setup
The application uses an existing Cognito User Pool:
- **User Pool ID**: `eu-central-1_uKRxqbEX5`
- **Client ID**: `6kmkgdkls92qfthrbglelcsdjm`
- **Domain**: `travel-assistant.auth.eu-central-1.amazoncognito.com`
- **Region**: `eu-central-1`

#### 2. AgentCore Runtime
- **Memory ID**: `memory_rllrl-lfg7zBH6MH`
- **Runtime ID**: `hosted_agent_rkxzc-Yq2wttGAF4`
- **Model**: `eu.amazon.nova-micro-v1:0`
- **Region**: `eu-central-1`

#### 3. Environment Variables

**Lambda Function:**
```bash
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:eu-central-1:206631439304:runtime/hosted_agent_rkxzc-Yq2wttGAF4
```

**AgentCore Runtime:**
```bash
TAVILY_API_KEY=your_tavily_api_key_here
```

### Deployment

#### Deploy Frontend and Lambda

```bash
# Make script executable
chmod +x deploy-frontend.sh

# Deploy
./deploy-frontend.sh
```

This script will:
1. Package and update Lambda function code
2. Upload frontend files to S3
3. Invalidate CloudFront cache
4. Wait for cache invalidation to complete

#### Deploy AgentCore Runtime

```bash
# Package runtime
cd agentcore
zip runtime.zip runtime_agent_main.py

# Update runtime
aws bedrock-agentcore update-runtime \
  --runtime-id hosted_agent_rkxzc-Yq2wttGAF4 \
  --runtime-code fileb://runtime.zip \
  --region eu-central-1
```

## Usage

### Access the Application

1. Navigate to: https://dbziso5b0wjgl.cloudfront.net
2. Click "Sign In with Cognito"
3. Enter your credentials
4. Start planning your trip!

### Example Conversations

**Flight Search:**
```
User: I want to fly from Barcelona to Athens, December 5-8
Agent: [Provides flight options with prices and links]
```

**Hotel Recommendations:**
```
User: What hotels are near Omonia Square?
Agent: [Lists hotels with prices, ratings, and booking links]
```

**Activities:**
```
User: What can I do in Athens in December?
Agent: [Suggests activities, attractions, and events]
```

**Follow-up Questions:**
```
User: Any Ryanair flights available?
Agent: [Searches specifically for Ryanair flights on the same route]
```

The agent remembers your travel details (origin, destination, dates) throughout the conversation, so you don't need to repeat them.

## Features in Detail

### Conversation Memory

- Uses AgentCore Memory service for persistence
- Stores last 5 conversation turns per session
- Maintains context across multiple questions
- Session-based isolation (each user has their own history)

### Search Integration

The agent uses Tavily API to search for:
- **Flights**: Real-time prices and availability
- **Hotels**: Booking options with ratings and prices
- **Activities**: Things to do, attractions, events
- **General Travel Info**: Weather, transportation, tips

Search results include:
- Direct links to booking sites
- Prices and ratings
- Descriptions and details
- Source attribution

### Authentication Flow

1. User clicks "Sign In"
2. Redirected to Cognito hosted UI
3. User authenticates
4. Redirected back with authorization code
5. OIDC client exchanges code for tokens
6. Access token used for API requests

### UI Features

- **Markdown Rendering**: Bold, italic, lists, headings
- **Clickable Links**: All URLs are clickable and open in new tabs
- **Message Types**: User, assistant, and system messages
- **Loading Indicators**: Shows when agent is thinking
- **Responsive Design**: Works on desktop and mobile
- **Auto-scroll**: Automatically scrolls to latest message

## API Endpoints

### Lambda Function URL
`https://fbiwuqkkwu6yqutfmr25anrnuy0hwfnl.lambda-url.eu-central-1.on.aws/`

#### POST /
Send a message to the agent.

**Request:**
```json
{
  "message": "I want to fly from Barcelona to Athens",
  "session_id": "session_1234567890_abc123"
}
```

**Response:**
```json
{
  "response": "Here are some flight options...",
  "session_id": "session_1234567890_abc123"
}
```

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "agent_runtime_arn": "arn:aws:bedrock-agentcore:...",
  "memory_id": "memory_rllrl-lfg7zBH6MH"
}
```

## Development

### Local Testing

The frontend can be opened locally, but it will connect to production AWS services:

```bash
# Open in browser
open frontend/index.html
```

### Viewing Logs

**Lambda Logs:**
```bash
aws logs tail /aws/lambda/TravelAgentLambda --follow --region eu-central-1
```

**AgentCore Logs:**
Check CloudWatch Logs for Bedrock AgentCore runtime logs.

### Making Changes

1. **Frontend Changes:**
   - Edit files in `frontend/`
   - Run `./deploy-frontend.sh`
   - Hard refresh browser (Cmd+Shift+R)

2. **Lambda Changes:**
   - Edit `lambda/handler.py`
   - Run `./deploy-frontend.sh`

3. **AgentCore Runtime Changes:**
   - Edit `agentcore/runtime_agent_main.py`
   - Package and deploy runtime (see deployment section)

## Troubleshooting

### Links Not Clickable
**Problem**: Links appear as plain text  
**Solution**: Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R) to clear cache

### Authentication Errors
**Problem**: Can't sign in or redirects fail  
**Solution**: 
- Verify Cognito configuration
- Check redirect URIs match CloudFront URL
- Clear browser cookies and try again

### Agent Not Responding
**Problem**: Messages sent but no response  
**Solution**:
- Check Lambda logs for errors
- Verify AgentCore runtime is deployed
- Check TAVILY_API_KEY is set

### Search Not Working
**Problem**: Agent can't find travel information  
**Solution**:
- Verify TAVILY_API_KEY environment variable
- Check Tavily API quota/limits
- Review AgentCore runtime logs

### Memory Not Working
**Problem**: Agent doesn't remember previous messages  
**Solution**:
- Check AgentCore Memory ID is correct
- Verify IAM permissions for memory access
- Check session_id is being passed correctly

## Cost Considerations

- **Bedrock AgentCore**: Pay per invocation and memory storage
- **Lambda**: Free tier covers most development usage
- **S3**: Minimal storage costs
- **CloudFront**: Free tier covers moderate traffic
- **Cognito**: Free tier covers up to 50,000 MAUs
- **Tavily API**: Check pricing at tavily.com

## Security

- All traffic uses HTTPS
- Authentication via AWS Cognito
- Access tokens validated on each request
- No sensitive data stored in frontend
- Session IDs are randomly generated
- Links open in new tabs with `noopener noreferrer`

## License

MIT

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review this README
3. Check AWS service status
4. Verify all environment variables are set

## Future Enhancements

- [ ] Booking integration
- [ ] Multi-language support
- [ ] Trip itinerary export
- [ ] Price alerts
- [ ] User preferences storage
- [ ] Mobile app
