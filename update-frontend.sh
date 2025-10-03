#!/bin/bash
set -e

REGION="${AWS_REGION:-eu-central-1}"

echo "Updating frontend with Lambda API URL..."

# Get the Lambda API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant-lambda \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text 2>/dev/null)

if [ -z "$API_URL" ]; then
    echo "❌ Error: Lambda stack not found or no API URL output"
    echo "Make sure you've deployed the Lambda function first:"
    echo "  cd lambda && ./deploy-lambda.sh <AGENT_ID> <AGENT_ALIAS_ID>"
    exit 1
fi

echo "API URL: $API_URL"

# Update frontend
sed -i.bak "s|const API_URL = '.*'|const API_URL = '$API_URL'|g" frontend/app.js
rm -f frontend/app.js.bak

echo ""
echo "✅ Frontend updated!"
echo ""

# Get frontend bucket and CloudFront URL
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' \
  --output text 2>/dev/null)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text 2>/dev/null)

if [ -n "$FRONTEND_BUCKET" ]; then
    echo "Deploy to S3 with:"
    echo "  aws s3 sync frontend/ s3://$FRONTEND_BUCKET/ --region $REGION"
    echo ""
fi

if [ -n "$CLOUDFRONT_URL" ]; then
    echo "Access your app at: $CLOUDFRONT_URL"
fi
