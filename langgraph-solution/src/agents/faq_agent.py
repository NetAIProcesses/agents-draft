"""FAQ Agent for handling frequently asked questions about energy services."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.tools.faq_tools import (
    search_faq,
    get_all_faq_topics,
    get_faq_by_topic,
)


FAQ_SYSTEM_PROMPT = """You are a friendly FAQ agent for a German energy supply company.

Your main tasks are:
1. Answer frequently asked questions (FAQs)
2. Help customers with general energy-related questions
3. Explain information clearly and helpfully

Available FAQ topics:
- Electricity pricing and price composition
- Provider switching
- Meter reading (general information)
- Prepayment adjustment
- Power outage
- Smart meters
- Understanding bills
- Contract termination

Your approach:
1. Understand the customer's question
2. Search the FAQs for relevant information
3. Provide a clear, understandable answer
4. If no suitable FAQ exists, explain this politely and offer to forward the question to a colleague

Communication style:
- Friendly and helpful
- Explain technical terms clearly
- Use FAQ information as a basis, but phrase naturally
- Offer additional help for complex topics
"""

# Define the tools available to this agent
FAQ_TOOLS = [
    search_faq,
    get_all_faq_topics,
    get_faq_by_topic,
]

# Create the prompt template
faq_prompt = ChatPromptTemplate.from_messages([
    ("system", FAQ_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])


def create_faq_agent(llm):
    """Create and return the FAQ agent with the given LLM."""
    return faq_prompt | llm.bind_tools(FAQ_TOOLS)


# Agent metadata
faq_agent = {
    "name": "faq_agent",
    "description": "Handles frequently asked questions about energy services, pricing, contracts, and general information",
    "system_prompt": FAQ_SYSTEM_PROMPT,
    "tools": FAQ_TOOLS,
    "prompt": faq_prompt,
    "create_agent": create_faq_agent,
}
