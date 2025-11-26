"""
Google Gemini Integration for Janus
Handles all Gemini API interactions
"""

import os
import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


class GeminiClient:
    """Client for Google Gemini API integration"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            model_name: Gemini model to use (gemini-1.5-pro, gemini-1.5-flash, etc.)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable.")
        
        genai.configure(api_key=self.api_key)
        
        # Configure model with appropriate safety settings for financial operations
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        print(f"✓ Initialized Gemini client with model: {model_name}")
    
    async def extract_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Extract intent and parameters from user input
        
        Returns dict with:
            - action: The intended action (payment.transfer, data.query, etc.)
            - parameters: Extracted parameters (amount, recipient, etc.)
            - confidence: Confidence score
        """
        prompt = f"""
        Analyze this user request and extract the intent and parameters.
        User input: "{user_input}"
        
        Return a JSON object with:
        - action: one of [payment.transfer, payment.wire, data.query, data.export, help.request]
        - parameters: object with relevant parameters (amount, recipient, reason, etc.)
        - confidence: float between 0 and 1
        
        For payment requests, extract:
        - amount: numeric value
        - recipient: who/what the payment is for
        - type: transfer, wire, or payment
        
        Example response:
        {{
            "action": "payment.transfer",
            "parameters": {{
                "amount": 100.00,
                "recipient": "office supplies",
                "type": "payment"
            }},
            "confidence": 0.95
        }}
        
        Response (JSON only):
        """
        
        response = self.model.generate_content(prompt)
        
        try:
            # Parse JSON response
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            
            result = json.loads(text.strip())
            return result
        except:
            # Fallback parsing
            return {
                "action": "help.request",
                "parameters": {"original": user_input},
                "confidence": 0.5
            }
    
    async def generate_response(self, 
                                user_input: str, 
                                policy_decision: Dict[str, Any],
                                context: Optional[str] = None) -> str:
        """
        Generate a natural language response based on policy decision
        
        Args:
            user_input: Original user request
            policy_decision: Decision from PDP (allow/deny/require_approval)
            context: Additional context for response generation
        """
        effect = policy_decision.get('effect', 'deny')
        reason = policy_decision.get('reason', '')
        
        prompt = f"""
        Generate a helpful, professional response for this financial assistant scenario.
        
        User request: "{user_input}"
        Policy decision: {effect}
        Policy reason: {reason}
        {f"Additional context: {context}" if context else ""}
        
        Guidelines:
        - If ALLOWED: Confirm the action will be processed
        - If DENIED: Explain why politely and suggest alternatives
        - If REQUIRE_APPROVAL: Explain the approval process
        - Be concise but helpful
        - Maintain professional tone
        
        Response:
        """
        
        response = self.model.generate_content(prompt)
        return response.text.strip()
    
    def create_chat_session(self) -> Any:
        """Create a persistent chat session for conversations"""
        return self.model.start_chat(history=[])
