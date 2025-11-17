#!/bin/bash
# Test runner script for Virtual Travel Assistant

set -e

echo "================================"
echo "Virtual Travel Assistant Tests"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r tests/requirements.txt
pip install -q -r lambda/requirements.txt

echo ""
echo "================================"
echo "Running Test Suite"
echo "================================"
echo ""

# Run all tests
echo -e "${YELLOW}Running tests...${NC}"
if pytest tests/test_basic.py -v --tb=short --cov=lambda --cov-report=term --cov-report=html; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    FAILED=0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    FAILED=1
fi

echo ""
echo "================================"
echo "Test Summary"
echo "================================"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Coverage report: htmlcov/index.html"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
