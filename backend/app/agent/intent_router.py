"""Intent router to identify conversational/greeting messages and bypass the full agent RAG workflow."""

import re
import string
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from app.auth.mock_auth import Session as UserSession
from app.retrieval.hybrid_search import _try_load_embedder

class IntentCategory(str, Enum):
    GREETING = "greeting"
    ACKNOWLEDGEMENT = "acknowledgement"
    GENERAL_HELP = "general_help"
    SUPPORT_QUERY = "support_query"
    ACTION_REQUEST = "action_request"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class IntentRoute:
    category: IntentCategory
    confidence: float
    method: str
    should_bypass_agent: bool
    reason: str

OBVIOUS_GREETINGS = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening"}
OBVIOUS_ACKNOWLEDGEMENTS = {
    "thanks", "thank you", "okay", "ok", "got it", "perfect", "great", "awesome",
    "no", "nope", "nah", "yes", "yeah", "sure", "nevermind", "none", "stop", "cancel that"
}
OBVIOUS_HELP = {"help", "what can you do", "what do you support", "how can you help", "what can you help me with"}

# Small set of intent prototypes for Option A (SentenceTransformers)
PROTOTYPE_EXAMPLES = {
    IntentCategory.GREETING: [
        "hi there", "hello assistant", "yo", "hiya", "whats up", "greetings", "good day", "hey there"
    ],
    IntentCategory.ACKNOWLEDGEMENT: [
        "thank you very much", "thanks helper", "awesome", "great", "nice", "ok thanks", "got it thanks"
    ],
    IntentCategory.GENERAL_HELP: [
        "can you help me", "help guide", "what features do you support", "show capabilities", "what is your function"
    ],
}

DOMAIN_WORDS = {
    "cancel", "cancellation", "fee", "waive", "waiver",
    "credit", "eligibility", "eligible", "service credit", "failed pickup", "failed-pickup",
    "sla", "response target", "target", "breach", "breached",
    "booked", "picked up", "picked_up", "delivered", "driver", "webhook", "delay",
    "bulk", "csv", "upload", "escalate", "escalation", "ticket", "order",
    "support policy", "sop", "policy", "agreement", "contract",
    "shipment", "stuck", "status", "package", "carrier"
}

_prototype_vectors = {}

def _init_prototypes():
    global _prototype_vectors
    if _prototype_vectors:
        return
    embedder = _try_load_embedder()
    if embedder is None:
        return  # sentence-transformers not available — BM25-only mode
    try:
        import numpy as np
        for cat, examples in PROTOTYPE_EXAMPLES.items():
            vecs = embedder.encode(examples)
            mean_vec = np.mean(vecs, axis=0)
            norm = np.linalg.norm(mean_vec)
            if norm > 0:
                mean_vec = mean_vec / norm
            _prototype_vectors[cat] = mean_vec
    except Exception:
        pass

def normalize_text(text: str) -> str:
    cleaned = text.strip().lower()
    cleaned = cleaned.translate(str.maketrans("", "", string.punctuation))
    return cleaned.strip()

def has_domain_content(message: str) -> bool:
    normalized = message.lower()
    # 1. Regex checks for order/ticket/account/KI IDs
    if re.search(r"\bORD-\d+\b", normalized) or re.search(r"\bTKT-\d+\b", normalized) or re.search(r"\bACCT-\d+\b", normalized) or re.search(r"\bKI-\d+\b", normalized):
        return True
    # 2. Check for action keyword indicators or domain concepts
    for word in DOMAIN_WORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", normalized):
            return True
    return False

CONTEXT_FOLLOW_UP_PHRASES = {"no", "nope", "nah", "yes", "yeah", "sure", "proceed", "confirm", "cancel that"}
STANDALONE_ACKNOWLEDGEMENTS = {"thanks", "thank you", "okay", "ok", "got it", "perfect", "great", "awesome", "none", "nevermind", "stop"}

def route_user_message(message: str, history: Optional[list[dict]] = None) -> IntentRoute:
    # 1. Check domain content first as a safety override
    if has_domain_content(message):
        return IntentRoute(
            category=IntentCategory.SUPPORT_QUERY,
            confidence=1.0,
            method="deterministic_obvious",
            should_bypass_agent=False,
            reason="Contains domain keywords or record identifiers.",
        )

    # 2. Deterministic Obvious Check
    normalized = normalize_text(message)
    if normalized in OBVIOUS_GREETINGS:
        return IntentRoute(
            category=IntentCategory.GREETING,
            confidence=0.99,
            method="deterministic_obvious",
            should_bypass_agent=True,
            reason="Matched obvious greeting phrase.",
        )

    # If there is active conversation history with an assistant question/prompt,
    # route contextual follow-ups ("yes", "no", "proceed", etc.) to the agent with context.
    has_prior_assistant_turn = bool(
        history and any(h.get("role") == "assistant" and h.get("content") for h in history)
    )
    if has_prior_assistant_turn and normalized in CONTEXT_FOLLOW_UP_PHRASES:
        return IntentRoute(
            category=IntentCategory.SUPPORT_QUERY,
            confidence=0.95,
            method="contextual_follow_up",
            should_bypass_agent=False,
            reason="Contextual follow-up response to prior conversation turn.",
        )

    if normalized in OBVIOUS_ACKNOWLEDGEMENTS or normalized in STANDALONE_ACKNOWLEDGEMENTS or normalized in CONTEXT_FOLLOW_UP_PHRASES:
        return IntentRoute(
            category=IntentCategory.ACKNOWLEDGEMENT,
            confidence=0.99,
            method="deterministic_obvious",
            should_bypass_agent=True,
            reason="Matched obvious acknowledgement phrase.",
        )
    if normalized in OBVIOUS_HELP:
        return IntentRoute(
            category=IntentCategory.GENERAL_HELP,
            confidence=0.99,
            method="deterministic_obvious",
            should_bypass_agent=True,
            reason="Matched obvious general help request.",
        )

    # 3. Semantic local fallback (only when sentence-transformers is available)
    try:
        _init_prototypes()
        if _prototype_vectors:
            import numpy as np
            embedder = _try_load_embedder()
            if embedder is not None:
                query_vec = embedder.encode([normalized])[0]
                q_norm = np.linalg.norm(query_vec)
                if q_norm > 0:
                    query_vec = query_vec / q_norm

                scores = {}
                for cat, proto_vec in _prototype_vectors.items():
                    sim = float(np.dot(query_vec, proto_vec))
                    scores[cat] = sim

                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                top_cat, top_score = sorted_scores[0]
                second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0

                margin = top_score - second_score
                if (top_score >= 0.65 and margin >= 0.08) or (top_score >= 0.55 and margin >= 0.12):
                    return IntentRoute(
                        category=top_cat,
                        confidence=round(top_score, 2),
                        method="semantic_local",
                        should_bypass_agent=True,
                        reason=f"Semantic prototype match score: {top_score:.2f}",
                    )
    except Exception:
        pass

    return IntentRoute(
        category=IntentCategory.UNKNOWN,
        confidence=0.0,
        method="main_agent",
        should_bypass_agent=False,
        reason="Unclassified conversational query or potential support inquiry.",
    )

def build_conversational_response(route: IntentRoute, session: UserSession, user_message: str = "") -> dict:
    norm = normalize_text(user_message)
    if route.category == IntentCategory.GREETING:
        answer = "Hello! I’m here to help with your orders, cancellations, service credits, shipment status, and support questions."
    elif route.category == IntentCategory.ACKNOWLEDGEMENT:
        if norm in {"no", "nope", "nah", "nevermind", "none", "cancel that", "stop"}:
            answer = "Understood! Let me know whenever you're ready or if you have any other questions."
        elif norm in {"yes", "yeah", "sure"}:
            answer = "Great! Please let me know how I can assist you or which order or ticket you'd like to check."
        else:
            answer = "You're welcome! Let me know if you need anything else."
    elif route.category == IntentCategory.GENERAL_HELP:
        if session.role == "customer":
            answer = "I can help with your orders, cancellations, service credits, shipment status, and support questions."
        elif session.role == "support_agent":
            answer = "I can help investigate orders and tickets, review SLAs and known issues, and prepare support actions."
        elif session.role == "manager":
            answer = "I can help review support signals, policy decisions, SLA risk, audit activity, and escalations."
        else:
            answer = "I can help with B2B logistics queries, calculations, support tickets, and SLA status."
    else:
        answer = "Hello! Please let me know how I can assist you with your logistics operations."

    return {
        "answer": answer,
        "confidence": None,
        "escalated": False,
        "tool_trace": [],
        "evidence": [],
        "answer_state": "conversational",
        "workflow_complete": True,
        "verification": "not_required",
        "operational_severity": "info",
        "escalation_required": False,
        "intent_category": route.category.value,
        "intent_confidence": route.confidence,
        "intent_method": route.method,
    }
