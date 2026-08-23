"""API endpoint tests for /chat verifying response shape and error resilience."""

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.agent.llm_client import LLMProviderError

client = TestClient(app)


def test_chat_api_successful_response():
    with patch("app.agent.orchestrator.chat_completion") as mock_llm:
        mock_llm.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Northstar has a signed contract with custom terms.",
                        "tool_calls": None,
                    }
                }
            ]
        }

        resp = client.post(
            "/chat",
            headers={"Authorization": "Bearer cust-northstar"},
            json={"message": "What is our plan type?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "confidence" in data
        assert "escalated" in data
        assert "tool_trace" in data
        assert "evidence" in data


def test_chat_api_provider_failure_returns_200_with_escalation():
    with patch("app.agent.orchestrator.chat_completion") as mock_llm:
        mock_llm.side_effect = LLMProviderError("All providers rate limited (429)")

        resp = client.post(
            "/chat",
            headers={"Authorization": "Bearer cust-northstar"},
            json={"message": "Can I cancel my shipment?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["escalated"] is True
        assert data["confidence"] == 0.0
        assert "unable to reach" in data["answer"].lower() or "escalat" in data["answer"].lower()


def test_chat_api_unhandled_exception_returns_200_safe_response():
    with patch("app.api.chat.run_turn") as mock_turn:
        mock_turn.side_effect = RuntimeError("Simulated internal exception")

        resp = client.post(
            "/chat",
            headers={"Authorization": "Bearer cust-northstar"},
            json={"message": "Test error handling"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["escalated"] is True
        assert data["confidence"] == 0.0
        assert "unexpected error" in data["answer"].lower()


def test_chat_api_completed_ki211_response():
    with patch("app.agent.orchestrator.chat_completion") as mock_llm, patch("app.agent.orchestrator.run_doc_search") as mock_search:
        mock_search.return_value.model_dump.return_value = {
            "status": "OK",
            "results": [{"doc_id": "DOC-04", "text": "KI-211 SwiftShip delay", "score": 0.9}],
        }
        doc_search_call = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_doc",
                                "function": {
                                    "name": "doc_search",
                                    "arguments": '{"query": "KI-211 SwiftShip"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }
        msg_final = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "The Product Operations Guide documents that SwiftShip pickup-confirmation webhooks can arrive up to 20 minutes late (KI-211).",
                        "tool_calls": None,
                    }
                }
            ]
        }
        mock_llm.side_effect = [doc_search_call, msg_final]

        resp = client.post(
            "/chat",
            headers={"Authorization": "Bearer cust-northstar"},
            json={"message": "Why does the SwiftShip shipment still show BOOKED after driver picked it up?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "KI-211" in data["answer"]
        assert data["confidence"] >= 0.8


def test_chat_api_workflow_budget_exhaustion():
    # Mock LLM constantly returning tool calls without text answer until iterations exhaust
    tool_call_msg = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_loop",
                            "function": {
                                "name": "doc_search",
                                "arguments": '{"query": "SwiftShip"}',
                            },
                        }
                    ],
                }
            }
        ]
    }

    with patch("app.agent.orchestrator.chat_completion") as mock_llm:
        mock_llm.return_value = tool_call_msg
        resp = client.post(
            "/chat",
            headers={"Authorization": "Bearer cust-northstar"},
            json={"message": "Indefinite tool loop query"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "allotted tool-call budget" in data["answer"]
        assert data["confidence"] <= 0.25
        assert data["escalated"] is True


def test_chat_api_access_denied_other_account():
    resp = client.post(
        "/chat",
        headers={"Authorization": "Bearer cust-northstar"},
        json={"message": "Can I view cancellation fee for order ORD-2001?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence"] <= 0.55
    assert data["escalated"] is True
