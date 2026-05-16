import anthropic
import json
import logging
from typing import Optional, Dict, Any
from app.config.settings import settings
from app.config.constants import QueryType

logger = logging.getLogger(__name__)

class ClaudeService:
    """
    Service for interacting with the Anthropic Claude API.
    
    Handles prompt construction, API communication, response parsing, 
    and structured error handling to ensure system resilience.
    """
    
    # Default fallback messages used when the AI service is unavailable.
    DEFAULT_FALLBACK = "Thank you for your message. Our team has been notified and will get back to you shortly."
    COMPLAINT_FALLBACK = "We’re very sorry about the inconvenience. Our support team has been alerted and will assist urgently."

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    async def get_response(
        self, 
        message: str, 
        property_id: str, 
        query_type: Optional[QueryType] = None
    ) -> Dict[str, Any]:
        """
        Fetches an AI-generated response based on property context and message intent.
        
        Args:
            message: The raw guest message.
            property_id: Unique identifier for the property context.
            query_type: Optional pre-classified intent to guide the AI.
            
        Returns:
            A dictionary containing the AI's response, confidence, and success status.
        """
        from app.config.constants import PROPERTY_CONTEXT_MAP
        context = PROPERTY_CONTEXT_MAP.get(property_id, "Unknown property context.")

        system_prompt = self._build_system_prompt(context)
        user_content = self._build_user_content(message, query_type)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
                timeout=10.0  # Strict timeout for better responsiveness
            )
            
            raw_text = response.content[0].text
            return self._parse_json_response(raw_text, query_type)            
        except (anthropic.APIStatusError, anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            return self._handle_api_error(e, query_type)

        except Exception as e:
            logger.exception(f"Unexpected internal failure in ClaudeService: {str(e)}")
            return self._build_failure_response("internal_error", query_type)

    def _build_system_prompt(self, context: str) -> str:
        """Constructs the system instructions for the AI."""
        return f"""
        You are a professional hospitality assistant for Nistula.
        
        Property Context:
        {context}
        
        Guidelines:
        1. Sound professional, concise, and hospitality-oriented.
        2. Avoid hallucinating unavailable information.
        3. Avoid making refund promises.
        4. Classify the message if not provided: 
           pre_sales_availability, pre_sales_pricing, post_sales_checkin, special_request, complaint, general_enquiry.
        
        Your response MUST be a valid JSON object with:
        - drafted_reply: Your professional response to the guest.
        - query_type: The classification of the message.
        - confidence: Your confidence score (0 to 1).
        """

    def _build_user_content(self, message: str, query_type: Optional[QueryType]) -> str:
        """Formats the guest message and optional intent for the AI."""
        content = f"Guest Message: {message}"
        if query_type:
            content += f"\nQuery Type: {query_type.value}"
        return content

    def _parse_json_response(self, text: str, query_type: Optional[QueryType] = None) -> Dict[str, Any]:
        """Extracts and parses JSON from the AI's raw text response."""
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                 raise ValueError("No JSON object found")
                 
            json_str = text[start:end]
            data = json.loads(json_str)
            
            # Patch 4: Validation
            if "drafted_reply" not in data or not data["drafted_reply"]:
                raise ValueError("AI response missing required 'drafted_reply'")
            
            # Safe default for confidence
            if "confidence" not in data:
                data["confidence"] = 0.5
                
            data["success"] = True
            return data
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Claude JSON validation failed: {str(e)} | Raw: {text[:100]}...")
            return self._build_failure_response("malformed_json", query_type)

    def _handle_api_error(self, e: Exception, query_type: Optional[QueryType]) -> Dict[str, Any]:
        """Categorizes and logs expected API failures, returning a safe fallback."""
        failure_type = "api_unavailable"
        status_code = getattr(e, "status_code", "N/A")
        
        if isinstance(e, anthropic.BadRequestError):
            failure_type = "billing_or_request_error"
        elif isinstance(e, anthropic.AuthenticationError):
            failure_type = "auth_error"
        elif isinstance(e, anthropic.RateLimitError):
            failure_type = "rate_limit_error"
        elif isinstance(e, anthropic.APITimeoutError):
            failure_type = "timeout"

        logger.error(f"Claude API expected failure | type={failure_type} status={status_code} msg={str(e)}")
        return self._build_failure_response(failure_type, query_type)

    def _build_failure_response(self, failure_type: str, query_type: Optional[QueryType]) -> Dict[str, Any]:
        """Constructs a standardized failure response with a hospitality-aware fallback."""
        drafted_reply = self.COMPLAINT_FALLBACK if query_type == QueryType.COMPLAINT else self.DEFAULT_FALLBACK
        
        return {
            "success": False,
            "failure_type": failure_type,
            "drafted_reply": drafted_reply,
            "query_type": query_type.value if query_type else "general_enquiry",
            "confidence": 0.0
        }

claude_service = ClaudeService()
