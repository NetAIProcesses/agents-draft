"""Orchestrator Agent for Multi-Agent System.

This agent routes customer requests to the appropriate specialized agent:
- Meter Reading Agent (Zählerstandserfassung)
- Prepayment Agent (Abschlagszahlung)  
- FAQ Agent (Häufig gestellte Fragen)
"""

from dataclasses import dataclass
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from ..config import config
from ..models import AgentType, CustomerContext, AgentResponse


@dataclass
class OrchestratorDeps:
    """Dependencies for the orchestrator."""
    
    customer_context: CustomerContext


class RoutingDecision(BaseModel):
    """Decision about which agent should handle the request."""
    
    agent_type: AgentType
    confidence: float
    reasoning: str
    extracted_info: dict | None = None


orchestrator_agent = Agent(
    config.get_model(),
    deps_type=OrchestratorDeps,
    output_type=RoutingDecision,
    instructions="""You are the orchestrator for a customer service system in the German energy market.

Your task is to analyze customer requests and route them to the appropriate agent.

Available agents:

1. **meter_reading** (Meter Reading)
   - Submit/report meter readings
   - Query reading history
   - Questions about reading meters
   - Move-in/move-out readings

2. **prepayment** (Prepayment/Advance Payment)
   - Query current prepayment amount
   - Adjust/change prepayment
   - Change payment method
   - Questions about payments

3. **faq** (Frequently Asked Questions)
   - General questions about electricity/gas
   - Contract questions
   - Tariff changes
   - Moving questions
   - Outage reports
   - Explanation of technical terms

Analyze the request and decide:
- Which agent is best suited
- How confident you are (0.0 to 1.0)
- Briefly justify your decision
- Extract relevant information (e.g., meter number, customer number)

When unclear: Choose the FAQ agent as fallback.
""",
)


@orchestrator_agent.tool
async def analyze_keywords(
    ctx: RunContext[OrchestratorDeps],
    message: str,
) -> dict:
    """Analysiere Schlüsselwörter in der Nachricht zur Kategorisierung.
    
    Args:
        message: Die Kundennachricht
    """
    message_lower = message.lower()
    
    meter_keywords = [
        "zählerstand", "zähler", "ablesung", "ablesen", "kwh", 
        "stand melden", "stromzähler", "gaszähler", "auszug", "einzug",
        "zählernummer", "meter", "verbrauch melden"
    ]
    
    prepayment_keywords = [
        "abschlag", "zahlung", "bezahlen", "lastschrift", "überweisung",
        "monatlich", "rate", "betrag", "iban", "bankverbindung",
        "zahlungsart", "abbuchung", "vorauszahlung"
    ]
    
    faq_keywords = [
        "frage", "wie", "was", "warum", "erkläre", "info",
        "vertrag", "kündigung", "tarif", "umzug", "störung",
        "rechnung", "ökostrom", "preis", "kosten"
    ]
    
    meter_score = sum(1 for kw in meter_keywords if kw in message_lower)
    prepayment_score = sum(1 for kw in prepayment_keywords if kw in message_lower)
    faq_score = sum(1 for kw in faq_keywords if kw in message_lower)
    
    return {
        "meter_reading_score": meter_score,
        "prepayment_score": prepayment_score,
        "faq_score": faq_score,
        "empfehlung": max(
            [("meter_reading", meter_score), 
             ("prepayment", prepayment_score), 
             ("faq", faq_score)],
            key=lambda x: x[1]
        )[0],
    }


@orchestrator_agent.tool
async def extract_identifiers(
    ctx: RunContext[OrchestratorDeps],
    message: str,
) -> dict:
    """Extrahiere Kennungen wie Kundennummer oder Zählernummer aus der Nachricht.
    
    Args:
        message: Die Kundennachricht
    """
    import re
    
    identifiers = {}
    
    # Customer number pattern: K-12345 or similar
    customer_match = re.search(r'K-?\d{4,8}', message, re.IGNORECASE)
    if customer_match:
        identifiers["kundennummer"] = customer_match.group().upper()
    
    # Meter number pattern: DE-001234567 or similar
    meter_match = re.search(r'DE-?\d{6,12}', message, re.IGNORECASE)
    if meter_match:
        identifiers["zaehlernummer"] = meter_match.group().upper()
    
    # Contract number pattern: V-12345
    contract_match = re.search(r'V-?\d{4,8}', message, re.IGNORECASE)
    if contract_match:
        identifiers["vertragsnummer"] = contract_match.group().upper()
    
    # Numeric values (potential meter readings or amounts)
    numbers = re.findall(r'\d+(?:[.,]\d+)?', message)
    if numbers:
        for num in numbers:
            num_val = float(num.replace(',', '.'))
            if num_val > 1000:  # Likely a meter reading
                identifiers["moeglicher_zaehlerstand"] = num_val
            elif num_val < 500:  # Likely a prepayment amount
                identifiers["moeglicher_betrag"] = num_val
    
    return identifiers


# Import the specialized agents for delegation
from .meter_reading_agent import meter_reading_agent, MeterReadingDeps
from .prepayment_agent import prepayment_agent, PrepaymentDeps
from .faq_agent import faq_agent, FAQDeps


async def handle_customer_request(
    message: str,
    customer_context: CustomerContext | None = None,
) -> AgentResponse:
    """Main entry point for handling customer requests.
    
    This function:
    1. Routes the request to the appropriate agent using the orchestrator
    2. Delegates to the specialized agent
    3. Returns a unified response
    
    Args:
        message: The customer's message
        customer_context: Optional customer context with identifiers
        
    Returns:
        Unified AgentResponse
    """
    if customer_context is None:
        customer_context = CustomerContext()
    
    # Step 1: Route the request
    orchestrator_deps = OrchestratorDeps(customer_context=customer_context)
    routing_result = await orchestrator_agent.run(message, deps=orchestrator_deps)
    routing = routing_result.output
    
    # Step 2: Delegate to the appropriate agent
    try:
        if routing.agent_type == AgentType.METER_READING:
            deps = MeterReadingDeps(customer_context=customer_context)
            result = await meter_reading_agent.run(message, deps=deps)
            response_data = {
                "success": result.output.success,
                "message": result.output.message,
                "confirmation_number": result.output.confirmation_number,
            }
            
        elif routing.agent_type == AgentType.PREPAYMENT:
            deps = PrepaymentDeps(customer_context=customer_context)
            result = await prepayment_agent.run(message, deps=deps)
            response_data = {
                "success": result.output.success,
                "message": result.output.message,
                "confirmation_number": result.output.confirmation_number,
            }
            
        else:  # FAQ as default
            deps = FAQDeps(customer_context=customer_context)
            result = await faq_agent.run(message, deps=deps)
            response_data = {
                "answer": result.output.answer,
                "category": result.output.category.value,
                "contact_required": result.output.contact_required,
            }
        
        return AgentResponse(
            agent_type=routing.agent_type,
            success=True,
            message=result.output.answer if hasattr(result.output, 'answer') else result.output.message,
            data=response_data,
            follow_up_required=getattr(result.output, 'contact_required', False),
            suggested_next_action=routing.reasoning,
        )
        
    except Exception as e:
        return AgentResponse(
            agent_type=routing.agent_type,
            success=False,
            message=f"Ein Fehler ist aufgetreten: {str(e)}. Bitte kontaktieren Sie unseren Kundenservice.",
            data={"error": str(e)},
            follow_up_required=True,
        )
