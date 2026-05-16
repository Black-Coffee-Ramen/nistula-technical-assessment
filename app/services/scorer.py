from app.config.constants import (
    QueryType, ActionDecision, BASE_CONFIDENCE, 
    AUTO_SEND_THRESHOLD, AGENT_REVIEW_THRESHOLD
)

class ScorerService:
    @staticmethod
    def calculate_confidence(
        query_type: QueryType, 
        claude_confidence: float, 
        was_ambiguous: bool,
        message_text: str,
        is_mixed: bool = False
    ) -> float:
        # 1. Base confidence
        score = BASE_CONFIDENCE.get(query_type, 0.5)
        
        # 2. Adjust based on Claude's self-confidence
        # We weigh Claude's confidence at 30% and base logic at 70%
        score = (score * 0.7) + (claude_confidence * 0.3)
        
        # 3. Penalize if it was ambiguous (required Claude classification)
        if was_ambiguous:
            score -= 0.1
            
        # 4. Penalize mixed intent (Multiple topics detected)
        if is_mixed:
            score -= 0.2

        # 5. Handle Claude failure explicitly
        # If Claude fails, we should not boost confidence unless we have a deterministic fallback
        if claude_confidence == 0.0:
            score = min(score, 0.4) # Force low confidence on failure
            
        # 6. Detect refund requests in text (Heavy Penalty)
        if "refund" in message_text.lower():
            score -= 0.25
            
        # Clamp between 0 and 1
        return max(0.0, min(1.0, score))

    @staticmethod
    def decide_action(query_type: QueryType, confidence: float) -> ActionDecision:
        if query_type == QueryType.COMPLAINT:
            return ActionDecision.ESCALATE
            
        if confidence > AUTO_SEND_THRESHOLD:
            return ActionDecision.AUTO_SEND
        elif confidence >= AGENT_REVIEW_THRESHOLD:
            return ActionDecision.AGENT_REVIEW
        else:
            # Reserve ESCALATE for complaints/refunds or extremely low confidence
            # For most non-dangerous queries, AGENT_REVIEW is sufficient
            return ActionDecision.AGENT_REVIEW

scorer_service = ScorerService()
