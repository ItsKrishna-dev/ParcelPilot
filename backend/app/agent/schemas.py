"""
Pydantic I/O contracts for every tool. Validating tool inputs/outputs against a schema is
the guardrail that stops a malformed model-generated tool call from silently producing a
wrong number -- directly relevant given ParcelPilot/CalQuity is financial/logistics
infrastructure where a bad number is the real production risk, not a stylistic issue.
"""
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field


class ToolResultStatus:
    OK = "OK"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    ACCESS_DENIED = "ACCESS_DENIED"
    ESCALATE = "ESCALATE"


class MessageHistoryItem(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class DocSearchInput(BaseModel):
    query: str
    doc_types: Optional[list[str]] = None
    allow_deprecated: bool = False
    top_k: int = 5


class DocSearchOutput(BaseModel):
    status: str = ToolResultStatus.OK
    results: list[dict] = Field(default_factory=list)


class StructuredLookupInput(BaseModel):
    entity: Literal["account", "order", "ticket", "cancellation_calc", "service_credit_calc", "sla_calc"]
    filters: dict[str, Any] = Field(default_factory=dict)


class StructuredLookupOutput(BaseModel):
    status: str = ToolResultStatus.OK
    data: dict[str, Any] = Field(default_factory=dict)
    authority_source: Optional[str] = None
    reason: Optional[str] = None


class ActionEngineInput(BaseModel):
    action_type: Literal["create_escalation", "update_ticket_status", "create_follow_up_task"]
    payload: dict[str, Any]
    confirmed: bool = False
    pending_action_id: Optional[str] = None


class ActionEngineOutput(BaseModel):
    status: str = ToolResultStatus.OK
    pending_action_id: Optional[str] = None
    draft: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    message: str = ""


class ToolTraceEntry(BaseModel):
    tool_name: str
    input: dict[str, Any]
    output: dict[str, Any]
    latency_ms: float


class ChatResponse(BaseModel):
    answer: str
    confidence: Optional[float] = None
    escalated: bool
    tool_trace: list[ToolTraceEntry]
    evidence: list[dict[str, Any]] = Field(default_factory=list)

    answer_state: Optional[str] = None
    workflow_complete: Optional[bool] = None
    verification: Optional[str] = None
    operational_severity: Optional[str] = None
    escalation_required: Optional[bool] = None
    intent_category: Optional[str] = None
    intent_confidence: Optional[float] = None
    intent_method: Optional[str] = None
