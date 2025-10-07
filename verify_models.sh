#!/bin/bash
# Verify all models are set to Nova Micro

echo "=== Checking for Old Models ==="
OLD_MODELS=$(grep -r "claude-sonnet-4\|claude-3-5-haiku\|claude-opus" agentcore/ 2>/dev/null | grep -v ".md" | grep -v "DEPLOYMENT" | grep -v "TROUBLESHOOTING")

if [ -z "$OLD_MODELS" ]; then
    echo "✅ No old Claude models found in code"
else
    echo "❌ Old models still present:"
    echo "$OLD_MODELS"
    exit 1
fi

echo ""
echo "=== Checking Nova Micro Usage ==="
echo "Files with Nova Micro:"
grep -r "us.amazon.nova-micro-v1:0" agentcore/*.py | grep "model="

echo ""
echo "=== Count of Nova Micro in runtime_agent_main.py ==="
COUNT=$(grep -c "us.amazon.nova-micro-v1:0" agentcore/runtime_agent_main.py)
echo "Found $COUNT occurrences (should be 4: orchestrator + 3 specialists)"

if [ "$COUNT" -eq 4 ]; then
    echo "✅ Correct number of Nova Micro models"
else
    echo "❌ Expected 4 occurrences, found $COUNT"
    exit 1
fi

echo ""
echo "=== All Checks Passed ==="
echo "✅ Code is ready for deployment"
echo ""
echo "Next steps:"
echo "1. docker build --no-cache -t travel-agent-agentcore ./agentcore"
echo "2. Push to ECR or deploy to AgentCore"
echo "3. Verify CloudWatch logs show recent startup"
