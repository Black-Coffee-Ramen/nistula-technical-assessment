from app.config.constants import (
    QueryType, ActionDecision, BASE_CONFIDENCE, 
    AUTO_SEND_THRESHOLD, AGENT_REVIEW_THRESHOLD
)

class ScorerService:
    """
    Engine for calculating confidence scores and determining operational actions.
    
    This service synthesizes AI confidence signals with deterministic business 
    safeguards to compute a final reliability score for a generated response. 
    It then maps this score to an operational action (Auto-send, Review, Escalate).
    """

    @staticmethod
    def calculate_confidence(
        query_type: QueryType, 
        claude_confidence: float, 
        was_ambiguous: bool,
        message_text: str,
        is_mixed: bool = False
    ) -> float:
        """
        Computes a final confidence score (0.0 to 1.0).
        
        Logic:
        1. Base score derived from the QueryType (defined in constants).
        2. Weighted blend of AI self-confidence (30%) and base logic (70%).
        3. Penalties applied for ambiguity, mixed intent, and high-risk terms.
        4. Strict cap applied if the AI service failed.
        """
        # 1. Base confidence from QueryType
        score = BASE_CONFIDENCE.get(query_type, 0.5)
        
        # 2. Weighted blend with AI confidence
        score = (score * 0.7) + (claude_confidence * 0.3)
        
        # 3. Penalties for operational uncertainty
        if was_ambiguous:
            score -= 0.1  # Moderate penalty for keyword-ambiguous messages
            
        if is_mixed:
            score -= 0.2  # Heavy penalty for multi-intent messages (risk of partial answer)

        # 4. Penalty for high-risk business terms
        if "refund" in message_text.lower():
            score -= 0.25
            
        # 5. Global cap for AI failures
        if claude_confidence == 0.0:
            score = min(score, 0.4) 

        # Ensure the final score stays within normalized bounds [0, 1]
        return max(0.0, min(1.0, score))

    @staticmethod
    def determine_action(query_type: QueryType, confidence: float) -> ActionDecision:
        """
        Maps a confidence score to a deterministic operational action.
        """
        # Critical business rule: All complaints must be escalated
        if query_type == QueryType.COMPLAINT:
            return ActionDecision.ESCALATE
            
        # Routing based on strict assessment thresholds
        if confidence > AUTO_SEND_THRESHOLD:
            return ActionDecision.AUTO_SEND
        elif confidence >= AGENT_REVIEW_THRESHOLD:
            return ActionDecision.AGENT_REVIEW
        else:
            return ActionDecision.ESCALATE

scorer_service = ScorerService()
