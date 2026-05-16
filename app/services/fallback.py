import re
from typing import Optional, Dict
from app.config.constants import PROPERTY_CONTEXT_MAP, QueryType

class FallbackService:
    @staticmethod
    def _parse_property_context(context_str: str) -> Dict[str, str]:
        """
        Parses the property context string into a dictionary for easier extraction.
        """
        context_dict = {}
        lines = context_str.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                context_dict[key.strip().lower()] = value.strip()
        return context_dict

    def generate_deterministic_response(
        self, 
        message: str, 
        query_type: QueryType, 
        property_id: str, 
        guest_name: str
    ) -> Optional[str]:
        """
        Generates a deterministic response from property context for factual queries.
        Returns None if no factual fallback matches.
        """
        context_str = PROPERTY_CONTEXT_MAP.get(property_id)
        if not context_str:
            return None

        context = self._parse_property_context(context_str)
        msg = message.lower()

        # Factual query detection and response generation
        if "wifi" in msg or "password" in msg:
            wifi_pass = context.get("wifi password")
            if wifi_pass:
                return f"Hi {guest_name}! The WiFi password for this property is {wifi_pass}."

        if "check-in" in msg or "checkin" in msg or "check in" in msg:
            check_in = context.get("check-in")
            if "early" in msg:
                return f"Hi {guest_name}! Early check-in requests are subject to availability. Standard check-in time is {check_in or '2pm'}. Our team will confirm availability with you shortly."
            if check_in:
                return f"Hi {guest_name}! Standard check-in time is {check_in}."

        if "check-out" in msg or "checkout" in msg or "check out" in msg:
            check_out = context.get("check-out")
            if "late" in msg:
                return f"Hi {guest_name}! Late check-out requests are subject to availability. Standard check-out time is {check_out or '11am'}. Our team will confirm availability with you shortly."
            if check_out:
                return f"Hi {guest_name}! Standard check-out time is {check_out}."

        if "caretaker" in msg:
            caretaker = context.get("caretaker")
            if caretaker:
                return f"Hi {guest_name}! Our caretaker is available: {caretaker}."

        if "cancellation" in msg or "cancel" in msg:
            cancellation = context.get("cancellation")
            if cancellation:
                return f"Hi {guest_name}! Our cancellation policy: {cancellation}."

        # If it's POST_SALES_CHECKIN but we couldn't find a specific match,
        # we can provide a general summary of check-in/wifi if available.
        if query_type == QueryType.POST_SALES_CHECKIN:
            check_in = context.get("check-in")
            wifi_pass = context.get("wifi password")
            if check_in and wifi_pass:
                return f"Hi {guest_name}! Standard check-in is {check_in} and the WiFi password is {wifi_pass}."

        return None

fallback_service = FallbackService()
