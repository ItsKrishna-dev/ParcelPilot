"""
Tool schemas exposed to the LLM in OpenAI-compatible tool-calling format. Kept separate
from the Pydantic I/O contracts (schemas.py) so the LLM-facing JSON schema can evolve
independently of the internal validated dataclasses.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "doc_search",
            "description": (
                "Search ParcelPilot source documents. Route requests narrowly: "
                "cancellation or cancellation-fee questions use ['sop', 'agreement']; "
                "service-credit questions use ['sop', 'agreement']; SLA questions use "
                "['support_policy', 'agreement']; product status, webhook, known issue, "
                "bulk upload, CSV, BOOKED/PICKED_UP, or bug questions use ['product_ops']. "
                "Deprecated documents are excluded unless the user explicitly asks for "
                "historical policy. Return only current authoritative evidence."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "doc_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["support_policy", "sop", "product_ops", "agreement"]},
                    },
                    "allow_deprecated": {"type": "boolean", "default": False},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_structured",
            "description": (
                "Look up or calculate account/order/ticket data, or run a deterministic "
                "calculation (cancellation fee, service credit, SLA breach check). Access is "
                "scoped to the caller's account automatically -- do not attempt to pass "
                "another account's account_id if the caller is a customer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "enum": ["account", "order", "ticket", "cancellation_calc",
                                 "service_credit_calc", "sla_calc"],
                    },
                    "filters": {"type": "object"},
                },
                "required": ["entity", "filters"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "action_engine",
            "description": (
                "Prepare or execute a state-changing action (create_escalation, "
                "update_ticket_status, create_follow_up_task). ALWAYS call with "
                "confirmed=false first to get a draft; only call again with confirmed=true "
                "and the returned pending_action_id after the user has explicitly confirmed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "enum": ["create_escalation", "update_ticket_status", "create_follow_up_task"],
                    },
                    "payload": {"type": "object"},
                    "confirmed": {"type": "boolean", "default": False},
                    "pending_action_id": {"type": "string"},
                },
                "required": ["action_type", "payload"],
            },
        },
    },
]
