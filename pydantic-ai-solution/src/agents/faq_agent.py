"""FAQ Agent (Häufig gestellte Fragen).

This agent handles common questions about the German energy market:
- Billing questions
- Contract questions
- Moving/relocation
- Tariff changes
- Payment issues
- Meter questions
- Green energy
"""

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from ..config import config
from ..models import (
    FAQCategory,
    FAQAnswer,
    CustomerContext,
)


@dataclass
class FAQDeps:
    """Dependencies for the FAQ agent."""
    
    customer_context: CustomerContext
    # In production: knowledge base API, search engine, etc.


# German Energy Market FAQ Knowledge Base (in English)
_faq_knowledge_base: dict[FAQCategory, list[dict]] = {
    FAQCategory.BILLING: [
        {
            "question": "When will I receive my annual bill?",
            "answer": "The annual bill is typically prepared 4-6 weeks after the billing period. "
                     "For most customers, this is in spring. You'll receive the bill by mail or, "
                     "if you use our online service, by email.",
            "keywords": ["annual", "bill", "invoice", "when", "receive"],
        },
        {
            "question": "What do the individual items on my bill mean?",
            "answer": "Your electricity bill contains: 1) **Energy price** (cost per kWh consumed), "
                     "2) **Base price** (monthly fixed costs), 3) **Grid fees** (for network usage), "
                     "4) **Taxes and levies** (EEG surcharge, electricity tax, concession fee). "
                     "The sum gives you your total amount.",
            "keywords": ["bill", "understand", "items", "energy price", "base price"],
        },
        {
            "question": "I have a very high back-payment. What can I do?",
            "answer": "For high back-payments you can: 1) Arrange installment payments (up to 6 monthly installments), "
                     "2) Have your prepayment adjusted for the future, 3) Have your meter reading verified. "
                     "Contact our customer service for individual solutions.",
            "keywords": ["back-payment", "high", "installment", "help"],
        },
    ],
    FAQCategory.CONTRACT: [
        {
            "question": "How can I cancel my contract?",
            "answer": "You can cancel your contract in writing (by letter, fax, or email). "
                     "Note the cancellation period in your contract terms (usually 4 weeks to month-end "
                     "after the minimum contract period). When moving, you often have a special cancellation right.",
            "keywords": ["cancellation", "contract", "cancel", "period"],
        },
        {
            "question": "What is the minimum contract period?",
            "answer": "The minimum contract period is 12 or 24 months depending on the tariff. "
                     "Basic supply tariffs have no minimum period and can be cancelled with 2 weeks notice. "
                     "Your personal contract period can be found in your contract confirmation.",
            "keywords": ["minimum", "contract", "period", "duration"],
        },
        {
            "question": "How do I switch to a different tariff?",
            "answer": "Switching tariffs is easy: 1) Choose your desired tariff on our website, "
                     "2) The switch usually takes effect at the next billing period, "
                     "3) For running contracts, we'll check the switching options for you. "
                     "Tariff switches are generally free of charge.",
            "keywords": ["tariff", "switch", "change"],
        },
    ],
    FAQCategory.MOVING: [
        {
            "question": "What do I need to consider when moving?",
            "answer": "When moving you should: 1) Inform us **3 weeks in advance**, "
                     "2) Read your **meter readings** (old and new) on moving day, "
                     "3) Create a **handover protocol** with landlord/buyer, "
                     "4) Provide your **new address** and new bank details if applicable. "
                     "We'll gladly transfer your contract to your new address.",
            "keywords": ["moving", "move out", "move in", "new apartment"],
        },
        {
            "question": "Can I take my contract with me when moving?",
            "answer": "Yes, in most cases you can take your contract to your new address. "
                     "If a different grid operator is responsible at the new location, there may be "
                     "minor price adjustments. When moving abroad, you have a special cancellation right.",
            "keywords": ["moving", "contract", "take with", "new address"],
        },
    ],
    FAQCategory.PAYMENT: [
        {
            "question": "What payment options are available?",
            "answer": "We offer the following payment methods: 1) **SEPA Direct Debit** (recommended - convenient and secure), "
                     "2) **Standing Order** (you keep control), "
                     "3) **Bank Transfer** (manual before each payment). "
                     "Direct debit is easiest for you and avoids late payment fees.",
            "keywords": ["payment", "direct debit", "transfer", "payment method"],
        },
        {
            "question": "What happens if I can't pay?",
            "answer": "If you have payment difficulties, please contact us early! We offer: "
                     "1) **Installment plans** for outstanding amounts, 2) **Deferment** in hardship cases, "
                     "3) **Prepayment adjustment** for persistently tight budgets. "
                     "Power disconnection only happens after multiple reminders and can often be avoided.",
            "keywords": ["payment", "difficulties", "cannot pay", "reminder", "disconnection"],
        },
    ],
    FAQCategory.METER: [
        {
            "question": "How do I read my meter?",
            "answer": "Here's how to read your meter: 1) Note the **meter number** (on the nameplate), "
                     "2) Read the **value** (only digits before the decimal point, usually black), "
                     "3) For **dual-rate meters**: note both values (peak/off-peak), "
                     "4) Report the reading online, via app, or by phone. "
                     "A photo of the meter reading is helpful for your records.",
            "keywords": ["meter", "read", "reading", "how"],
        },
        {
            "question": "What is a Smart Meter?",
            "answer": "A **Smart Meter** is a digital electricity meter that: "
                     "1) Transmits your consumption **automatically** to us, "
                     "2) Provides **detailed consumption data** (15-minute intervals), "
                     "3) Forms the basis for **flexible tariffs**. "
                     "Installation is mandatory for households >6,000 kWh/year or with solar panels.",
            "keywords": ["smart meter", "digital", "automatic"],
        },
    ],
    FAQCategory.GREEN_ENERGY: [
        {
            "question": "What is green electricity?",
            "answer": "**Green electricity** is generated from renewable energy sources: wind power, solar energy, "
                     "hydropower, and biomass. Our green electricity is **TÜV-certified** and actively contributes to "
                     "the energy transition. With every kWh you consume, you support the expansion of renewable energy.",
            "keywords": ["green", "renewable", "sustainable", "eco"],
        },
        {
            "question": "Is green electricity more expensive?",
            "answer": "Green electricity today is often **just as affordable** as conventional electricity or only slightly more expensive. "
                     "The price difference is usually only 1-2 cents per kWh. With our 'Green Basic' tariff "
                     "you pay only a small premium for 100% renewable energy.",
            "keywords": ["green", "price", "expensive", "cost"],
        },
        {
            "question": "How can I reduce my electricity consumption?",
            "answer": "Tips for saving electricity: 1) Use **LED bulbs** (up to 80% savings), "
                     "2) **Avoid standby** (use power strips with switches), "
                     "3) Buy **efficient appliances** (A+++ energy label), "
                     "4) **Wash clothes at 30°C**, 5) Don't set your **fridge** too cold (7°C is enough). "
                     "An average household can save 10-20% this way.",
            "keywords": ["save", "consumption", "reduce", "tips", "energy"],
        },
    ],
    FAQCategory.OUTAGE: [
        {
            "question": "What to do during a power outage?",
            "answer": "During a power outage: 1) First check your **fuses/circuit breakers**, "
                     "2) Ask your **neighbors** if they're also affected, "
                     "3) For larger outages: Report the issue at **0800-OUTAGE** (24/7), "
                     "4) Keep **flashlights** ready (no candles due to fire risk). "
                     "Current outages can be found on our website.",
            "keywords": ["power outage", "outage", "no power", "blackout"],
        },
    ],
    FAQCategory.TARIFF: [
        {
            "question": "What tariffs do you offer?",
            "answer": "Our tariff selection: 1) **Power Basic** - affordable basic tariff, "
                     "2) **Power Flex** - monthly cancellable, 3) **Green Basic** - 100% renewable, "
                     "4) **Green Plus** - with new plant funding, 5) **Heat Power** - for heat pumps. "
                     "All tariffs can be found on our website with a price calculator.",
            "keywords": ["tariff", "tariffs", "offer", "prices"],
        },
    ],
}


faq_agent = Agent(
    config.get_model(),
    deps_type=FAQDeps,
    output_type=FAQAnswer,
    instructions="""You are a friendly customer service expert for the German energy market.

Your tasks:
- Answer frequently asked questions about electricity and gas
- Explain complex topics in simple, understandable terms
- Refer to additional information when needed
- Redirect to the right contact person when necessary

Topic areas:
- Bills and invoicing
- Contracts and cancellations
- Moving and address changes
- Payments and prepayments
- Meters and readings
- Green energy and sustainability
- Outages and disruptions
- Tariff changes

Communication style:
- Friendly and helpful
- Clear and simple language
- Brief explanation for technical terms
- Respond in English

For questions you cannot answer, recommend customer service: 0800-123456
""",
)


@faq_agent.tool
async def search_faq(
    ctx: RunContext[FAQDeps],
    query: str,
    category: str | None = None,
) -> dict:
    """Search the FAQ knowledge base.
    
    Args:
        query: The customer's search query
        category: Optional category to filter by
    """
    query_lower = query.lower()
    results = []
    
    # Search in all categories or specific one
    categories_to_search = [FAQCategory(category)] if category else list(FAQCategory)
    
    for cat in categories_to_search:
        if cat not in _faq_knowledge_base:
            continue
            
        for faq in _faq_knowledge_base[cat]:
            # Check if query matches keywords or question
            score = 0
            for keyword in faq["keywords"]:
                if keyword in query_lower:
                    score += 1
            
            if score > 0 or any(word in faq["question"].lower() for word in query_lower.split()):
                results.append({
                    "question": faq["question"],
                    "answer": faq["answer"],
                    "category": cat.value,
                    "relevance": score,
                })
    
    # Sort by relevance
    results.sort(key=lambda x: x["relevance"], reverse=True)
    
    if not results:
        return {
            "success": False,
            "message": "Unfortunately, I couldn't find a matching answer. "
                      "Please contact our customer service at 0800-123456.",
            "results": [],
        }
    
    return {
        "success": True,
        "message": f"Found {len(results)} relevant answer(s):",
        "results": results[:3],  # Top 3 results
    }


@faq_agent.tool
async def get_category_info(
    ctx: RunContext[FAQDeps],
    category: str,
) -> dict:
    """Show all FAQs for a specific category.
    
    Args:
        category: The FAQ category (billing, contract, moving, tariff, payment, meter, outage, green_energy, general)
    """
    try:
        cat = FAQCategory(category.lower())
    except ValueError:
        categories = [c.value for c in FAQCategory]
        return {
            "success": False,
            "message": f"Unknown category: {category}. Available categories: {', '.join(categories)}",
        }
    
    faqs = _faq_knowledge_base.get(cat, [])
    
    if not faqs:
        return {
            "success": True,
            "message": f"No FAQs found in category '{cat.value}'.",
            "questions": [],
        }
    
    questions = [{"question": faq["question"]} for faq in faqs]
    
    return {
        "success": True,
        "message": f"FAQs in category '{cat.value}':",
        "questions": questions,
    }


@faq_agent.tool
async def get_contact_info(
    ctx: RunContext[FAQDeps],
    topic: str | None = None,
) -> dict:
    """Provide customer service contact information.
    
    Args:
        topic: Optional topic for specific contact details
    """
    contact_info = {
        "general": {
            "phone": "0800-123456",
            "hours": "Mon-Fri 8:00-20:00, Sat 8:00-14:00",
            "email": "customerservice@stadtwerke-example.de",
            "address": "Stadtwerke Example GmbH, Example Street 1, 12345 Example City",
        },
        "outage": {
            "phone": "0800-OUTAGE (0800-688243)",
            "hours": "24 hours, 7 days a week",
            "note": "If you smell gas: Open windows immediately, leave the building, call fire department (112)!",
        },
        "online": {
            "website": "www.stadtwerke-example.de",
            "customer_portal": "portal.stadtwerke-example.de",
            "app": "Available for iOS and Android",
        },
    }
    
    if topic and topic.lower() == "outage":
        return {
            "success": True,
            "message": "Outage hotline:",
            "contact": contact_info["outage"],
        }
    
    return {
        "success": True,
        "message": "Our contact options:",
        "contact": contact_info,
    }


@faq_agent.tool
async def explain_term(
    ctx: RunContext[FAQDeps],
    term: str,
) -> dict:
    """Explain a technical term from the energy sector.
    
    Args:
        term: The term to explain
    """
    glossary = {
        "energy price": "The energy price is the cost per consumed kilowatt-hour (kWh). "
                       "It makes up the largest part of your electricity costs and varies by tariff.",
        
        "base price": "The base price is a monthly flat fee regardless of consumption. "
                     "It covers the costs for meter, billing, and network provision.",
        
        "grid fee": "The grid fee is the charge for using the power grid. "
                   "It's collected by the network operator and passed on to you.",
        
        "eeg surcharge": "The EEG surcharge promotes the expansion of renewable energy in Germany. "
                        "It was reduced to 0 cents in 2023 but may rise again.",
        
        "electricity tax": "The electricity tax is a consumption tax on electricity (currently 2.05 cents/kWh). "
                          "It's levied by the state and included in the electricity price.",
        
        "kwh": "Kilowatt-hour (kWh) is the unit of measurement for energy. "
              "One kWh equals running a 1000-watt device for one hour.",
        
        "smart meter": "A Smart Meter is a digital electricity meter that automatically "
                      "transmits consumption data and enables detailed usage analysis.",
        
        "basic supply": "Basic supply is the legally guaranteed electricity tariff for all households. "
                       "It's often more expensive than special tariffs but always available.",
        
        "prepayment": "Prepayment is a monthly advance payment toward your annual electricity costs. "
                     "The actual consumption is settled in the annual bill.",
        
        "sepa direct debit": "SEPA direct debit is an automatic payment method. "
                            "We debit the amounts from your account on the due date.",
    }
    
    term_lower = term.lower().replace("-", "").replace(" ", "")
    
    # Search for term
    for key, explanation in glossary.items():
        if term_lower in key.replace("-", "").replace(" ", "") or key.replace("-", "").replace(" ", "") in term_lower:
            return {
                "success": True,
                "term": term,
                "explanation": explanation,
            }
    
    return {
        "success": False,
        "message": f"The term '{term}' is not in my glossary. "
                  "Please ask our customer service for an explanation.",
        "tip": "Perhaps you mean: " + ", ".join(list(glossary.keys())[:5]) + "...",
    }
