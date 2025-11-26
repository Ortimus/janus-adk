"""
Google ADK (Agent Development Kit) Adapter
Integrates Janus PDP multi-policy output into the ADK agent pipeline.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable
import logging

from janus_agent.core.pdp import PolicyDecisionPoint

logger = logging.getLogger(__name__)


@dataclass
class ADKTool:
    """Tool definition for ADK agents"""
    name: str
    description: str
    function: Callable[..., Any]
    parameters: Dict[str, Any]


class ADKAgent:
    """ADK-compatible agent with Janus policy integration and multi-policy reasoning."""

    def __init__(
        self,
        agent_id: str,
        gemini_client,
        policy_repository,
        pdp: PolicyDecisionPoint,
        tools: Optional[List[ADKTool]] = None
    ):
        """
        Initialize ADK agent with policy controls

        Args:
            agent_id: Unique agent identifier
            gemini_client: Gemini client for LLM operations (must implement extract_intent and generate_response)
            policy_repository: repository object (kept for compatibility / future refresh)
            pdp: PolicyDecisionPoint instance (must implement evaluate_all)
            tools: Optional list of ADKTool objects
        """
        self.agent_id = agent_id
        self.gemini = gemini_client
        self.repository = policy_repository
        self.pdp = pdp
        self.tools: List[ADKTool] = tools or []
        self.chat_session = None

        # Register default tools
        self._register_default_tools()

        logger.info(f"Initialized ADK Agent: {agent_id}")
        logger.info(f"Available tools: {[t.name for t in self.tools]}")

    # ----------------------------
    # Tool registration
    # ----------------------------
    def _register_default_tools(self):
        """Register default financial tools"""

        # process_payment tool
        self.register_tool(ADKTool(
            name="process_payment",
            description="Process a payment transaction",
            function=self._process_payment,
            parameters={
                "amount": "float",
                "recipient": "string",
                "type": "string"
            }
        ))

        # check_balance tool
        self.register_tool(ADKTool(
            name="check_balance",
            description="Check account balance",
            function=self._check_balance,
            parameters={"account": "string"}
        ))

        # check_policy tool (explicit policy check)
        self.register_tool(ADKTool(
            name="check_policy",
            description="Check if an action is allowed by policy",
            function=self._check_policy,
            parameters={
                "action": "string",
                "resource": "string",
                "attributes": "dict"
            }
        ))

    def register_tool(self, tool: ADKTool):
        """Register a new tool with the agent."""
        self.tools.append(tool)
        logger.debug(f"Registered tool: {tool.name}")

    # ----------------------------
    # Payment / Tools
    # ----------------------------

    async def _process_payment(self, amount: float, recipient: str, type: str = "transfer") -> Dict[str, Any]:
        """
        Process payment with policy check.
        Uses the PDP's evaluate_all() so we have full reasoning trace available.
        """
        # Map payment type -> action used by policies
        action_map = {
            "transfer": "payment.transfer",
            "wire": "payment.wire",
            "payment": "payment.transfer"
        }
        action = action_map.get(type, "payment.transfer")

        # Evaluate policies (multi-policy)
        eval_all = self.pdp.evaluate_all(
            subject=self.agent_id,
            action=action,
            resource="payment_system",
            attrs={"amount": amount, "recipient": recipient}
        )

        final = eval_all["final"]  # dict with allow/effect/reason/matched_policy
        matches = eval_all.get("matches", [])

        # Log a concise canonical summary AND a detailed match breakdown
        logger.info(self._format_policy_summary_for_logs(action, final, amount, recipient))
        self._log_policy_reasoning(matches)

        if final.get("allow"):
            # Simulate processing and return structured result
            txid = f"TXN-{abs(hash((self.agent_id, amount, recipient))) % 1000000:06d}"
            return {
                "status": "approved",
                "message": f"Payment of ${amount} to {recipient} approved",
                "transaction_id": txid,
                "policy": final.get("matched_policy"),
                "reason": final.get("reason"),
                "trace": matches
            }
        else:
            # Denied or requires approval
            status = "denied"
            return {
                "status": status,
                "message": f"Payment {status}: {final.get('reason')}",
                "policy": final.get("matched_policy"),
                "reason": final.get("reason"),
                "trace": matches
            }

    async def _check_balance(self, account: str = "main") -> Dict[str, Any]:
        """Mock balance check."""
        # In a real system, connect to banking / ledger systems.
        return {
            "account": account,
            "balance": 10000.00,
            "currency": "USD",
            "available": 9500.00
        }

    async def _check_policy(self, action: str, resource: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Explicit policy check via the PDP evaluate_all() API.
        Returns legacy-friendly fields and the full trace.
        """
        eval_all = self.pdp.evaluate_all(
            subject=self.agent_id,
            action=action,
            resource=resource,
            attrs=attributes
        )

        final = eval_all["final"]
        matches = eval_all.get("matches", [])

        # canonical log line
        logger.info(self._format_policy_summary_for_logs(action, final, attributes.get("amount"), attributes.get("recipient")))
        self._log_policy_reasoning(matches)

        return {
            "allowed": final.get("allow", False),
            "effect": final.get("effect"),
            "reason": final.get("reason"),
            "policy": final.get("matched_policy"),
            "matched_policies": matches
        }

    # ----------------------------
    # Message processing (LLM integration)
    # ----------------------------

    async def process_message(self, user_input: str) -> str:
        """
        Full pipeline for processing a user message:
         - Use Gemini to extract intent
         - Evaluate policies (multi-policy)
         - Execute action via tool if allowed
         - Ask Gemini to generate a natural language response (include decision trace)
        """

        # 1) Intent extraction using Gemini client
        intent = await self.gemini.extract_intent(user_input)
        logger.info(f"Extracted intent: {intent}")

        action = intent.get("action")
        params = intent.get("parameters", {})

        # 2) Policy evaluation (multi-policy)
        eval_all = self.pdp.evaluate_all(
            subject=self.agent_id,
            action=action,
            resource="*",
            attrs=params
        )

        final = eval_all["final"]
        matches = eval_all.get("matches", [])

        # Canonical log and detailed reasoning
        logger.info(self._format_policy_summary_for_logs(action, final, params.get("amount"), params.get("recipient")))
        self._log_policy_reasoning(matches)

        # 3) Execute if allowed
        result = None
        if final.get("allow"):
            # choose tool based on action
            if action and ("payment" in action):
                # run payment tool
                amount = params.get("amount", 0)
                recipient = params.get("recipient", "unknown")
                ttype = params.get("type", "transfer")
                result = await self._process_payment(amount, recipient, ttype)
            # (other tools can be added here)

        # 4) Generate final response via Gemini: include policy decision and trace for transparency
        response = await self.gemini.generate_response(
            user_input=user_input,
            policy_decision=final,
            context=(str(result) if result is not None else None)
        )

        return response

    # ----------------------------
    # Chat helpers
    # ----------------------------

    async def start_conversation(self) -> str:
        """Initialize a chat session on the Gemini client (if supported)."""
        if hasattr(self.gemini, "create_chat_session"):
            self.chat_session = self.gemini.create_chat_session()
        else:
            self.chat_session = {"history": []}
        return "Hello! I'm your AI financial assistant. How can I help you today?"

    async def continue_conversation(self, user_input: str) -> str:
        """Continue a conversation, maintaining chat history where available."""
        if not self.chat_session:
            await self.start_conversation()

        response = await self.process_message(user_input)

        # Update chat history if supported
        if isinstance(self.chat_session, dict) and "history" in self.chat_session:
            self.chat_session["history"].append({"role": "user", "parts": [user_input]})
            self.chat_session["history"].append({"role": "model", "parts": [response]})

        return response

    # ----------------------------
    # Logging helpers (single canonical summary + detailed reasoning)
    # ----------------------------
    def _format_policy_summary_for_logs(self, action: str, final: Dict[str, Any], amount: Optional[float], recipient: Optional[str]) -> str:
        """Return a single-line policy summary suitable for info logs."""
        applied = final.get("matched_policy") or final.get("matched_policy") or "default-deny"
        decision_name = final.get("effect") or ("allow" if final.get("allow") else "deny")
        intent_part = f"action={action}, amount={amount}, recipient={recipient}"
        return f"Policy decision: {decision_name} (policy: {applied}) -- {intent_part} -- agent={self.agent_id}"

    def _log_policy_reasoning(self, matches: List[Dict[str, Any]]):
        """Long-form matched policy dump for audit/debug (INFO level)."""
        if not matches:
            logger.info("Matched policy reasoning: <none>")
            return

        logger.info("Matched policy reasoning:")
        for m in matches:
            logger.info(f" - {m.get('policy')} (level={m.get('level')}, priority={m.get('priority')}, effect={m.get('effect')}) -> result={m.get('result')}")
        logger.info("")



class ADKOrchestrator:
    """Create and manage a collection of ADKAgent instances (multi-agent orchestration)."""

    def __init__(self, gemini_client, policy_repository, pdp: PolicyDecisionPoint):
        self.gemini = gemini_client
        self.repository = policy_repository
        self.pdp = pdp
        self.agents: Dict[str, ADKAgent] = {}

    def create_agent(self, agent_id: str, tools: Optional[List[ADKTool]] = None) -> ADKAgent:
        """Create and register a new ADKAgent using shared gemini/pdp instances."""
        agent = ADKAgent(
            agent_id=agent_id,
            gemini_client=self.gemini,
            policy_repository=self.repository,
            pdp=self.pdp,
            tools=tools
        )
        self.agents[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[ADKAgent]:
        return self.agents.get(agent_id)
