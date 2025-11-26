"""
Janus Agent - Enhanced with Gemini Integration
"""

import asyncio
from pathlib import Path
import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from janus_agent.core.policy_repository import PolicyRepository
from janus_agent.core.pdp import PolicyDecisionPoint
from janus_agent.integrations.gemini_client import GeminiClient
from janus_agent.adapters.adk_adapter import ADKAgent, ADKOrchestrator


class JanusAgent:
    """Enhanced Janus Agent with Gemini integration"""
    
    def __init__(self, agent_id: str, description: str = "", use_gemini: bool = True):
        self.agent_id = agent_id
        self.description = description
        
        # Load policies
        policy_dir = Path("policies/examples")
        if not policy_dir.exists():
            policy_dir = Path(__file__).parent.parent / "policies" / "examples"
        
        self.repository = PolicyRepository(str(policy_dir))
        self.pdp = PolicyDecisionPoint(self.repository)
        
        print(f"Initialized {agent_id}: {description}")
        print(f"Loaded {self.repository.size()} policies")
        
        # Initialize Gemini if API key is available
        self.gemini = None
        self.adk_agent = None
        
        if use_gemini and os.getenv('GOOGLE_API_KEY'):
            try:
                self.gemini = GeminiClient()
                self.adk_agent = ADKAgent(
                    agent_id=agent_id,
                    gemini_client=self.gemini,
                    policy_repository=self.repository,
                    pdp=self.pdp
                )
                print("✓ Gemini integration enabled")
            except Exception as e:
                print(f"⚠️  Gemini not available: {e}")
                print("   Running in policy-only mode")
    
    async def run(self, text: str):
        """Process text through policies (and Gemini if available)"""
        
        # If Gemini is available, use it for intelligent processing
        if self.adk_agent:
            response = await self.adk_agent.process_message(text)
            
            # Also get the policy decision for consistency
            intent = await self.gemini.extract_intent(text)
            decision = self.pdp.evaluate(
                subject=self.agent_id,
                action=intent.get('action', 'unknown'),
                resource='*',
                attrs=intent.get('parameters', {})
            )
            
            return response, decision, []
        
        # Fallback to simple policy-based processing
        amount = None
        for word in text.split():
            if word.startswith('$'):
                try:
                    amount = float(word[1:].replace(',', ''))
                    break
                except:
                    pass
        
        action = "payment.transfer"
        if "wire" in text.lower():
            action = "payment.wire"
        
        decision = self.pdp.evaluate(
            subject=self.agent_id,
            action=action,
            resource='*',
            attrs={'amount': amount} if amount else {}
        )
        
        # Generate simple response
        if decision['allow']:
            response = f"✅ Approved: {text}"
        else:
            response = f"❌ Denied: {decision['reason']}"
        
        return response, decision, []


def interactive_janus_agent(agent_id: str, description: str = ""):
    """Factory function for demos"""
    return JanusAgent(agent_id, description)


def create_adk_orchestrator():
    """Create an ADK orchestrator with Janus policies"""
    # Load policies
    repository = PolicyRepository("policies/examples")
    pdp = PolicyDecisionPoint(repository)
    
    # Create Gemini client
    gemini = GeminiClient()
    
    # Create orchestrator
    orchestrator = ADKOrchestrator(gemini, repository, pdp)
    
    return orchestrator
