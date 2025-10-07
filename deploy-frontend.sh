#!/bin/bash
# Deploy Lambda function and frontend to S3, then invalidate CloudFront cache
set -e

echo "🚀 Deploying Travel Assistant..."

# Configuration
STACK_NAME="travelassistant"
REGION="eu-central-1"
DISTRIBUTION_ID="E3U9T2QOCG5HLD"

# Get Lambda function name from CloudFormation
LAMBDA_FUNCTION=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunction`].OutputValue' \
  --output text 2>/dev/null)

if [ -z "$LAMBDA_FUNCTION" ]; then
  echo "❌ Error: Could not find Lambda function from CloudFormation stack"
  exit 1
fi

# Get S3 bucket name from CloudFormation
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' \
  --output text 2>/dev/null)

if [ -z "$BUCKET_NAME" ]; then
  echo "❌ Error: Could not find S3 bucket from CloudFormation stack"
  exit 1
fi

# Step 1: Update Lambda function
echo "⚡ Updating Lambda function: $LAMBDA_FUNCTION"
cd lambda
zip -q lambda.zip handler.py
aws lambda update-function-code \
  --function-name $LAMBDA_FUNCTION \
  --zip-file fileb://lambda.zip \
  --region $REGION > /dev/null
rm lambda.zip
cd ..
echo "✅ Lambda function updated"

# Step 2: Upload frontend files to S3
echo "📦 Uploading frontend to S3: $BUCKET_NAME"
aws s3 sync frontend/ s3://$BUCKET_NAME/ \
  --region $REGION \
  --exclude ".git/*" \
  --exclude "*.md" \
  --delete
echo "✅ Frontend uploaded to S3"

# Step 3: Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache: $DISTRIBUTION_ID"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*" \
  --region $REGION \
  --query 'Invalidation.Id' \
  --output text)

echo "⏳ Waiting for invalidation to complete..."
aws cloudfront wait invalidation-completed \
  --distribution-id $DISTRIBUTION_ID \
  --id $INVALIDATION_ID \
  --region $REGION

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Access your application at:"
echo "https://dbziso5b0wjgl.cloudfront.net"
