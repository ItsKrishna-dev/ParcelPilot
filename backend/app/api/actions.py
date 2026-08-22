"""Direct REST endpoint for confirming a previously drafted action -- used by the frontend's
explicit 'Confirm' button so confirmation does not depend on the LLM remembering to ask."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.auth.dependencies import get_current_session
from app.auth.mock_auth import Session as UserSession
from app.agent.tools.action_engine_tool import run_action_engine
from app.agent.schemas import ActionEngineInput, ActionEngineOutput

router = APIRouter(prefix="/actions", tags=["actions"])


class ConfirmRequest(BaseModel):
    pending_action_id: str
    action_type: str
    payload: dict


@router.post("/confirm", response_model=ActionEngineOutput)
def confirm_action(req: ConfirmRequest, db: Session = Depends(get_db),
                    session: UserSession = Depends(get_current_session)):
    tool_input = ActionEngineInput(
        action_type=req.action_type, payload=req.payload,
        confirmed=True, pending_action_id=req.pending_action_id,
    )
    return run_action_engine(db, tool_input, actor_user_id=session.user_id, actor_role=session.role)
