# Architecture Overview

## System Design

The Virtual Travel Assistant is a multi-agent system built on AWS with the following components:

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   CloudFront    │ (CDN)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   S3 Bucket     │ (Static Frontend)
└─────────────────┘

       │ API Calls
       ▼
┌─────────────────┐
│  API Gateway    │ (HTTP API)
└──────┬──────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Lambda (AgentCoreProxyFunction)    │
│  ┌───────────────────────────────┐  │
│  │   AgentCore Runtime           │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Coordinator Agent      │  │  │
│  │  │  ┌──────────────────┐   │  │  │
│  │  │  │ Flight Agent     │   │  │  │
│  │  │  │ Hotel Agent      │   │  │  │
│  │  │  │ Activity Agent   │   │  │  │
│  │  │  └──────────────────┘   │  │  │
│  │  └─────────────────────────┘  │  │
│  │                                │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Memory Manager         │  │  │
│  │  │  (Short-term)           │  │  │
│  │  └─────────────────────────┘  │  │
│  │                                │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Guardrails Manager     │  │  │
│  │  └─────────────────────────┘  │  │
│  │                                │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Observability Manager  │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │
               ▼
       ┌───────────────┐
       │ Amazon Bedrock│
       │ (Claude 3)    │
       └───────────────┘
```

## Components

### 1. Frontend (S3 + CloudFront)

- **Technology**: Vanilla JavaScript, HTML, CSS
- **Hosting**: S3 bucket with CloudFront CDN
- **Features**:
  - Chat interface
  - Session management
  - Real-time messaging
  - Responsive design

### 2. API Gateway

- **Type**: HTTP API (v2)
- **Routes**:
  - `GET /health` - Health check
  - `POST /chat` - Send message
  - `POST /reset` - Reset session
- **Features**:
  - CORS enabled
  - Lambda proxy integration

### 3. Lambda Function (AgentCoreProxyFunction)

- **Runtime**: Python 3.11
- **Memory**: 1024 MB
- **Timeout**: 300 seconds
- **Purpose**: Host AgentCore FastAPI application via Mangum adapter
- **Package**: Contains AgentCore service + all dependencies

### 4. AgentCore Runtime

#### Multi-Agent System

**Coordinator Agent**
- Orchestrates specialized agents
- Routes requests based on intent
- Combines responses into coherent plans

**Flight Agent**
- Searches flights
- Provides flight options
- Handles booking queries

**Hotel Agent**
- Searches accommodations
- Provides hotel information
- Handles booking queries

**Activity Agent**
- Searches activities and attractions
- Provides recommendations
- Handles activity planning

#### Memory Manager

- **Type**: Short-term memory
- **Storage**: In-memory (Lambda execution context)
- **Capacity**: Last 20 messages per session
- **Features**:
  - Session-based isolation
  - Automatic trimming
  - Context window generation

#### Guardrails Manager

- **Integration**: Amazon Bedrock Guardrails
- **Checks**: Input and output filtering
- **Features**:
  - Content safety
  - PII detection
  - Topic filtering
  - Graceful degradation

#### Observability Manager

- **Tracing**: Request-level traces
- **Logging**: Structured logs to CloudWatch
- **Metrics**:
  - Response times
  - Token usage
  - Error rates
  - Agent invocations

### 5. Amazon Bedrock

- **Model**: Claude 3 Sonnet
- **Purpose**: LLM inference for agents
- **Features**:
  - Tool calling
  - Streaming responses
  - Guardrails integration

## Data Flow

### Chat Request Flow

1. User sends message from browser
2. CloudFront routes to S3 for static assets
3. JavaScript makes API call to API Gateway
4. API Gateway invokes Lambda function
5. Lambda:
   - Retrieves conversation history from memory
   - Applies input guardrails
   - Builds context with history
   - Invokes coordinator agent
   - Coordinator delegates to specialized agents
   - Agents call Bedrock for inference
   - Agents use tools to search data
   - Applies output guardrails
   - Stores messages in memory
   - Logs trace information
6. Response returned through API Gateway
7. Frontend displays response

### Memory Management

- Each session has isolated memory
- Messages stored with timestamps
- Automatic cleanup after max messages
- Context window built from recent messages

### Guardrails Flow

1. Input text checked before processing
2. If blocked, return error immediately
3. Output text checked after generation
4. If blocked, return safe fallback message

### Observability Flow

1. Trace created for each request
2. Logs added at key points
3. Metrics collected
4. Trace written to CloudWatch
5. Available for analysis and debugging

## Security

### IAM Roles

- **Lambda Execution Role**:
  - Bedrock model invocation
  - Guardrails application
  - CloudWatch logging

### Network Security

- CloudFront with HTTPS only
- API Gateway with CORS
- S3 bucket not publicly accessible
- Origin Access Control for CloudFront

### Data Security

- No persistent storage of conversations
- Memory cleared on Lambda cold start
- Session IDs client-generated
- No PII stored

## Scalability

### Lambda Scaling

- Automatic scaling based on requests
- Concurrent execution limit: 1000 (default)
- Cold start optimization with minimal dependencies

### Memory Scaling

- In-memory storage per Lambda instance
- Sessions distributed across instances
- No shared state between instances

### Cost Optimization

- Lambda charged per request
- Bedrock charged per token
- S3 and CloudFront minimal costs
- No always-on infrastructure

## Best Practices Implemented

1. **Separation of Concerns**: Frontend, API, and agents separated
2. **Stateless Design**: Lambda functions are stateless
3. **Error Handling**: Graceful degradation at all levels
4. **Observability**: Comprehensive logging and tracing
5. **Security**: IAM roles, HTTPS, guardrails
6. **Scalability**: Serverless architecture
7. **Cost Efficiency**: Pay-per-use model
8. **Maintainability**: Modular code structure

## Future Enhancements

- Persistent memory with DynamoDB
- User authentication with Cognito
- Real-time updates with WebSockets
- Advanced analytics with CloudWatch Insights
- Multi-region deployment
- A/B testing capabilities
