from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.config.constants import MessageSource, QueryType, ActionDecision

class WebhookRequest(BaseModel):
    source: MessageSource
    guest_name: str
    message: str = Field(..., min_length=1)
    timestamp: datetime
    booking_ref: str
    property_id: str

class WebhookResponse(BaseModel):
    message_id: str = Field(..., description="Unique correlation ID for the message lifecycle")
    query_type: QueryType = Field(..., description="Primary detected intent of the guest message")
    drafted_reply: str = Field(..., description="The AI-generated or deterministic hospitality response")
    confidence_score: float = Field(..., description="System confidence in the drafted reply (0.0 to 1.0)")
    action: ActionDecision = Field(..., description="Recommended operational action (auto_send, agent_review, escalate)")
