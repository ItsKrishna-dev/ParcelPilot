"""
Unit tests for document type query routing.
"""

from app.domain.query_routing import route_document_types


def test_routing_product_ops_queries():
    assert route_document_types("Why does the SwiftShip shipment still show BOOKED after the driver picked it up?") == ["product_ops"]
    assert route_document_types("Why is my 4,200-row Growth CSV upload failing?") == ["product_ops"]
    assert route_document_types("We experienced a webhook delay") == ["product_ops"]


def test_routing_service_credit_queries():
    assert route_document_types("Is ORD-2002 eligible for a failed pickup service credit?") == ["sop", "agreement"]


def test_routing_cancellation_queries():
    assert route_document_types("What is the fee to cancel order ORD-1001?") == ["sop", "agreement"]


def test_routing_sla_queries():
    assert route_document_types("What is the SLA target for P1 tickets?") == ["support_policy", "agreement"]
