#!/bin/bash
set -e

REGION="${AWS_REGION:-eu-central-1}"
STACK_NAME="travel-assistant-lambda"
AGENT_ID="${1:-}"
AGENT_ALIAS_ID="${2:-}"

if [ -z "$AGENT_ID" ] || [ -z "$AGENT_ALIAS_ID" ]; then
    echo "Usage: ./deploy-lambda.sh <AGENT_ID> <AGENT_ALIAS_ID>"
    exit 1
fi

echo "Deploying Lambda function..."
echo "Agent ID: $AGENT_ID"
echo "Agent Alias ID: $AGENT_ALIAS_ID"
echo ""

# Create build directory
rm -rf build
mkdir -p build

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t build/ -q

# Copy Lambda code
echo "Copying Lambda code..."
cp handler.py build/

# Create deployment package
echo "Creating deployment package..."
cd build
zip -r ../lambda-package.zip . -q
cd ..

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --parameter-overrides \
        AgentId=$AGENT_ID \
        AgentAliasId=$AGENT_ALIAS_ID

# Get Lambda function name
FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`FunctionName`].OutputValue' \
    --output text)

# Update Lambda function code
echo "Updating Lambda function code..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://lambda-package.zip \
    --region $REGION > /dev/null

# Cleanup
rm -rf build lambda-package.zip

echo ""
echo "✅ Lambda deployed successfully!"
echo ""

# Get and display API URL
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

echo "API URL: $API_URL"
echo ""
echo "Test with:"
echo "curl -X POST $API_URL/chat -H 'Content-Type: application/json' -d '{\"message\":\"I want to plan a trip to Paris\",\"session_id\":\"test\"}'"
