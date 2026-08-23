from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agent.orchestrator import run_turn
from app.agent.schemas import ChatResponse
from app.auth.dependencies import get_current_session
from app.auth.mock_auth import Session as UserSession
from app.db.session import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


@router.post("", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    try:
        from app.agent.intent_router import route_user_message, build_conversational_response
        route = route_user_message(req.message)
        if route.should_bypass_agent:
            conv_resp = build_conversational_response(route, session)
            return ChatResponse(**conv_resp)
        return run_turn(db, session, req.message)
    except Exception as e:
        return ChatResponse(
            answer=(
                "An unexpected error occurred while processing your request. "
                "The incident has been logged and escalated to human support."
            ),
            confidence=0.0,
            escalated=True,
            tool_trace=[],
            evidence=[],
        )
