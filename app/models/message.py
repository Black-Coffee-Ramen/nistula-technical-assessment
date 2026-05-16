from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from app.config.constants import MessageSource, QueryType

class NormalizedMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    source: MessageSource
    guest_name: str
    message_text: str
    timestamp: datetime
    booking_ref: str
    property_id: str
    query_type: QueryType
