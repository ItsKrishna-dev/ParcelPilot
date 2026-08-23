"""
Document routing module to assign correct document types based on query intent.
"""


def route_document_types(user_message: str) -> list[str] | None:
    text = (user_message or "").lower()

    product_terms = [
        "swiftship",
        "webhook",
        "still shows booked",
        "status not updated",
        "pickup status",
        "bulk upload",
        "csv",
        "rows",
        "known issue",
        "product issue",
        "bug",
    ]

    service_credit_terms = [
        "service credit",
        "failed pickup",
        "failed-pickup",
        "credit eligibility",
    ]

    cancellation_terms = [
        "cancel",
        "cancellation",
        "cancellation fee",
    ]

    sla_terms = [
        "sla",
        "response target",
        "response time",
        "breach",
        "breached",
    ]

    if any(term in text for term in product_terms):
        return ["product_ops"]

    if any(term in text for term in service_credit_terms):
        return ["sop", "agreement"]

    if any(term in text for term in cancellation_terms):
        return ["sop", "agreement"]

    if any(term in text for term in sla_terms):
        return ["support_policy", "agreement"]

    return None
