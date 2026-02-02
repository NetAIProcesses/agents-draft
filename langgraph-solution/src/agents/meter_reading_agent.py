"""Meter Reading Agent for handling Zählerablesung processes."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.tools.meter_reading_tools import (
    get_meter_readings,
    create_meter_reading,
    get_meters_by_contract,
    get_consumption_history,
    validate_meter_reading,
    get_meter_details,
)
from src.tools.common_tools import (
    get_client_by_id,
    get_contract_by_id,
    get_contracts_by_client,
)


METER_READING_SYSTEM_PROMPT = """You are a specialized agent for meter reading in the German energy market.

Your main tasks are:
1. Record and validate meter readings
2. Analyze consumption history
3. Detect and report anomalous readings
4. Assist customers with questions about their meter readings

Important rules for the German energy market:
- All consumption values are given in kWh
- Meter readings must be plausible (no negative values, no unrealistically high jumps)
- If in doubt about a reading, validate it against historical data
- Document the type of reading: 'actual' (customer reading/on-site) or 'estimated' (estimated value)

When communicating with a customer:
- Be polite and professional
- Explain technical terms clearly
- Offer concrete solutions to problems

You have access to the following functions:
- Retrieve and record meter readings
- Analyze consumption history
- Retrieve meter details
- Validate consumption readings
"""

# Define the tools available to this agent
METER_READING_TOOLS = [
    get_meter_readings,
    create_meter_reading,
    get_meters_by_contract,
    get_consumption_history,
    validate_meter_reading,
    get_meter_details,
    get_client_by_id,
    get_contract_by_id,
    get_contracts_by_client,
]

# Create the prompt template
meter_reading_prompt = ChatPromptTemplate.from_messages([
    ("system", METER_READING_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])


def create_meter_reading_agent(llm):
    """Create and return the meter reading agent with the given LLM."""
    return meter_reading_prompt | llm.bind_tools(METER_READING_TOOLS)


# Agent metadata
meter_reading_agent = {
    "name": "meter_reading_agent",
    "description": "Handles meter reading (Zählerablesung) processes including recording readings, validating consumption, and analyzing usage history",
    "system_prompt": METER_READING_SYSTEM_PROMPT,
    "tools": METER_READING_TOOLS,
    "prompt": meter_reading_prompt,
    "create_agent": create_meter_reading_agent,
}
