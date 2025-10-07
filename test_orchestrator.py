#!/usr/bin/env python3
"""Test script for the orchestrator agent pattern."""

import sys
sys.path.insert(0, 'agentcore')

from agents import create_coordinator_agent

def test_orchestrator():
    """Test the orchestrator agent with sample queries."""
    
    print("=" * 60)
    print("Testing Travel Orchestrator Agent")
    print("=" * 60)
    
    # Create the orchestrator
    print("\n1. Creating orchestrator agent...")
    agent = create_coordinator_agent()
    print(f"   ✓ Agent created: {agent.name}")
    print(f"   ✓ Model: {agent.model}")
    print(f"   ✓ Tools: {len(agent.tools)} specialized agents")
    
    # Test queries
    test_queries = [
        "I want to plan a trip to Paris",
        "Find me flights from New York to London on March 15th",
        "What hotels are available in Tokyo?",
        "Suggest activities in Barcelona for 3 days",
    ]
    
    print("\n2. Testing queries...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        print("   " + "-" * 50)
        
        try:
            response = agent(query)
            
            # Extract content
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, dict) and 'content' in response:
                content = response['content']
            else:
                content = str(response)
            
            print(f"   Response length: {len(content)} characters")
            print(f"   Preview: {content[:200]}...")
            print("   ✓ Success")
            
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_orchestrator()
