#!/bin/bash

REGION="${AWS_REGION:-eu-central-1}"

echo "=========================================="
echo "  Current Configuration"
echo "=========================================="
echo ""

# Check Lambda stack
echo "Lambda Stack (travel-assistant-lambda):"
LAMBDA_EXISTS=$(aws cloudformation describe-stacks \
  --stack-name travel-assistant-lambda \
  --region $REGION 2>/dev/null)

if [ $? -eq 0 ]; then
    AGENT_ID=$(aws cloudformation describe-stacks \
      --stack-name travel-assistant-lambda \
      --region $REGION \
      --query 'Stacks[0].Parameters[?ParameterKey==`AgentId`].ParameterValue' \
      --output text)
    
    AGENT_ALIAS_ID=$(aws cloudformation describe-stacks \
      --stack-name travel-assistant-lambda \
      --region $REGION \
      --query 'Stacks[0].Parameters[?ParameterKey==`AgentAliasId`].ParameterValue' \
      --output text)
    
    API_URL=$(aws cloudformation describe-stacks \
      --stack-name travel-assistant-lambda \
      --region $REGION \
      --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
      --output text)
    
    echo "  ✅ Stack exists"
    echo "  Agent ID: $AGENT_ID"
    echo "  Agent Alias ID: $AGENT_ALIAS_ID"
    echo "  API URL: $API_URL"
else
    echo "  ❌ Stack not found"
fi

echo ""
echo "Frontend Configuration:"
FRONTEND_API=$(grep "const API_URL" frontend/app.js | sed "s/.*'\(.*\)'.*/\1/")
echo "  API URL: $FRONTEND_API"

echo ""
echo "=========================================="
echo ""

# List Bedrock Agents
echo "Available Bedrock Agents:"
aws bedrock-agent list-agents --region $REGION \
  --query 'agentSummaries[*].[agentId,agentName,agentStatus]' \
  --output table 2>/dev/null || echo "  ❌ Could not list agents (check permissions)"

echo ""
echo "To redeploy with correct Agent ID:"
echo "  ./deploy-all.sh <AGENT_ID> <AGENT_ALIAS_ID>"
