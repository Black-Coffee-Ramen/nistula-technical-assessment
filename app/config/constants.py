from enum import Enum

class MessageSource(str, Enum):
    WHATSAPP = "whatsapp"
    BOOKING_COM = "booking_com"
    AIRBNB = "airbnb"
    INSTAGRAM = "instagram"
    DIRECT = "direct"

class QueryType(str, Enum):
    PRE_SALES_AVAILABILITY = "pre_sales_availability"
    PRE_SALES_PRICING = "pre_sales_pricing"
    POST_SALES_CHECKIN = "post_sales_checkin"
    SPECIAL_REQUEST = "special_request"
    COMPLAINT = "complaint"
    GENERAL_ENQUIRY = "general_enquiry"

class ActionDecision(str, Enum):
    AUTO_SEND = "auto_send"
    AGENT_REVIEW = "agent_review"
    ESCALATE = "escalate"

# Property Context
PROPERTY_ID_VILLA_B1 = "villa-b1"
PROPERTY_CONTEXT_VILLA_B1 = """
Property: Villa B1, Assagao, North Goa
Bedrooms: 3
Max guests: 6
Private pool: Yes
Check-in: 2pm
Check-out: 11am
Base rate: INR 18,000 per night (up to 4 guests)
Extra guest: INR 2,000 per night per person
WiFi password: Nistula@2024
Caretaker: Available 8am to 10pm
Chef on call: Yes, pre-booking required
Availability April 20-24: Available
Cancellation: Free up to 7 days before check-in
"""

# Property Context Map
PROPERTY_CONTEXT_MAP = {
    PROPERTY_ID_VILLA_B1: PROPERTY_CONTEXT_VILLA_B1,
}
BASE_CONFIDENCE = {
    QueryType.POST_SALES_CHECKIN: 0.95,
    QueryType.PRE_SALES_AVAILABILITY: 0.90,
    QueryType.PRE_SALES_PRICING: 0.88,
    QueryType.GENERAL_ENQUIRY: 0.80,
    QueryType.SPECIAL_REQUEST: 0.70,
    QueryType.COMPLAINT: 0.40,
}

# Thresholds
AUTO_SEND_THRESHOLD = 0.85
AGENT_REVIEW_THRESHOLD = 0.60
