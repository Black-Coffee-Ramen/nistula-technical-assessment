from typing import Optional
from app.config.constants import QueryType

class ClassifierService:
    """
    Service for fast keyword-based intent classification.
    
    This service acts as the first layer in the hybrid classification strategy.
    It provides low-latency, deterministic detection of common guest queries
    and critical operational issues like complaints.
    """

    # Mapping of QueryTypes to their associated trigger keywords.
    # Keywords are checked using case-insensitive partial matching.
    INTENT_KEYWORDS = {
        QueryType.COMPLAINT: [
            "not working", "broken", "issue", "problem", "unacceptable", 
            "refund", "bad", "terrible", "angry", "upset", "disappointed", 
            "complaint", "dirty", "no hot water", "ac not working", 
            "wifi not working", "slow wifi", "wifi slow", "poor service", 
            "disgusting", "faulty", "noise", "cooling", "properly", 
            "frustrating", "annoying", "leak", "smell", "failed", "fix", "slow"
        ],
        QueryType.PRE_SALES_AVAILABILITY: ["available", "availability", "vacant", "booked"],
        QueryType.PRE_SALES_PRICING: ["price", "rate", "cost", "how much", "charge"],
        QueryType.SPECIAL_REQUEST: [
            "early", "late", "airport", "transfer", "pickup", 
            "extra bed", "early check-in", "late check-out"
        ],
        QueryType.POST_SALES_CHECKIN: [
            "check-in", "checkin", "check in", "wifi", "password", 
            "wi-fi", "check-out", "checkout", "check out"
        ],
        QueryType.GENERAL_ENQUIRY: ["pet", "parking", "pool", "kitchen", "location"]
    }

    # Priority order for selecting the primary intent if multiple are detected.
    # Complaints and Special Requests take precedence over general enquiries.
    INTENT_PRIORITY = [
        QueryType.COMPLAINT,
        QueryType.SPECIAL_REQUEST,
        QueryType.PRE_SALES_AVAILABILITY,
        QueryType.PRE_SALES_PRICING,
        QueryType.POST_SALES_CHECKIN,
        QueryType.GENERAL_ENQUIRY
    ]

    @staticmethod
    def classify_by_keywords(message: str) -> tuple[Optional[QueryType], bool]:
        """
        Classifies a message based on pre-defined keyword mappings.
        
        Returns:
            - A tuple containing (PrimaryQueryType, is_mixed_intent)
            - is_mixed_intent is True if more than one query type was detected.
        """
        msg = message.lower()
        matched_types = set()
        
        # Identify all matching intents
        for q_type, keywords in ClassifierService.INTENT_KEYWORDS.items():
            if any(kw in msg for kw in keywords):
                matched_types.add(q_type)

        is_mixed = len(matched_types) > 1
        
        # Select the primary intent based on pre-defined operational priority
        for q_type in ClassifierService.INTENT_PRIORITY:
            if q_type in matched_types:
                return q_type, is_mixed

        return None, False  # No clear intent detected via keywords

classifier_service = ClassifierService()
