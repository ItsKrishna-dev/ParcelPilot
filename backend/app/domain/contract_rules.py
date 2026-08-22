"""
Contract-rule lookup and validation.

This module converts rows from contract_rules into calculation parameters.
It does not know any account-specific IDs or customer names.
"""

from dataclasses import dataclass

from app.db.models import ContractRule


@dataclass
class ContractOverrides:
    cancellation_fee_waived: bool | None = None
    cancellation_free_window_minutes: int | None = None
    cancellation_fee_inr: float | None = None

    service_credit_delay_threshold_hours: float | None = None
    service_credit_fixed_amount_inr: float | None = None
    service_credit_monthly_cap_inr: float | None = None

    sla_p1_minutes: int | None = None
    sla_p2_minutes: int | None = None
    sla_p3_minutes: int | None = None

    sources: list[str] | None = None


def resolve_contract_overrides(
    rules: list[ContractRule],
) -> ContractOverrides:
    overrides = ContractOverrides(sources=[])

    for rule in rules:
        key = rule.rule_key

        if rule.value_boolean is not None:
            value = rule.value_boolean
        else:
            value = rule.value_number

        if key == "cancellation_fee_waived":
            overrides.cancellation_fee_waived = bool(value)

        elif key == "cancellation_free_window_minutes":
            overrides.cancellation_free_window_minutes = int(value)

        elif key == "cancellation_fee_inr":
            overrides.cancellation_fee_inr = float(value)

        elif key == "service_credit_delay_threshold_hours":
            overrides.service_credit_delay_threshold_hours = float(value)

        elif key == "service_credit_fixed_amount_inr":
            overrides.service_credit_fixed_amount_inr = float(value)

        elif key == "service_credit_monthly_cap_inr":
            overrides.service_credit_monthly_cap_inr = float(value)

        elif key == "sla_p1_minutes":
            overrides.sla_p1_minutes = int(value)

        elif key == "sla_p2_minutes":
            overrides.sla_p2_minutes = int(value)

        elif key == "sla_p3_minutes":
            overrides.sla_p3_minutes = int(value)

        if rule.source_text:
            overrides.sources.append(rule.source_text)

    return overrides