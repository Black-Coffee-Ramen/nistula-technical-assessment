from typing import Optional
from app.config.constants import QueryType

class ClassifierService:
    @staticmethod
    def classify_by_keywords(message: str) -> tuple[Optional[QueryType], bool]:
        msg = message.lower()
        matched_types = set()
        
        # 1. PRIORITY: Complaint Detection
        COMPLAINT_KEYWORDS = [
            "not working", "broken", "issue", "problem", "unacceptable", 
            "refund", "bad", "terrible", "angry", "upset", "disappointed", 
            "complaint", "dirty", "no hot water", "ac not working", 
            "wifi not working", "slow wifi", "wifi slow", "poor service", "disgusting", "faulty",
            "noise", "cooling", "properly", "frustrating", "annoying",
            "leak", "smell", "failed", "broken", "fix", "slow"
        ]
        if any(kw in msg for kw in COMPLAINT_KEYWORDS):
            matched_types.add(QueryType.COMPLAINT)

        # 2. Pre-sales & Post-sales logic
        if any(kw in msg for kw in ["available", "availability", "vacant", "booked"]):
            matched_types.add(QueryType.PRE_SALES_AVAILABILITY)
        
        if any(kw in msg for kw in ["price", "rate", "cost", "how much", "charge"]):
            matched_types.add(QueryType.PRE_SALES_PRICING)
            
        if any(kw in msg for kw in ["early", "late", "airport", "transfer", "pickup", "extra bed", "early check-in", "late check-out"]):
            matched_types.add(QueryType.SPECIAL_REQUEST)
            
        if any(kw in msg for kw in ["check-in", "checkin", "check in", "wifi", "password", "wi-fi", "check-out", "checkout", "check out"]):
            matched_types.add(QueryType.POST_SALES_CHECKIN)
            
        if any(kw in msg for kw in ["pet", "parking", "pool", "kitchen", "location"]):
            matched_types.add(QueryType.GENERAL_ENQUIRY)

        is_mixed = len(matched_types) > 1
        
        # Priority ordering for the primary query type
        if QueryType.COMPLAINT in matched_types:
            return QueryType.COMPLAINT, is_mixed
        if QueryType.SPECIAL_REQUEST in matched_types:
            return QueryType.SPECIAL_REQUEST, is_mixed
        if QueryType.PRE_SALES_AVAILABILITY in matched_types:
            return QueryType.PRE_SALES_AVAILABILITY, is_mixed
        if QueryType.PRE_SALES_PRICING in matched_types:
            return QueryType.PRE_SALES_PRICING, is_mixed
        if QueryType.POST_SALES_CHECKIN in matched_types:
            return QueryType.POST_SALES_CHECKIN, is_mixed
        if QueryType.GENERAL_ENQUIRY in matched_types:
            return QueryType.GENERAL_ENQUIRY, is_mixed

        return None, False  # Ambiguous

classifier_service = ClassifierService()
