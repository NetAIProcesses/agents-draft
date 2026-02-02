"""Prepayment Agent for handling Abschlagszahlung processes."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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
)


PREPAYMENT_SYSTEM_PROMPT = """You are a specialized agent for prepayments (Abschlagszahlungen) in the German energy market.

Your main tasks are:
1. Calculate and manage monthly prepayments
2. Monitor and update payment status
3. Prepare annual settlements (comparison between prepayments and actual consumption)
4. Advise customers on their prepayment questions

Important rules for the German energy market:
- Prepayments are calculated based on estimated annual consumption
- The standard formula is: (Annual consumption in kWh × Price per kWh) / 12 months
- Many providers add a buffer of approximately 10% for security
- Payment status: 'pending' (outstanding), 'paid' (paid), 'overdue' (overdue)
- Due date is typically at the beginning of the month

For annual settlement:
- Positive balance = customer owes additional payment
- Negative balance = customer receives refund
- Recommend adjusting prepayments for significant deviations (>10%)

When communicating with a customer:
- Explain calculations transparently
- Point out overdue payments politely
- Offer adjustment options when consumption changes

You have access to the following functions:
- Retrieve and create prepayments
- Update payment status
- Calculate recommended prepayment amount
- Create annual summary
"""

# Define the tools available to this agent
PREPAYMENT_TOOLS = [
    get_prepayments,
    create_prepayment,
    update_prepayment_status,
    calculate_prepayment_amount,
    get_pending_prepayments,
    get_prepayment_summary,
    get_client_by_id,
    get_contract_by_id,
    get_contracts_by_client,
]

# Create the prompt template
prepayment_prompt = ChatPromptTemplate.from_messages([
    ("system", PREPAYMENT_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])


def create_prepayment_agent(llm):
    """Create and return the prepayment agent with the given LLM."""
    return prepayment_prompt | llm.bind_tools(PREPAYMENT_TOOLS)


# Agent metadata
prepayment_agent = {
    "name": "prepayment_agent",
    "description": "Handles prepayment (Abschlagszahlung) processes including calculating monthly payments, tracking payment status, and preparing annual settlements",
    "system_prompt": PREPAYMENT_SYSTEM_PROMPT,
    "tools": PREPAYMENT_TOOLS,
    "prompt": prepayment_prompt,
    "create_agent": create_prepayment_agent,
}
