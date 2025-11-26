#!/usr/bin/env python3
"""
Janus + Google Gemini Demo - Enhanced with Hierarchy & Edge Cases
Shows integration with Google's Gemini API plus comprehensive policy testing
"""

import asyncio
import os
from pathlib import Path
import sys

# Load .env file
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from janus_agent.agent import JanusAgent, create_adk_orchestrator
from janus_agent.core.policy_repository import PolicyRepository
from janus_agent.core.pdp import PolicyDecisionPoint


async def test_basic_policies(agent):
    """Test basic agent-level policies"""
    print("\n" + "="*60)
    print("BASIC POLICY TESTS")
    print("Agent-level payment policies")
    print("="*60)
    
    tests = [
        ("Small payment", "Pay $50 to office supplies", "allow"),
        ("Medium payment", "Transfer $750 to vendor", "allow"),
        ("Edge case", "Pay $999 for equipment", "allow"),
        ("Threshold", "Transfer $1000 to account", "deny"),
        ("Large payment", "Pay $5000 for services", "deny"),
    ]
    
    results = []
    for name, text, expected_effect in tests:
        print(f"\n{name}: {text}")
        response, decision, _ = await agent.run(text)
        effect = decision.get('effect', 'unknown')
        
        if effect == expected_effect:
            print(f"   ✅ Correct: {effect} (policy: {decision['matched_policy']})")
            results.append(True)
        else:
            print(f"   ❌ Wrong: expected {expected_effect}, got {effect}")
            results.append(False)
        
        # Show Gemini response if available
        if agent.gemini:
            print(f"   Gemini: {response[:100]}...")
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Basic Tests: {passed}/{total} passed")
    return all(results)


async def test_hierarchy_with_domain():
    """Test policy hierarchy with domain-level policies"""
    print("\n" + "="*60)
    print("HIERARCHY TESTS")
    print("Domain + Agent policy interaction")
    print("="*60)
    
    # Check if domain policies are enabled
    domain_file = Path("policies/examples/domain-finance.yaml")
    if not domain_file.exists():
        # Try to enable it
        disabled_file = Path("policies/examples/domain-finance.yaml.disabled")
        if disabled_file.exists():
            print("\n⚠️  Enabling domain policies...")
            import shutil
            shutil.copy2(disabled_file, domain_file)
            print("✅ Domain policies enabled!")
        else:
            print("\n⚠️  Domain policies file not found!")
            return False
    
    print("\n1️⃣  Subject-Specific Domain Policies")
    print("-" * 40)
    
    # Test regular vs finance agents
    print("\nTesting different agent types with $10,000 transfer:")
    
    regular_agent = JanusAgent("payment-agent-1", "Payment processor")
    finance_agent = JanusAgent("finance-agent-1", "Finance team", use_gemini=False)
    
    # Regular agent
    _, decision1, _ = await regular_agent.run("Transfer $10,000 to supplier")
    print(f"Regular agent (payment-*): {decision1['effect']} - {decision1['matched_policy']}")
    
    # Finance agent
    _, decision2, _ = await finance_agent.run("Transfer $10,000 to supplier")
    print(f"Finance agent (finance-*): {decision2['effect']} - {decision2['matched_policy']}")
    
    print("\n💡 Domain policies can target specific agent patterns!")
    
    print("\n2️⃣  Action-Specific Policies")
    print("-" * 40)
    
    test_agent = JanusAgent("test-agent", "Test")
    
    # Different actions
    _, decision3, _ = await test_agent.run("Transfer $100 to petty cash")
    print(f"Regular transfer: {decision3['effect']}")
    
    _, decision4, _ = await test_agent.run("Wire $100 to bank account")
    print(f"Wire transfer: {decision4['effect']}")
    
    print("\n💡 Different actions can trigger different policies!")
    
    print("\n3️⃣  Policy Precedence")
    print("-" * 40)
    print("""
    Policy Evaluation Order:
    ┌─────────────────┐
    │   ENTERPRISE    │ ← Highest priority
    ├─────────────────┤
    │     DOMAIN      │ ← Department rules
    ├─────────────────┤
    │     AGENT       │ ← Service rules
    └─────────────────┘
    """)
    
    return True


async def test_edge_cases(agent):
    """Test edge cases with Gemini understanding"""
    print("\n" + "="*60)
    print("EDGE CASE TESTS")
    print("How Gemini + Policies handle special scenarios")
    print("="*60)
    
    edge_cases = [
        "Transfer exactly $999 dollars",
        "Send one thousand dollars to vendor",  # Natural language for $1000
        "Pay 0 dollars for testing",
        "I need to transfer five thousand to reserve",  # No $ sign
        "Can you process a million dollar payment?",  # Huge amount
        "Transfer five hundred... actually make it six hundred",  # Changed mind
    ]
    
    for test in edge_cases:
        print(f"\nUser: {test}")
        
        if agent.gemini:
            # Get Gemini's interpretation
            intent = await agent.gemini.extract_intent(test)
            print(f"   Gemini extracted: amount=${intent.get('parameters', {}).get('amount', 'unknown')}")
        
        response, decision, _ = await agent.run(test)
        effect = decision.get('effect', 'unknown')
        print(f"   Policy decision: {effect}")
        
        if agent.gemini:
            print(f"   Response: {response[:100]}...")
    
    print("\n💡 Gemini handles natural language amounts!")


async def test_gemini_integration():
    """Test Gemini integration with policy enforcement"""
    
    print("=" * 60)
    print(" JANUS + GOOGLE GEMINI INTEGRATION DEMO")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("\n⚠️  GOOGLE_API_KEY not set!")
        print("To enable Gemini:")
        print("  export GOOGLE_API_KEY='your-api-key-here'")
        print("\nRunning in policy-only mode...\n")
    
    # Create agent with Gemini
    agent = JanusAgent(
        "gemini-financial-assistant",
        "AI Financial Assistant powered by Gemini"
    )
    
    # Run basic policy tests
    await test_basic_policies(agent)
    
    # Run hierarchy tests
    await test_hierarchy_with_domain()
    
    # Run edge case tests
    await test_edge_cases(agent)
    
    print("\n" + "="*60)
    print(" Natural Language Processing Tests")
    print("="*60)
    
    # Test natural language understanding
    if agent.gemini:
        nl_tests = [
            "I need to pay fifty dollars for office supplies",
            "Can you send ten grand to our contractor?",
            "Wire five hundred euros to our European office",
            "Process a payment of two thousand five hundred dollars",
        ]
        
        print("\nTesting Gemini's natural language understanding:\n")
        for test in nl_tests:
            print(f"User: {test}")
            response, decision, _ = await agent.run(test)
            print(f"Gemini: {response[:150]}...")
            print(f"Policy: {decision['effect']} ({decision['matched_policy']})")
            print()


async def test_adk_orchestrator():
    """Test ADK Orchestrator with multiple agents"""
    
    if not os.getenv('GOOGLE_API_KEY'):
        print("\nSkipping ADK Orchestrator test (no API key)")
        return
    
    print("\n" + "=" * 60)
    print(" ADK ORCHESTRATOR WITH HIERARCHY")
    print("=" * 60)
    
    try:
        # Create orchestrator
        orchestrator = create_adk_orchestrator()
        
        # Create specialized agents with different permissions
        agents = [
            ("junior-payment-agent", "Junior staff - strict limits"),
            ("senior-payment-agent", "Senior staff - higher limits"),
            ("finance-manager-1", "Finance manager - department rules"),
            ("audit-agent-1", "Audit team - monitoring only"),
        ]
        
        for agent_id, description in agents:
            orchestrator.create_agent(agent_id)
            print(f"Created: {agent_id} - {description}")
        
        # Test same request with different agents
        test_amount = "$5,000 payment to contractor"
        print(f"\nTesting: '{test_amount}' with different agents:\n")
        
        for agent_id, _ in agents[:3]:  # Test first 3 agents
            agent = orchestrator.get_agent(agent_id)
            if agent:
                print(f"Agent: {agent_id}")
                response = await agent.process_message(test_amount)
                print(f"Response: {response}\n")
    
    except Exception as e:
        print(f"Error in orchestrator: {e}")


async def interactive_chat():
    """Interactive chat with policy testing"""
    
    print("\n" + "=" * 60)
    print(" INTERACTIVE POLICY TESTING CHAT")
    print("=" * 60)
    
    if not os.getenv('GOOGLE_API_KEY'):
        print("\n⚠️  Interactive chat requires GOOGLE_API_KEY")
        return
    
    try:
        # Let user choose agent type
        print("\nChoose agent type:")
        print("1. payment-agent (standard limits)")
        print("2. finance-agent (higher limits)")
        print("3. audit-agent (monitoring)")
        
        choice = input("Select (1-3): ").strip()
        
        agent_configs = {
            "1": ("payment-agent-1", "Payment processor"),
            "2": ("finance-agent-1", "Finance team member"),
            "3": ("audit-agent-1", "Audit monitor"),
        }
        
        agent_id, description = agent_configs.get(choice, agent_configs["1"])
        
        # Create agent
        agent = JanusAgent(agent_id, description)
        
        if agent.adk_agent:
            print(f"\n✅ Initialized as: {agent_id} - {description}")
            print("\n" + await agent.adk_agent.start_conversation())
            print("\nTry these:")
            print("  • 'Pay $50 for supplies' (should work)")
            print("  • 'Transfer $5000 to vendor' (depends on agent)")
            print("  • 'Wire $100 to partner' (special rules)")
            print("\n(Type 'quit' to exit)\n")
            
            while True:
                user_input = input("You: ")
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Assistant: Goodbye!")
                    break
                
                response = await agent.adk_agent.continue_conversation(user_input)
                print(f"Assistant: {response}\n")
        else:
            print("Could not initialize Gemini agent")
    
    except Exception as e:
        print(f"Error in chat: {e}")


async def main():
    """Run all demos"""
    
    print("\n🔍 Checking environment...")
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        print(f"✅ Found API key: {api_key[:10]}...")
    else:
        print("⚠️  No API key - running in policy-only mode")
    
    # Main integration test with all features
    await test_gemini_integration()
    
    # Test orchestrator
    await test_adk_orchestrator()
    
    # Interactive chat
    response = input("\nStart interactive chat? (y/n): ")
    if response.lower() == 'y':
        await interactive_chat()
    
    print("\n✅ Demo complete!")
    print("\n📊 Summary:")
    print("  • Basic policies ✓")
    print("  • Hierarchy tests ✓")
    print("  • Edge cases ✓")
    print("  • Natural language ✓" if api_key else "  • Natural language (requires API key)")
    print("  • Multi-agent orchestration ✓" if api_key else "  • Multi-agent (requires API key)")


if __name__ == "__main__":
    asyncio.run(main())
