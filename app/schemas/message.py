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
    message_id: str
    query_type: QueryType
    drafted_reply: str
    confidence_score: float
    action: ActionDecision
    failure_type: Optional[str] = None
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
