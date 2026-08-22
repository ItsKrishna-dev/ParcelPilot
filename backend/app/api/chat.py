from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.dependencies import get_current_session
from app.auth.mock_auth import Session as UserSession
from app.agent.orchestrator import run_turn
from app.agent.schemas import ChatResponse
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db),
         session: UserSession = Depends(get_current_session)):
    return run_turn(db, session, req.message)
