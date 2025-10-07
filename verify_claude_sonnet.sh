#!/bin/bash
# Verify all agents are using Claude Sonnet 4.5

echo "=== Verifying Claude Sonnet 4.5 Configuration ==="
echo ""

# Check for the correct model
CORRECT_MODEL="eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
echo "Looking for model: $CORRECT_MODEL"
echo ""

# Count occurrences in each file
echo "=== Checking runtime_agent_main.py ==="
COUNT_RUNTIME=$(grep -c "$CORRECT_MODEL" agentcore/runtime_agent_main.py 2>/dev/null || echo "0")
echo "Found $COUNT_RUNTIME occurrences (expected: 4)"

echo ""
echo "=== Checking agents.py ==="
COUNT_AGENTS=$(grep -c "$CORRECT_MODEL" agentcore/agents.py 2>/dev/null || echo "0")
echo "Found $COUNT_AGENTS occurrences (expected: 4)"

echo ""
echo "=== Checking agent.py ==="
COUNT_AGENT=$(grep -c "$CORRECT_MODEL" agentcore/agent.py 2>/dev/null || echo "0")
echo "Found $COUNT_AGENT occurrences (expected: 4)"

echo ""
echo "=== Total Count ==="
TOTAL=$((COUNT_RUNTIME + COUNT_AGENTS + COUNT_AGENT))
echo "Total: $TOTAL occurrences (expected: 12)"

echo ""
echo "=== Checking for Old Models ==="
OLD_MODELS=$(grep -r "nova-micro\|claude-3-5-haiku\|claude-sonnet-4-20250514" agentcore/*.py 2>/dev/null)
if [ -z "$OLD_MODELS" ]; then
    echo "✅ No old models found"
else
    echo "❌ Old models still present:"
    echo "$OLD_MODELS"
    exit 1
fi

echo ""
if [ "$TOTAL" -eq 12 ]; then
    echo "✅ SUCCESS: All agents configured with Claude Sonnet 4.5"
    echo ""
    echo "Next steps:"
    echo "1. docker build --no-cache -t travel-agent-agentcore ./agentcore"
    echo "2. Push to ECR and deploy to AgentCore"
    echo "3. Test with: {\"input\": \"Plan a trip to Paris\"}"
else
    echo "❌ ERROR: Expected 12 occurrences, found $TOTAL"
    echo "Please check the configuration"
    exit 1
fi
