#!/bin/bash
set -e

STACK_NAME="travelassistant"
REGION="${AWS_REGION:-eu-central-1}"

echo "Deploying Virtual Travel Assistant..."

# Deploy CloudFormation stack
echo "1. Deploying infrastructure..."
aws cloudformation deploy \
  --template-file infrastructure/template.yaml \
  --stack-name $STACK_NAME \
  --capabilities CAPABILITY_IAM \
  --region $REGION \
  --parameter-overrides \
    BedrockModelId="anthropic.claude-3-sonnet-20240229-v1:0"

# Get stack outputs
echo "2. Getting stack outputs..."
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

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text)

echo "API Gateway URL: $API_URL"
echo "Frontend Bucket: $FRONTEND_BUCKET"
echo "CloudFront URL: $CLOUDFRONT_URL"

# Update frontend with API URL
echo "3. Updating frontend configuration..."
sed -i.bak "s|YOUR_API_GATEWAY_URL|$API_URL|g" frontend/app.js
rm -f frontend/app.js.bak

# Deploy frontend to S3
echo "4. Deploying frontend to S3..."
aws s3 sync frontend/ s3://$FRONTEND_BUCKET/ \
  --exclude "*.md" \
  --region $REGION

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Build and deploy AgentCore using CodeBuild"
echo "2. Access your application at: $CLOUDFRONT_URL"
echo ""
