"""Tools for FAQ (Frequently Asked Questions) handling."""

from langchain_core.tools import tool

# Dummy FAQs for the German energy market
FAQS = {
    "electricity_price": {
        "question": "How is my electricity price composed?",
        "answer": """The electricity price consists of several components:
1. **Energy costs** (~25%): Costs for electricity generation and procurement
2. **Network charges** (~25%): Fees for electricity transport through the grid
3. **Taxes and levies** (~50%):
   - Electricity tax
   - EEG levy (Renewable Energies)
   - Concession fee
   - Value-added tax (19%)"""
    },
    "provider_switching": {
        "question": "How do I switch my electricity provider?",
        "answer": """Switching providers is easy:
1. Select a new provider and sign a contract
2. The new provider handles the cancellation with the old provider
3. The switch usually takes 2-4 weeks
4. Electricity supply is guaranteed during the switch

**Important**: Check your cancellation period with your current provider!"""
    },
    "meter_reading": {
        "question": "How do I read my electricity meter?",
        "answer": """How to read your electricity meter correctly:
1. Locate your meter (usually in the basement or house connection room)
2. Note the **meter number** (printed on the meter)
3. Read the **meter reading** (only numbers before the decimal point)
4. For dual-tariff meters: Read HT (high tariff) and NT (night tariff) separately

**Tip**: Photograph the meter reading as proof!"""
    },
    "adjust_prepayment": {
        "question": "Can I have my prepayment adjusted?",
        "answer": """Yes, you can adjust your prepayment:
- **Increase**: Possible at any time to avoid additional payments
- **Reduction**: Possible with demonstrably lower consumption

Contact us with your request and current meter readings if applicable.
An adjustment typically takes effect from the following month."""
    },
    "power_outage": {
        "question": "What do I do in case of a power outage?",
        "answer": """In case of a power outage:
1. **Check**: Does it only affect your apartment or the entire building?
2. **Check fuses**: Check the fuse box
3. **Ask neighbors**: Is their power also out?
4. **For larger outages**: Contact the grid operator (not us as the electricity provider)

**Emergency number grid operator**: Can be found on your bill or on the internet."""
    },
    "smart_meter": {
        "question": "What is a Smart Meter?",
        "answer": """A **Smart Meter** (intelligent electricity meter) is a digital meter that:
- Automatically records electricity consumption in detail
- Digitally transmits data to the grid operator
- No longer requires manual reading
- Enables detailed consumption analyses

**Rollout**: By 2032, all households will be equipped with smart meters.
For consumption over 6,000 kWh/year, installation is mandatory."""
    },
    "understand_bill": {
        "question": "How do I read my electricity bill?",
        "answer": """Your electricity bill contains:
1. **Billing period**: Period of the billing
2. **Meter readings**: Starting and ending readings
3. **Consumption in kWh**: Difference between meter readings
4. **Working price**: Costs per kWh
5. **Basic price**: Fixed costs per month/year
6. **Prepayments already paid**: What you've already paid
7. **Additional payment/Credit**: Difference to actual consumption"""
    },
    "cancellation": {
        "question": "How do I cancel my electricity contract?",
        "answer": """Cancelling your electricity contract:
- **Cancellation period**: Stated in your contract terms (usually 4-6 weeks)
- **Special right of cancellation**: You can cancel immediately in case of price increases
- **Moving**: You have a special right of cancellation when moving

**Important**: Only cancel once you have a new provider, otherwise the basic supplier steps in (more expensive!)"""
    },
}


@tool
async def search_faq(search_term: str) -> dict:
    """
    Search through frequently asked questions for relevant answers.
    
    Args:
        search_term: The search term or topic to look for in FAQs.
    
    Returns:
        Matching FAQs with questions and answers.
    """
    search_lower = search_term.lower()
    matches = []
    
    for key, faq in FAQS.items():
        # Check if search term matches key, question, or answer
        if (search_lower in key.lower() or 
            search_lower in faq["question"].lower() or 
            search_lower in faq["answer"].lower()):
            matches.append({
                "topic": key,
                "question": faq["question"],
                "answer": faq["answer"]
            })
    
    return {
        "search_term": search_term,
        "matches_found": len(matches),
        "faqs": matches
    }


@tool
async def get_all_faq_topics() -> dict:
    """
    Get a list of all available FAQ topics.
    
    Returns:
        List of all FAQ topics with their questions.
    """
    topics = [
        {"topic": key, "question": faq["question"]}
        for key, faq in FAQS.items()
    ]
    
    return {
        "total_topics": len(topics),
        "topics": topics
    }


@tool
async def get_faq_by_topic(topic: str) -> dict:
    """
    Get a specific FAQ by its topic key.
    
    Args:
        topic: The topic key (e.g., "strompreis", "anbieterwechsel").
    
    Returns:
        The FAQ question and answer for the topic.
    """
    topic_lower = topic.lower()
    
    if topic_lower in FAQS:
        faq = FAQS[topic_lower]
        return {
            "found": True,
            "topic": topic_lower,
            "question": faq["question"],
            "answer": faq["answer"]
        }
    
    # Try partial match
    for key, faq in FAQS.items():
        if topic_lower in key:
            return {
                "found": True,
                "topic": key,
                "question": faq["question"],
                "answer": faq["answer"]
            }
    
    return {
        "found": False,
        "message": f"No FAQ found for topic '{topic}'.",
        "available_topics": list(FAQS.keys())
    }
