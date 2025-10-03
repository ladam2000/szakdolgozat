#!/bin/bash
set -e

STACK_NAME="travel-assistant"
REGION="${AWS_REGION:-eu-central-1}"

echo "Deploying Travel Assistant with Bedrock AgentCore..."

# Deploy CloudFormation stack
echo "1. Deploying infrastructure..."
aws cloudformation deploy \
  --template-file infrastructure/template.yaml \
  --stack-name $STACK_NAME \
  --capabilities CAPABILITY_IAM \
  --region $REGION

# Get outputs
API_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayURL`].OutputValue' \
  --output text)

FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' \
  --output text)

AGENT_CODE_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`AgentCodeBucket`].OutputValue' \
  --output text)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text)

AGENT_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`BedrockAgentId`].OutputValue' \
  --output text)

echo "API Gateway URL: $API_URL"
echo "Agent ID: $AGENT_ID"

# Package and upload agent code
echo "2. Packaging agent code..."
cd agentcore
zip -r ../agent-code.zip agent_definition.py agents.py agentcore/
cd ..

echo "3. Uploading agent code to S3..."
aws s3 cp agent-code.zip s3://$AGENT_CODE_BUCKET/agent-code.zip --region $REGION

# Update frontend with API URL
echo "4. Updating frontend configuration..."
sed -i.bak "s|YOUR_API_GATEWAY_URL|$API_URL|g" frontend/app.js
rm -f frontend/app.js.bak

# Deploy frontend
echo "5. Deploying frontend..."
aws s3 sync frontend/ s3://$FRONTEND_BUCKET/ --region $REGION

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Application URL: $CLOUDFRONT_URL"
echo "Agent ID: $AGENT_ID"
echo ""
