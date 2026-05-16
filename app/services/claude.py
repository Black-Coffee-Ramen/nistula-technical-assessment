import anthropic
import json
import logging
from typing import Optional, Dict, Any
from app.config.settings import settings
from app.config.constants import QueryType

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    async def get_response(self, message: str, property_id: str, query_type: Optional[QueryType] = None) -> Dict[str, Any]:
        """
        Gets a response from Claude using property-specific context.
        """
        from app.config.constants import PROPERTY_CONTEXT_MAP
        context = PROPERTY_CONTEXT_MAP.get(property_id, "Unknown property context.")

        system_prompt = f"""
        You are a professional hospitality assistant for Nistula.
        
        Property Context:
        {context}
        
        Guidelines:
        1. Sound professional, concise, and hospitality-oriented.
        2. Avoid hallucinating unavailable information.
        3. Avoid making refund promises.
        4. If you are unsure of the query type, choose from: 
           pre_sales_availability, pre_sales_pricing, post_sales_checkin, special_request, complaint, general_enquiry.
        
        Your response MUST be a valid JSON object with the following keys:
        - drafted_reply: Your professional response to the guest.
        - query_type: (Only if not provided) The classification of the message.
        - confidence: Your self-confidence score (0 to 1) for this response.
        """
        
        user_content = f"Guest Message: {message}"
        if query_type:
            user_content += f"\nQuery Type: {query_type.value}"

        try:
            # Added 10-second timeout for responsiveness
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
                timeout=10.0
            )
            
            # Extract JSON from response
            text = response.content[0].text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                 raise ValueError("No JSON object found in response")
                 
            json_str = text[start:end]
            json_data = json.loads(json_str)
            json_data["success"] = True
            return json_data
            
        except (anthropic.APIStatusError, anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            # Categorize the failure for metrics/observability
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

            logger.error(
                f"Claude API expected failure | type={failure_type} status={status_code} msg={str(e)}"
            )

            # Fallback reply logic
            drafted_reply = "Thank you for your message. Our team has been notified and will get back to you shortly."
            if query_type == QueryType.COMPLAINT:
                drafted_reply = "We’re very sorry about the inconvenience. Our support team has been alerted and will assist urgently."
                
            return {
                "success": False,
                "failure_type": failure_type,
                "drafted_reply": drafted_reply,
                "query_type": query_type.value if query_type else "general_enquiry",
                "confidence": 0.0
            }

        except Exception as e:
            # Unexpected internal failures (e.g. JSON corruption, parser bugs)
            logger.exception(f"Unexpected error in ClaudeService: {str(e)}")
            return {
                "success": False,
                "failure_type": "internal_error",
                "drafted_reply": "Thank you for your message. Our team has been notified and will get back to you shortly.",
                "query_type": query_type.value if query_type else "general_enquiry",
                "confidence": 0.0
            }

claude_service = ClaudeService()
