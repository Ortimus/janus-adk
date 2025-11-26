"""
Policy Decision Point (PDP) - Dict-Based Implementation
Supports multi-policy evaluation with full reasoning output.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PolicyDecisionPoint:
    """Policy Decision Point (PDP) with full multi-policy evaluation."""

    def __init__(self, repository):
        self.repository = repository
        self.logger = logger

    # ------------------------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------------------------

    def evaluate(self, subject: str, action: str, resource: Optional[str] = None,
                 attrs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        High-level evaluation entry point.
        Returns the *final decision* plus list of all policy matches.
        """
        full = self.evaluate_all(subject, action, resource, attrs)
        return full["final"]

    def evaluate_all(self, subject: str, action: str, resource: Optional[str] = None,
                     attrs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Full multi-policy evaluation.
        Returns:
          {
            "matches": [...per-policy results...],
            "final": { final decision dict }
          }
        """

        if attrs is None:
            attrs = {}

        # Build evaluation context
        context = {
            "subject": subject,
            "action": action,
            "resource": resource or "*",
            **attrs,
        }

        self.logger.debug(f"[PDP] Evaluating context: {context}")

        policies = self.repository.list()
        match_results = []

        # Check match per-policy (but do NOT short-circuit)
        for p in policies:
            matches = self._matches(p, context)
            match_results.append({
                "policy": p.get("id"),
                "level": p.get("level", "agent"),
                "priority": p.get("priority", 50),
                "effect": p.get("effect"),
                "matches": matches,
                "result": self._result_for_single_policy(p, matches)
            })

        # Determine final decision using level/priority ordering
        final_decision = self._compute_final_decision(match_results)

        return {
            "matches": match_results,
            "final": final_decision,
        }

    # ------------------------------------------------------------------------------------
    # INTERNAL MATCHING / DECISION LOGIC
    # ------------------------------------------------------------------------------------

    def _matches(self, policy: Dict, context: Dict) -> bool:
        """Check whether a policy applies based on subject/action/resource + attributes."""
        if not self._matches_pattern(policy.get("action", "*"), context.get("action", "")):
            return False

        if not self._matches_pattern(policy.get("subject", "*"), context.get("subject", "")):
            return False

        if not self._matches_pattern(policy.get("resource", "*"), context.get("resource", "*")):
            return False

        # Additional match constraints
        match = policy.get("match", {})

        if "amount_max" in match:
            if context.get("amount", float("inf")) > match["amount_max"]:
                return False

        if "amount_min" in match:
            if context.get("amount", 0) < match["amount_min"]:
                return False

        return True

    def _matches_pattern(self, pattern: str, value: str) -> bool:
        """Support '*', prefix*, or exact."""
        if pattern == "*":
            return True
        if pattern == value:
            return True
        if pattern.endswith("*"):
            return value.startswith(pattern[:-1])
        return False

    def _result_for_single_policy(self, policy: Dict, matches: bool) -> str:
        """Returns per-policy outcome string."""
        if not matches:
            return "not_applicable"
        effect = policy.get("effect")
        if effect == "deny":
            return "deny"
        if effect == "allow":
            return "allow"
        if effect == "require_approval":
            return "require_approval"
        return "unknown"

    # ------------------------------------------------------------------------------------
    # FINAL DECISION LOGIC
    # ------------------------------------------------------------------------------------

    def _compute_final_decision(self, match_results: List[Dict]) -> Dict[str, Any]:
        """
        Applies precedence ordering:
           1. level order: enterprise → domain → agent → runtime
           2. priority (lower = stronger)
           3. effect order: deny > require_approval > allow
        """

        # Filter policies that matched
        applicable = [m for m in match_results if m["matches"]]

        if not applicable:
            return {
                "allow": False,
                "effect": "deny",
                "reason": "No matching policies",
                "matched_policy": "default-deny",
            }

        LEVEL_ORDER = {"enterprise": 1, "domain": 2, "agent": 3, "runtime": 4}

        # Sort by level → priority
        applicable_sorted = sorted(
            applicable,
            key=lambda m: (
                LEVEL_ORDER.get(m["level"], 3),
                m["priority"]
            )
        )

        # Now apply effect precedence:
        # Deny wins over require_approval wins over allow
        for m in applicable_sorted:
            if m["result"] == "deny":
                return {
                    "allow": False,
                    "effect": "deny",
                    "reason": f"Deny by policy {m['policy']}",
                    "matched_policy": m["policy"],
                }

        for m in applicable_sorted:
            if m["result"] == "require_approval":
                return {
                    "allow": False,
                    "effect": "require_approval",
                    "reason": f"Approval required by policy {m['policy']}",
                    "matched_policy": m["policy"],
                }

        for m in applicable_sorted:
            if m["result"] == "allow":
                return {
                    "allow": True,
                    "effect": "allow",
                    "reason": f"Allow by policy {m['policy']}",
                    "matched_policy": m["policy"],
                }

        # Should never happen
        return {
            "allow": False,
            "effect": "deny",
            "reason": "Default deny",
            "matched_policy": "default-deny",
        }


PDP = PolicyDecisionPoint
