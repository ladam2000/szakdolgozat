# Creating Bedrock Agent with AgentCore

## Step 1: Get ECR Image URI

```bash
aws cloudformation describe-stacks \
  --stack-name travel-assistant \
  --region eu-central-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ECRRepository`].OutputValue' \
  --output text
```

This will output something like: `123456789.dkr.ecr.eu-central-1.amazonaws.com/travel-assistant-agentcore:latest`

## Step 2: Create Bedrock Agent in AWS Console

1. Go to **Amazon Bedrock** console
2. Navigate to **Agents** → **Create Agent**
3. Configure:
   - **Agent name**: `travel-assistant`
   - **Agent resource role**: Use the role from CloudFormation output `AgentCoreRoleArn`
   - **Model**: Claude 3 Sonnet
   - **Instructions**: (optional, AgentCore has its own instructions)

4. Under **Agent runtime**:
   - Select **Custom runtime with AgentCore**
   - **Container image URI**: Paste the ECR URI from Step 1
   - **Port**: `8000`

5. Click **Create Agent**

6. After creation, click **Create Alias**:
   - **Alias name**: `live`
   - Click **Create**

## Step 3: Get Agent ID and Alias ID

After creating the agent:
- **Agent ID**: Found on the agent details page (10 characters, e.g., `ABCD123456`)
- **Alias ID**: Found on the alias details page (10 characters, e.g., `TSTALIASID`)

## Step 4: Deploy Lambda and Frontend

```bash
./deploy-all.sh <AGENT_ID> <ALIAS_ID>
```

Example:
```bash
./deploy-all.sh ABCD123456 TSTALIASID
```

This will:
1. Deploy Lambda with correct Agent IDs
2. Update frontend with API URL
3. Deploy frontend to S3
4. Invalidate CloudFront cache

## Step 5: Test

Get your CloudFront URL:
```bash
aws cloudformation describe-stacks \
  --stack-name travel-assistant \
  --region eu-central-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text
```

Open in browser and test!

## Troubleshooting

### Agent not found
- Make sure the agent is in `PREPARED` or `VERSIONED` state
- Check the agent is in the same region (eu-central-1)

### Container fails to start
- Check CloudWatch logs for the agent
- Verify the Docker image exists in ECR
- Make sure the image was built successfully

### Lambda errors
- Check Lambda CloudWatch logs
- Verify Agent ID and Alias ID are correct
- Ensure Lambda has permission to invoke agent
