import asyncio
import json
from unittest.mock import patch, MagicMock
from app.services.claude import ClaudeService
from app.routes.webhook import handle_message
from app.schemas.message import WebhookRequest
from datetime import datetime
from app.config.constants import QueryType, ActionDecision

async def test_claude_failure_wifi_query():
    """
    Test Case A: Claude failure + WiFi query
    → deterministic factual response
    → auto_send allowed
    """
    print("\nRunning Test A: Claude failure + WiFi query")
    
    request = WebhookRequest(
        source="whatsapp",
        guest_name="John",
        message="What is the wifi password?",
        timestamp=datetime.now(),
        booking_ref="REF123",
        property_id="villa-b1"
    )

    # Mock ClaudeService to return a failure
    with patch("app.services.claude.claude_service.get_response", new_callable=MagicMock) as mock_claude:
        mock_claude.return_value = asyncio.Future()
        mock_claude.return_value.set_result({
            "success": False,
            "drafted_reply": "Generic fallback",
            "confidence": 0.0,
            "query_type": "general_enquiry"
        })

        response = await handle_message(request)
        
        print(f"Drafted Reply: {response.drafted_reply}")
        print(f"Action: {response.action}")
        print(f"Confidence: {response.confidence_score}")

        assert "Nistula@2024" in response.drafted_reply
        assert response.action == ActionDecision.AUTO_SEND
        assert response.confidence_score == 0.95
        print("PASS: Test A successful")

async def test_claude_failure_ambiguous_query():
    """
    Test Case B: Claude failure + ambiguous query
    → generic fallback
    → forced agent_review
    """
    print("\nRunning Test B: Claude failure + ambiguous query")
    
    request = WebhookRequest(
        source="whatsapp",
        guest_name="John",
        message="I have a strange question.",
        timestamp=datetime.now(),
        booking_ref="REF123",
        property_id="villa-b1"
    )

    # Mock ClaudeService to return a failure
    with patch("app.services.claude.claude_service.get_response", new_callable=MagicMock) as mock_claude:
        mock_claude.return_value = asyncio.Future()
        mock_claude.return_value.set_result({
            "success": False,
            "drafted_reply": "Generic fallback message.",
            "confidence": 0.0,
            "query_type": "general_enquiry"
        })

        response = await handle_message(request)
        
        print(f"Drafted Reply: {response.drafted_reply}")
        print(f"Action: {response.action}")
        print(f"Confidence: {response.confidence_score}")

        assert "Generic fallback message." in response.drafted_reply
        assert response.action in [ActionDecision.AGENT_REVIEW, ActionDecision.ESCALATE]
        assert response.action != ActionDecision.AUTO_SEND
        print("PASS: Test B successful")

async def test_complaint_query():
    """
    Test Case C: Complaint query
    → escalate unchanged
    """
    print("\nRunning Test C: Complaint query")
    
    request = WebhookRequest(
        source="whatsapp",
        guest_name="John",
        message="The AC is broken!",
        timestamp=datetime.now(),
        booking_ref="REF123",
        property_id="villa-b1"
    )

    # Even if Claude succeeds or fails, complaints should escalate
    with patch("app.services.claude.claude_service.get_response", new_callable=MagicMock) as mock_claude:
        mock_claude.return_value = asyncio.Future()
        mock_claude.return_value.set_result({
            "success": True,
            "drafted_reply": "I am sorry to hear that.",
            "confidence": 0.9,
            "query_type": "complaint"
        })

        response = await handle_message(request)
        
        print(f"Query Type: {response.query_type}")
        print(f"Action: {response.action}")

        assert response.query_type == QueryType.COMPLAINT
        assert response.action == ActionDecision.ESCALATE
        print("PASS: Test C successful")

async def test_claude_failure_availability_pricing_query():
    """
    Test Case D: Claude failure + availability/pricing query
    -> deterministic factual response from property context
    -> auto_send allowed because no speculative totals are computed
    """
    print("\nRunning Test D: Claude failure + availability/pricing query")

    request = WebhookRequest(
        source="whatsapp",
        guest_name="Rahul",
        message="Is the villa available from April 20 to 24? What is the rate for 2 adults?",
        timestamp=datetime.now(),
        booking_ref="REF123",
        property_id="villa-b1"
    )

    with patch("app.services.claude.claude_service.get_response", new_callable=MagicMock) as mock_claude:
        mock_claude.return_value = asyncio.Future()
        mock_claude.return_value.set_result({
            "success": False,
            "drafted_reply": "Generic fallback",
            "confidence": 0.0,
            "query_type": "pre_sales_availability"
        })

        response = await handle_message(request)

        print(f"Drafted Reply: {response.drafted_reply}")
        print(f"Action: {response.action}")
        print(f"Confidence: {response.confidence_score}")

        assert "available for April 20-24" in response.drafted_reply
        assert "base rate is INR 18,000" in response.drafted_reply
        assert response.query_type == QueryType.PRE_SALES_AVAILABILITY
        assert response.action == ActionDecision.AUTO_SEND
        assert response.confidence_score == 0.95
        print("PASS: Test D successful")

if __name__ == "__main__":
    asyncio.run(test_claude_failure_wifi_query())
    asyncio.run(test_claude_failure_ambiguous_query())
    asyncio.run(test_complaint_query())
    asyncio.run(test_claude_failure_availability_pricing_query())
