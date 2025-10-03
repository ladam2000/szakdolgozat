# Deployment Guide - Bedrock AgentCore

## Architecture

This solution uses **AWS Bedrock AgentCore** to host a custom Strands agent in a Docker container.

**Components:**
1. **AgentCore** - AWS managed service that runs your Docker container with the agent
2. **Lambda** - Proxy that calls `bedrock-agent-runtime.invoke_agent()`
3. **ECR** - Stores the Docker image with your agent code
4. **API Gateway** - REST API for frontend
5. **CloudFront + S3** - Static frontend hosting

## Prerequisites

- AWS CLI configured with credentials
- AWS account with Bedrock access in eu-central-1
- Docker installed locally (for testing)
- Bedrock AgentCore enabled in your account

## Deployment Steps

### 1. Deploy Infrastructure

```bash
chmod +x deploy.sh
./deploy.sh
```

This creates:
- S3 buckets (frontend + artifacts)
- ECR repository
- Lambda function
- API Gateway
- CloudFront distribution
- CodeBuild project

### 2. Build and Push Docker Image

```bash
# Get CodeBuild project name
CODEBUILD_PROJECT=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant \
  --region eu-central-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CodeBuildProject`].OutputValue' \
  --output text)

# Start build
aws codebuild start-build \
  --project-name $CODEBUILD_PROJECT \
  --region eu-central-1
```

This will build the Docker image and push it to ECR.

### 3. Create Bedrock Agent with AgentCore

After the build completes, get the ECR image URI:

```bash
ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant \
  --region eu-central-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ECRRepository`].OutputValue' \
  --output text)

echo "Image URI: $ECR_URI:latest"
```

**In AWS Console:**

1. Go to **Amazon Bedrock** → **Agents**
2. Click **Create Agent**
3. Choose **Custom agent with AgentCore**
4. Configure:
   - **Agent name**: `travel-assistant`
   - **Model**: Claude 3 Sonnet
   - **Container image URI**: `<ECR_URI>:latest`
   - **IAM role**: Use the `AgentCoreRoleArn` from CloudFormation outputs
5. Create agent and note the **Agent ID** and **Alias ID**

### 4. Deploy Lambda Function

```bash
cd lambda

AGENT_ID="<your-agent-id>"
AGENT_ALIAS_ID="<your-agent-alias-id>"

# Deploy Lambda with SAM
chmod +x deploy-lambda.sh
./deploy-lambda.sh $AGENT_ID $AGENT_ALIAS_ID

cd ..
```

Get the API URL:

```bash
API_URL=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant-lambda \
  --region eu-central-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

echo "API URL: $API_URL"
```

### 5. Deploy Frontend

```bash
# Get API URL from Lambda stack
API_URL=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant-lambda \
  --region eu-central-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

# Get frontend bucket from main stack
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant \
  --region eu-central-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' \
  --output text)

# Update frontend config
sed -i "s|YOUR_API_GATEWAY_URL|$API_URL|g" frontend/app.js

# Deploy
aws s3 sync frontend/ s3://$FRONTEND_BUCKET/ --region eu-central-1
```

### 6. Access Application

```bash
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant \
  --region eu-central-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text)

echo "Application URL: $CLOUDFRONT_URL"
```

## Testing

### Test Agent Locally (Optional)

```bash
cd agentcore
docker build -t travel-agent .
docker run -p 8000:8000 \
  -e AWS_REGION=eu-central-1 \
  -e BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0 \
  travel-agent

# Test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to plan a trip to Paris", "session_id": "test"}'
```

### Test Lambda

```bash
aws lambda invoke \
  --function-name $LAMBDA_FUNCTION \
  --payload '{"body": "{\"message\": \"Hello\", \"session_id\": \"test\"}"}' \
  --region eu-central-1 \
  response.json

cat response.json
```

## Updating the Agent

To update agent code:

1. Modify code in `agentcore/`
2. Run CodeBuild to rebuild image
3. In Bedrock console, update agent to use new image tag
4. Test changes

## Monitoring

### CloudWatch Logs

```bash
# AgentCore logs
aws logs tail /aws/bedrock/agents/<agent-id> --follow --region eu-central-1

# Lambda logs
aws logs tail /aws/lambda/$LAMBDA_FUNCTION --follow --region eu-central-1
```

### Metrics

Check Bedrock Agent metrics in CloudWatch:
- Invocations
- Errors
- Latency

## Cleanup

```bash
# Empty S3 buckets
aws s3 rm s3://$FRONTEND_BUCKET --recursive --region eu-central-1
aws s3 rm s3://$ARTIFACT_BUCKET --recursive --region eu-central-1

# Delete agent in Bedrock console

# Delete stack
aws cloudformation delete-stack --stack-name travel-assistant --region eu-central-1
```

## Troubleshooting

### Agent not responding
- Check AgentCore logs in CloudWatch
- Verify Docker image is in ECR
- Ensure IAM role has Bedrock permissions

### Lambda errors
- Verify AGENT_ID and AGENT_ALIAS_ID are set
- Check Lambda has permission to invoke agent
- Review CloudWatch logs

### Frontend not loading
- Check CloudFront distribution status
- Verify S3 bucket policy
- Check API Gateway URL in frontend config

## Cost Estimate

- **Bedrock AgentCore**: Pay per request + compute time
- **Lambda**: Pay per invocation
- **ECR**: Storage costs (minimal)
- **S3 + CloudFront**: Storage + data transfer
- **API Gateway**: Pay per request

Estimated: $20-100/month depending on usage
