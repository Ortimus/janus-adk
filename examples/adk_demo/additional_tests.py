#!/usr/bin/env python3
"""
Additional JANUS Demo Tests
- Enterprise-level PII protection
- Domain-level require_approval for finance agents

Add these functions to gemini_demo.py or run standalone
"""

import asyncio
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from janus_agent.core.policy_repository import PolicyRepository
from janus_agent.core.pdp import PolicyDecisionPoint


async def test_enterprise_pii_protection():
    """
    Test Enterprise-Level Policy: PII Data Protection
    
    Demonstrates the highest priority policy layer blocking
    sensitive data exports regardless of other permissions.
    """
    print("\n" + "="*70)
    print(" ENTERPRISE POLICY TEST: PII Data Protection")
    print("="*70)
    
    print("""
    Policy Under Test:
    ┌─────────────────────────────────────────────────────────────────┐
    │  enterprise-pii-protection (Level: ENTERPRISE, Priority: 1)    │
    │  Action: data.export | Resource: external | Effect: DENY       │
    │  Condition: data_classification = "pii"                        │
    └─────────────────────────────────────────────────────────────────┘
    """)
    
    # Initialize PDP
    policy_dir = Path("policies/examples")
    if not policy_dir.exists():
        policy_dir = Path(__file__).parent.parent / "policies" / "examples"
    
    repository = PolicyRepository(str(policy_dir))
    pdp = PolicyDecisionPoint(repository)
    
    print("Scenario: Various agents attempting to export data externally\n")
    print("-" * 70)
    
    # Test cases: Different agents trying to export PII vs non-PII data
    test_cases = [
        {
            "name": "Export PII to external API",
            "subject": "data-export-agent",
            "action": "data.export",
            "resource": "external",
            "attrs": {"data_classification": "pii", "destination": "third-party-api"},
            "expected": "deny",
            "reason": "Enterprise policy blocks ALL PII exports"
        },
        {
            "name": "Finance agent export PII",
            "subject": "finance-agent-1",
            "action": "data.export", 
            "resource": "external",
            "attrs": {"data_classification": "pii", "destination": "vendor-system"},
            "expected": "deny",
            "reason": "Even privileged finance agents cannot export PII"
        },
        {
            "name": "Export non-PII data externally",
            "subject": "data-export-agent",
            "action": "data.export",
            "resource": "external", 
            "attrs": {"data_classification": "public", "destination": "partner-api"},
            "expected": "deny",  # default-deny (no allow policy for this)
            "reason": "No explicit allow policy, defaults to deny"
        },
        {
            "name": "Export PII internally (not external)",
            "subject": "analytics-agent",
            "action": "data.export",
            "resource": "internal-warehouse",
            "attrs": {"data_classification": "pii"},
            "expected": "deny",  # default-deny (resource doesn't match)
            "reason": "Policy targets 'external' resource, but no allow exists"
        },
    ]
    
    results = []
    for test in test_cases:
        print(f"Test: {test['name']}")
        print(f"  Agent: {test['subject']}")
        print(f"  Action: {test['action']} → {test['resource']}")
        print(f"  Data Classification: {test['attrs'].get('data_classification', 'N/A')}")
        
        # Evaluate policy
        full_result = pdp.evaluate_all(
            subject=test['subject'],
            action=test['action'],
            resource=test['resource'],
            attrs=test['attrs']
        )
        
        decision = full_result['final']
        effect = decision.get('effect', 'unknown')
        policy = decision.get('matched_policy', 'unknown')
        
        # Show policy evaluation chain
        print(f"\n  Policy Evaluation Chain:")
        for match in full_result['matches']:
            status = "✓ MATCHED" if match['matches'] else "○ not applicable"
            print(f"    [{match['level'].upper():10}] {match['policy']:30} → {status}")
        
        # Show result
        is_correct = effect == test['expected']
        symbol = "✅" if is_correct else "❌"
        print(f"\n  {symbol} Decision: {effect.upper()} (policy: {policy})")
        print(f"  Reason: {test['reason']}")
        print("-" * 70)
        
        results.append(is_correct)
    
    # Summary
    passed = sum(results)
    print(f"\n📊 Enterprise PII Tests: {passed}/{len(results)} passed")
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║  KEY INSIGHT: Enterprise policies enforce organization-wide       ║
    ║  security rules that NO agent can bypass, regardless of their     ║
    ║  domain permissions or agent-level allowances.                    ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    return all(results)


async def test_domain_finance_approval():
    """
    Test Domain-Level Policy: Finance Team Approval Workflow
    
    Demonstrates how domain policies can require human approval
    for high-value transactions by specific agent groups.
    """
    print("\n" + "="*70)
    print(" DOMAIN POLICY TEST: Finance Team Approval Workflow")
    print("="*70)
    
    print("""
    Policy Under Test:
    ┌─────────────────────────────────────────────────────────────────┐
    │  domain-finance-team-limit (Level: DOMAIN, Priority: 20)       │
    │  Action: payment.transfer | Subject: finance-*                 │
    │  Effect: REQUIRE_APPROVAL | Condition: amount >= $10,000       │
    └─────────────────────────────────────────────────────────────────┘
    
    Challenge: Agent-level policy denies ALL payments >= $1,000
    This test shows how policy hierarchy SHOULD work vs current behavior.
    """)
    
    # Initialize PDP
    policy_dir = Path("policies/examples")
    if not policy_dir.exists():
        policy_dir = Path(__file__).parent.parent / "policies" / "examples"
    
    repository = PolicyRepository(str(policy_dir))
    pdp = PolicyDecisionPoint(repository)
    
    print("Scenario: Comparing regular vs finance agents on large transfers\n")
    print("-" * 70)
    
    test_cases = [
        {
            "name": "Regular agent - $15,000 transfer",
            "subject": "payment-agent-1",
            "action": "payment.transfer",
            "attrs": {"amount": 15000, "recipient": "supplier"},
            "description": "Standard payment agent attempting large transfer"
        },
        {
            "name": "Finance agent - $15,000 transfer", 
            "subject": "finance-agent-1",
            "action": "payment.transfer",
            "attrs": {"amount": 15000, "recipient": "supplier"},
            "description": "Finance team member with elevated permissions"
        },
        {
            "name": "Finance agent - $5,000 transfer",
            "subject": "finance-agent-1", 
            "action": "payment.transfer",
            "attrs": {"amount": 5000, "recipient": "vendor"},
            "description": "Finance agent below domain threshold"
        },
        {
            "name": "Finance manager - $50,000 transfer",
            "subject": "finance-manager-1",
            "action": "payment.transfer",
            "attrs": {"amount": 50000, "recipient": "contractor"},
            "description": "Finance manager with large transaction"
        },
    ]
    
    for test in test_cases:
        print(f"Test: {test['name']}")
        print(f"  Agent: {test['subject']}")
        print(f"  Amount: ${test['attrs']['amount']:,}")
        print(f"  Context: {test['description']}")
        
        # Evaluate with full reasoning
        full_result = pdp.evaluate_all(
            subject=test['subject'],
            action=test['action'],
            resource='*',
            attrs=test['attrs']
        )
        
        decision = full_result['final']
        
        # Show detailed policy matching
        print(f"\n  Policy Evaluation (by hierarchy level):")
        
        # Group by level for clearer display
        for level in ['enterprise', 'domain', 'agent']:
            level_policies = [m for m in full_result['matches'] if m['level'] == level]
            for match in level_policies:
                if match['matches']:
                    print(f"    [{level.upper():10}] {match['policy']:35} → ✓ {match['result'].upper()}")
                else:
                    print(f"    [{level.upper():10}] {match['policy']:35} → ○ not applicable")
        
        # Final decision
        effect = decision.get('effect', 'unknown')
        policy = decision.get('matched_policy', 'unknown')
        
        effect_symbol = {
            'allow': '✅',
            'deny': '❌', 
            'require_approval': '⚠️'
        }.get(effect, '❓')
        
        print(f"\n  {effect_symbol} Final Decision: {effect.upper()}")
        print(f"     Winning Policy: {policy}")
        print("-" * 70)
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║  ANALYSIS: Current PDP Behavior                                   ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║  The agent-level deny (amount >= $1000) currently catches all     ║
    ║  large payments before the domain require_approval can trigger.   ║
    ║                                                                   ║
    ║  This demonstrates an important design consideration:             ║
    ║  Effect precedence (deny > require_approval > allow) applies      ║
    ║  ACROSS all matching policies, not per-level.                     ║
    ║                                                                   ║
    ║  To enable domain override, you could:                            ║
    ║  1. Modify agent policy: subject="payment-*" (exclude finance)    ║
    ║  2. Adjust PDP: Apply effect precedence within each level first   ║
    ║  3. Use priority: Give domain policies lower (stronger) priority  ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)


async def test_hierarchy_override_demo():
    """
    Demonstrates proper hierarchy override with modified policy scope.
    
    This shows what SHOULD happen when domain policies properly
    override agent policies for specific agent groups.
    """
    print("\n" + "="*70)
    print(" HIERARCHY OVERRIDE DEMO: Domain Overrides Agent")
    print("="*70)
    
    print("""
    To properly demonstrate domain-level override, we simulate
    a policy configuration where:
    
    - Agent policy: Deny payments >= $1000 for "payment-*" agents only
    - Domain policy: Require approval for "finance-*" agents >= $10,000
    
    This allows finance agents to process mid-range payments ($1000-$9999)
    that regular payment agents cannot.
    """)
    
    # Create a custom policy repository with modified scope
    from janus_agent.core.policy_repository import PolicyRepository
    from janus_agent.core.pdp import PolicyDecisionPoint
    
    # We'll manually create policies to demonstrate the concept
    class MockRepository:
        def __init__(self):
            self.policies = [
                {
                    "id": "enterprise-pii-protection",
                    "level": "enterprise",
                    "action": "data.export",
                    "subject": "*",
                    "resource": "external",
                    "effect": "deny",
                    "match": {"data_classification": "pii"},
                    "priority": 1
                },
                {
                    "id": "domain-finance-elevated",
                    "level": "domain", 
                    "action": "payment.transfer",
                    "subject": "finance-*",
                    "resource": "*",
                    "effect": "allow",  # Changed to allow for demo
                    "match": {"amount_max": 9999},
                    "priority": 15
                },
                {
                    "id": "domain-finance-approval",
                    "level": "domain",
                    "action": "payment.transfer", 
                    "subject": "finance-*",
                    "resource": "*",
                    "effect": "require_approval",
                    "match": {"amount_min": 10000},
                    "priority": 20
                },
                {
                    "id": "agent-allow-small",
                    "level": "agent",
                    "action": "payment.transfer",
                    "subject": "*",
                    "resource": "*",
                    "effect": "allow",
                    "match": {"amount_max": 999},
                    "priority": 10
                },
                {
                    "id": "agent-deny-large",
                    "level": "agent",
                    "action": "payment.transfer",
                    "subject": "payment-*",  # Only payment agents, not finance
                    "resource": "*",
                    "effect": "deny",
                    "match": {"amount_min": 1000},
                    "priority": 10
                },
            ]
        
        def list(self):
            return self.policies
        
        def size(self):
            return len(self.policies)
    
    mock_repo = MockRepository()
    pdp = PolicyDecisionPoint(mock_repo)
    
    print("\nModified Policy Configuration:")
    print("┌─────────────────────────────────────────────────────────────────┐")
    print("│ agent-deny-large: subject='payment-*' (excludes finance-*)     │")
    print("│ domain-finance-elevated: allows finance-* up to $9,999         │")
    print("│ domain-finance-approval: requires approval for finance-* >=$10k│")
    print("└─────────────────────────────────────────────────────────────────┘")
    
    print("\n" + "-" * 70)
    
    test_cases = [
        ("payment-agent-1", 5000, "Regular payment agent"),
        ("finance-agent-1", 5000, "Finance agent (mid-range)"),
        ("finance-agent-1", 15000, "Finance agent (high-value)"),
        ("finance-manager-1", 500, "Finance manager (small)"),
    ]
    
    print(f"\n{'Agent':<25} {'Amount':>10} {'Decision':<20} {'Policy':<30}")
    print("=" * 85)
    
    for subject, amount, desc in test_cases:
        result = pdp.evaluate(
            subject=subject,
            action="payment.transfer",
            resource="*",
            attrs={"amount": amount}
        )
        
        effect = result['effect']
        policy = result['matched_policy']
        
        symbol = {'allow': '✅', 'deny': '❌', 'require_approval': '⚠️'}.get(effect, '?')
        
        print(f"{subject:<25} ${amount:>8,} {symbol} {effect:<17} {policy:<30}")
    
    print("\n" + "=" * 85)
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║  RESULT: With scoped agent policies, the hierarchy works:         ║
    ║                                                                   ║
    ║  • payment-agent-1 @ $5,000  → DENY (agent-deny-large)           ║
    ║  • finance-agent-1 @ $5,000  → ALLOW (domain-finance-elevated)   ║
    ║  • finance-agent-1 @ $15,000 → REQUIRE_APPROVAL (domain policy)  ║
    ║                                                                   ║
    ║  Finance team gets elevated permissions via domain-level policy!  ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)


async def main():
    """Run all additional demo tests"""
    
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "     JANUS ADDITIONAL DEMO TESTS".center(68) + "█")
    print("█" + "     Enterprise & Domain Policy Scenarios".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    # Test 1: Enterprise PII Protection
    await test_enterprise_pii_protection()
    
    # Test 2: Domain Finance Approval (current behavior)
    await test_domain_finance_approval()
    
    # Test 3: Hierarchy Override Demo (with modified policies)
    await test_hierarchy_override_demo()
    
    print("\n" + "="*70)
    print(" DEMO COMPLETE")
    print("="*70)
    print("""
    Summary of Policy Hierarchy Demonstration:
    
    1. ENTERPRISE LEVEL (Highest Priority)
       └─ PII protection blocks ALL external data exports
       └─ No agent or domain can override this
    
    2. DOMAIN LEVEL (Department Rules)  
       └─ Can grant elevated permissions to specific agent groups
       └─ Example: finance-* agents get higher transaction limits
    
    3. AGENT LEVEL (Service Rules)
       └─ Default operational constraints
       └─ Can be overridden by higher-level policies
    
    This demonstrates defense-in-depth with flexible policy management!
    """)


if __name__ == "__main__":
    asyncio.run(main())
