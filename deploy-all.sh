#!/bin/bash
set -e

REGION="${AWS_REGION:-eu-central-1}"
AGENT_RUNTIME_ARN="${1:-}"

if [ -z "$AGENT_RUNTIME_ARN" ]; then
    echo "Usage: ./deploy-all.sh <AGENT_RUNTIME_ARN>"
    echo ""
    echo "Example: ./deploy-all.sh arn:aws:bedrock-agentcore:eu-central-1:206631439304:runtime/hosted_agent_rkxzc-Yq2wttGAF4"
    echo ""
    echo "This script will:"
    echo "  1. Deploy Lambda function to call AgentCore Runtime"
    echo "  2. Update frontend with correct API URL"
    echo "  3. Deploy frontend to S3"
    echo "  4. Invalidate CloudFront cache"
    exit 1
fi

echo "=========================================="
echo "  Deploying Travel Assistant"
echo "=========================================="
echo "Agent Runtime ARN: $AGENT_RUNTIME_ARN"
echo "Region: $REGION"
echo ""

# Step 1: Deploy Lambda
echo "📦 Step 1/4: Deploying Lambda function..."
cd lambda
./deploy-lambda.sh "$AGENT_RUNTIME_ARN"
cd ..
echo ""

# Step 2: Get API URL
echo "🔗 Step 2/4: Getting API URL..."
API_URL=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant-lambda \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

if [ -z "$API_URL" ]; then
    echo "❌ Error: Could not get API URL"
    exit 1
fi

echo "API URL: $API_URL"
echo ""

# Step 3: Update and deploy frontend
echo "🌐 Step 3/4: Updating and deploying frontend..."

# Update API URL in frontend
sed -i.bak "s|const API_URL = '.*'|const API_URL = '$API_URL'|g" frontend/app.js
rm -f frontend/app.js.bak

# Get frontend bucket
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name travelassistant \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' \
  --output text)

if [ -z "$FRONTEND_BUCKET" ]; then
    echo "❌ Error: Could not get frontend bucket"
    exit 1
fi

# Deploy to S3
echo "Uploading to S3: $FRONTEND_BUCKET"
aws s3 sync frontend/ s3://$FRONTEND_BUCKET/ \
  --exclude "*.md" \
  --region $REGION \
  --quiet

echo ""

# Step 4: Invalidate CloudFront cache
echo "🔄 Step 4/4: Invalidating CloudFront cache..."

# Get CloudFront distribution ID
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name travelassistant \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text | sed 's|https://||' | sed 's|\.cloudfront\.net||')

if [ -z "$DISTRIBUTION_ID" ]; then
    # Try to get it from CloudFront directly
    DISTRIBUTION_ID=$(aws cloudfront list-distributions \
      --query "DistributionList.Items[?Origins.Items[0].DomainName=='$FRONTEND_BUCKET.s3.$REGION.amazonaws.com'].Id" \
      --output text 2>/dev/null | head -1)
fi

if [ -n "$DISTRIBUTION_ID" ]; then
    echo "Invalidating distribution: $DISTRIBUTION_ID"
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
      --distribution-id $DISTRIBUTION_ID \
      --paths "/*" \
      --query 'Invalidation.Id' \
      --output text)
    
    echo "Invalidation created: $INVALIDATION_ID"
    echo "Waiting for invalidation to complete..."
    aws cloudfront wait invalidation-completed \
      --distribution-id $DISTRIBUTION_ID \
      --id $INVALIDATION_ID
    echo "✅ Cache invalidated"
else
    echo "⚠️  Warning: Could not find CloudFront distribution ID"
    echo "You may need to manually invalidate the cache or wait for TTL"
fi

echo ""
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""

# Get CloudFront URL
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name travelassistant \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text)

echo "🌍 Application URL: $CLOUDFRONT_URL"
echo "🔗 API URL: $API_URL"
echo ""
echo "Test the API:"
echo "curl -X POST $API_URL/chat -H 'Content-Type: application/json' -d '{\"message\":\"I want to plan a trip to Paris\",\"session_id\":\"test\"}'"
echo ""
