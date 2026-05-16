from fastapi import APIRouter, HTTPException, status
from app.schemas.message import WebhookRequest, WebhookResponse
from app.models.message import NormalizedMessage
from app.services.classifier import classifier_service
from app.services.claude import claude_service
from app.services.scorer import scorer_service
from app.config.constants import PROPERTY_ID_VILLA_B1, QueryType, ActionDecision

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post("/message", response_model=WebhookResponse)
async def handle_message(request: WebhookRequest):
    # 0. Generate Initial Context
    from uuid import uuid4
    message_id = str(uuid4())
    
    logger.info(f"[{message_id}] Received message from {request.source} for property {request.property_id}")

    # 1. Property Validation
    if request.property_id != PROPERTY_ID_VILLA_B1:
        logger.error(f"[{message_id}] Invalid property_id: {request.property_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property '{request.property_id}' not found. Only '{PROPERTY_ID_VILLA_B1}' is supported."
        )

    # 2. Hybrid Classification
    logger.info(f"[{message_id}] Starting hybrid classification")
    query_type, is_mixed = classifier_service.classify_by_keywords(request.message)
    was_ambiguous = query_type is None
    
    if not was_ambiguous:
        logger.info(f"[{message_id}] Keyword classification successful: {query_type}")
        if is_mixed:
            logger.info(f"[{message_id}] Mixed intent detected.")
    else:
        logger.info(f"[{message_id}] Keyword classification ambiguous, falling back to Claude")

    # 3. AI Interaction & Classification Fallback
    claude_result = await claude_service.get_response(
        message=request.message, 
        property_id=request.property_id, 
        query_type=query_type
    )
    
    claude_success = claude_result.get("success", False)
    drafted_reply = claude_result.get("drafted_reply")

    internal_reason = None
    if not claude_success:
        # 1. Determine if it's safe to use a deterministic factual fallback
        is_safe_factual_type = query_type in [QueryType.POST_SALES_CHECKIN, QueryType.GENERAL_ENQUIRY]
        
        if is_safe_factual_type and not is_mixed:
            logger.info(f"[{message_id}] Claude API failure detected. Attempting deterministic fallback.")
            from app.services.fallback import fallback_service
            deterministic_reply = fallback_service.generate_deterministic_response(
                message=request.message,
                query_type=query_type,
                property_id=request.property_id,
                guest_name=request.guest_name
            )
            
            if deterministic_reply:
                internal_reason = "safe_factual_fallback_activated"
                logger.info(f"[{message_id}] Internal Reason: {internal_reason}")
                drafted_reply = deterministic_reply
                forced_confidence = 0.95
            else:
                internal_reason = "no_specific_fallback_found"
                logger.info(f"[{message_id}] Internal Reason: {internal_reason}")
                forced_confidence = None
        else:
            internal_reason = "mixed_intent_fallback_suppressed" if is_mixed else f"unsafe_type_fallback_suppressed_{query_type}"
            logger.warning(f"[{message_id}] Internal Reason: {internal_reason}")
            forced_confidence = None
    else:
        forced_confidence = None

    if was_ambiguous:
        # Fallback to Claude's classification if keyword matching failed
        ai_query_type = claude_result.get("query_type")
        try:
            query_type = QueryType(ai_query_type)
            logger.info(f"[{message_id}] Claude classification successful: {query_type}")
        except ValueError:
            query_type = QueryType.GENERAL_ENQUIRY
            logger.warning(f"[{message_id}] Claude classification invalid or missing, defaulting to GENERAL_ENQUIRY")

    # 4. Normalization (Internal Record)
    normalized = NormalizedMessage(
        message_id=message_id,
        source=request.source,
        guest_name=request.guest_name,
        message_text=request.message,
        timestamp=request.timestamp,
        booking_ref=request.booking_ref,
        property_id=request.property_id,
        query_type=query_type
    )

    # 5. Confidence Scoring & Action Decision
    logger.info(f"[{message_id}] Calculating confidence score")
    
    if forced_confidence is not None:
        final_confidence = forced_confidence
    else:
        final_confidence = scorer_service.calculate_confidence(
            query_type=query_type,
            claude_confidence=claude_result.get("confidence", 0.5),
            was_ambiguous=was_ambiguous,
            message_text=request.message,
            is_mixed=is_mixed
        )
    
    action = scorer_service.decide_action(query_type, final_confidence)
    
    # Critical Operational Safeguard: 
    # If Claude failed AND no deterministic fallback was found, NEVER auto_send.
    if not claude_success and forced_confidence is None:
        if action == ActionDecision.AUTO_SEND:
            action = ActionDecision.AGENT_REVIEW
            logger.info(f"[{message_id}] Safeguard: Claude failed and no fallback. Downgrading AUTO_SEND to AGENT_REVIEW.")

    logger.info(
        f"[{message_id}] Final Decision | "
        f"action={action.value} "
        f"confidence={final_confidence:.2f} "
        f"query_type={query_type.value if query_type else 'none'} "
        f"is_mixed={is_mixed} "
        f"claude_success={claude_success}"
    )

    # 6. Response
    return WebhookResponse(
        message_id=normalized.message_id,
        query_type=query_type,
        drafted_reply=drafted_reply,
        confidence_score=round(final_confidence, 2),
        action=action,
        failure_type=claude_result.get("failure_type"),
        is_fallback=(forced_confidence is not None),
        fallback_reason=internal_reason if not claude_success else None
    )
