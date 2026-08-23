"""
Unit and integration tests for orchestrator guardrails and state machine transitions.
"""

from unittest.mock import patch
from app.agent.orchestrator import run_turn
from app.agent.schemas import ToolResultStatus
from app.auth.mock_auth import Session as UserSession


def test_orchestrator_reprompts_when_required_calculation_is_missing(db_session):
    session = UserSession(user_id="cust-northstar", role="customer", account_id="ACCT-001")

    # First response attempts to answer in prose without calling cancellation_calc
    msg_no_tool = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "You can cancel for free because Northstar has a contract.",
                    "tool_calls": None,
                }
            }
        ]
    }

    # Second response (after re-prompt) calls cancellation_calc
    msg_with_tool = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "lookup_structured",
                                "arguments": '{"entity": "cancellation_calc", "filters": {"order_id": "ORD-1001"}}',
                            },
                        }
                    ],
                }
            }
        ]
    }

    # Third response provides final answer with tool result
    msg_final = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Northstar can cancel ORD-1001 with 0 INR fee as verified by agreement authority.",
                    "tool_calls": None,
                }
            }
        ]
    }

    with patch("app.agent.orchestrator.chat_completion") as mock_llm:
        mock_llm.side_effect = [msg_no_tool, msg_with_tool, msg_final]
        response = run_turn(db_session, session, "Can Northstar cancel ORD-1001 without a cancellation fee?")

        assert mock_llm.call_count >= 2
        assert response.confidence >= 0.8
        assert not response.escalated
        assert any(t.tool_name == "lookup_structured" for t in response.tool_trace)


def test_orchestrator_handles_malformed_tool_json(db_session):
    session = UserSession(user_id="agent-rohit", role="support_agent", account_id=None)

    msg_bad_json = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_bad",
                            "function": {
                                "name": "lookup_structured",
                                "arguments": '{"entity": "order", "filters": INVALID_JSON}',
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
                    "content": "I encountered an error looking up that record.",
                    "tool_calls": None,
                }
            }
        ]
    }

    with patch("app.agent.orchestrator.chat_completion") as mock_llm:
        mock_llm.side_effect = [msg_bad_json, msg_final]
        response = run_turn(db_session, session, "Lookup order details")
        assert response is not None
        assert len(response.tool_trace) == 1
        assert response.tool_trace[0].output.get("status") in (
            ToolResultStatus.NEEDS_VERIFICATION,
            ToolResultStatus.OUT_OF_SCOPE,
        )


def test_orchestrator_handles_empty_content(db_session):
    session = UserSession(user_id="agent-rohit", role="support_agent", account_id=None)

    msg_empty = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": None,
                }
            }
        ]
    }

    with patch("app.agent.orchestrator.chat_completion") as mock_llm:
        mock_llm.return_value = msg_empty
        response = run_turn(db_session, session, "Status check")
        assert response.escalated is True
        assert len(response.answer) > 0
