import logging
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status

from app.schemas.message import WebhookRequest, WebhookResponse
from app.models.message import NormalizedMessage
from app.services.classifier import classifier_service
from app.services.claude import claude_service
from app.services.scorer import scorer_service
from app.services.fallback import fallback_service
from app.config.constants import PROPERTY_ID_VILLA_B1, QueryType, ActionDecision

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post("/message", response_model=WebhookResponse)
async def handle_message(request: WebhookRequest):
    """
    Primary orchestration endpoint for processing inbound guest messages.
    
    This function coordinates classification, AI generation, and operational 
    routing. It implements high-reliability fallback mechanisms to ensure 
    guest queries are handled safely even during upstream service failures.
    """
    message_id = str(uuid4())
    log_prefix = f"[{message_id}]"
    
    logger.info(f"{log_prefix} Inbound {request.source} message for property: {request.property_id}")

    # 1. Context Validation
    if request.property_id != PROPERTY_ID_VILLA_B1:
        logger.error(f"{log_prefix} Unauthorized property_id: {request.property_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property '{request.property_id}' not found. Supported: '{PROPERTY_ID_VILLA_B1}'"
        )

    # 2. Intent Classification (Hybrid)
    # Start with fast keyword matching, fallback to AI classification later if needed.
    query_type, is_mixed = classifier_service.classify_by_keywords(request.message)
    was_ambiguous = (query_type is None)
    
    if not was_ambiguous:
        logger.info(f"{log_prefix} Keyword classification: {query_type.value} (Mixed: {is_mixed})")
    else:
        logger.info(f"{log_prefix} Keyword classification ambiguous, delegating to Claude.")

    # 3. Message Normalization (Requirement: Normalize before passing to AI)
    normalized = NormalizedMessage(
        message_id=message_id,
        source=request.source,
        guest_name=request.guest_name,
        message_text=request.message,
        timestamp=request.timestamp,
        booking_ref=request.booking_ref,
        property_id=request.property_id,
        query_type=query_type or QueryType.GENERAL_ENQUIRY
    )

    # 4. AI Generation & Failure Handling
    claude_result = await claude_service.get_response(
        message=normalized.message_text, 
        property_id=normalized.property_id, 
        query_type=query_type
    )
    
    claude_success = claude_result.get("success", False)
    drafted_reply = claude_result.get("drafted_reply")
    internal_reason = None
    forced_confidence = None

    # Graceful Degradation Logic
    if not claude_success:
        # Check if we can safely provide a deterministic factual answer
        factual_fallback_types = {
            QueryType.POST_SALES_CHECKIN,
            QueryType.GENERAL_ENQUIRY,
            QueryType.PRE_SALES_AVAILABILITY,
            QueryType.PRE_SALES_PRICING,
        }
        is_factual = query_type in factual_fallback_types
        is_safe_mixed_presales = (
            is_mixed
            and query_type in {
                QueryType.PRE_SALES_AVAILABILITY,
                QueryType.PRE_SALES_PRICING,
            }
        )
        
        if is_factual and (not is_mixed or is_safe_mixed_presales):
            logger.info(f"{log_prefix} Claude failure. Attempting deterministic factual fallback.")
            deterministic_reply = fallback_service.generate_deterministic_response(
                message=normalized.message_text,
                query_type=query_type,
                property_id=normalized.property_id,
                guest_name=normalized.guest_name
            )
            
            if deterministic_reply:
                internal_reason = "safe_factual_fallback_activated"
                drafted_reply = deterministic_reply
                forced_confidence = 0.95
                logger.info(f"{log_prefix} Deterministic fallback successful.")
            else:
                internal_reason = "no_specific_fallback_found"
        else:
            internal_reason = "mixed_intent_fallback_suppressed" if is_mixed else f"unsafe_type_fallback_suppressed_{query_type}"
            logger.warning(f"{log_prefix} Fallback suppressed: {internal_reason}")

    # Refine intent if keyword matching was ambiguous
    if was_ambiguous:
        ai_intent = claude_result.get("query_type")
        try:
            query_type = QueryType(ai_intent)
            logger.info(f"{log_prefix} Claude-resolved classification: {query_type.value}")
        except ValueError:
            query_type = QueryType.GENERAL_ENQUIRY
            logger.warning(f"{log_prefix} Claude-resolved intent invalid, defaulting to GENERAL_ENQUIRY.")

    # 4. Confidence Scoring & Routing Decision
    if forced_confidence is not None:
        final_confidence = forced_confidence
    else:
        final_confidence = scorer_service.calculate_confidence(
            query_type=query_type,
            claude_confidence=claude_result.get("confidence", 0.5),
            was_ambiguous=was_ambiguous,
            message_text=normalized.message_text,
            is_mixed=is_mixed
        )
    
    action = scorer_service.determine_action(query_type, final_confidence)
    
    # 5. Operational Safety Guard
    # Never auto-send generic fallback messages if the AI failed.
    if not claude_success and forced_confidence is None:
        if action == ActionDecision.AUTO_SEND:
            action = ActionDecision.AGENT_REVIEW
            logger.info(f"{log_prefix} Safety: Downgrading action to AGENT_REVIEW due to AI failure.")

    logger.info(
        f"{log_prefix} Routing Decision | "
        f"action={action.value} "
        f"confidence={final_confidence:.2f} "
        f"type={query_type.value} "
        f"claude_ok={claude_success} "
        f"failure={claude_result.get('failure_type')} "
        f"fallback_reason={internal_reason}"
    )

    # 6. Final Structured Response (Internal metadata kept in logs only)
    return WebhookResponse(
        message_id=message_id,
        query_type=query_type,
        drafted_reply=drafted_reply,
        confidence_score=round(final_confidence, 2),
        action=action
    )
