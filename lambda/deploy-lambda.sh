#!/bin/bash
set -e

REGION="${AWS_REGION:-eu-central-1}"
AGENT_ID="${1:-}"
AGENT_ALIAS_ID="${2:-}"

if [ -z "$AGENT_ID" ] || [ -z "$AGENT_ALIAS_ID" ]; then
    echo "Usage: ./deploy-lambda.sh <AGENT_ID> <AGENT_ALIAS_ID>"
    exit 1
fi

echo "Deploying Lambda function..."
echo "Agent ID: $AGENT_ID"
echo "Agent Alias ID: $AGENT_ALIAS_ID"

# Install dependencies
pip install -r requirements.txt -t .

# Deploy with SAM
sam deploy \
    --template-file template.yaml \
    --stack-name travel-assistant-lambda \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --parameter-overrides \
        AgentId=$AGENT_ID \
        AgentAliasId=$AGENT_ALIAS_ID \
    --resolve-s3

echo ""
echo "✅ Lambda deployed successfully!"
echo ""
echo "Get API URL:"
echo "aws cloudformation describe-stacks --stack-name travel-assistant-lambda --region $REGION --query 'Stacks[0].Outputs[?OutputKey==\`ApiUrl\`].OutputValue' --output text"
