"""Tools for LangGraph agents."""

from src.tools.meter_reading_tools import (
    get_meter_readings,
    create_meter_reading,
    get_meters_by_contract,
    get_consumption_history,
    validate_meter_reading,
    get_meter_details,
)

from src.tools.prepayment_tools import (
    get_prepayments,
    create_prepayment,
    update_prepayment_status,
    calculate_prepayment_amount,
    get_pending_prepayments,
    get_prepayment_summary,
)

from src.tools.common_tools import (
    get_client_by_id,
    get_contract_by_id,
    get_contracts_by_client,
    search_clients,
    get_client_with_contracts,
)

from src.tools.faq_tools import (
    search_faq,
    get_all_faq_topics,
    get_faq_by_topic,
)

__all__ = [
    # Meter reading tools
    "get_meter_readings",
    "create_meter_reading",
    "get_meters_by_contract",
    "get_consumption_history",
    "validate_meter_reading",
    "get_meter_details",
    # Prepayment tools
    "get_prepayments",
    "create_prepayment",
    "update_prepayment_status",
    "calculate_prepayment_amount",
    "get_pending_prepayments",
    "get_prepayment_summary",
    # Common tools
    "get_client_by_id",
    "get_contract_by_id",
    "get_contracts_by_client",
    "search_clients",
    "get_client_with_contracts",
    # FAQ tools
    "search_faq",
    "get_all_faq_topics",
    "get_faq_by_topic",
]
