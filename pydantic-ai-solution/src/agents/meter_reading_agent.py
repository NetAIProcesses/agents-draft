"""Meter Reading Agent (Zählerstandserfassung).

This agent handles all meter reading related tasks for the German energy market:
- Submit new meter readings
- Query reading history
- Validate readings
- Handle move-in/move-out readings
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
import uuid

from pydantic_ai import Agent, RunContext

from ..config import config
from ..models import (
    MeterReadingResponse,
    MeterType,
    CustomerContext,
)


@dataclass
class MeterReadingDeps:
    """Dependencies for the meter reading agent."""
    
    customer_context: CustomerContext
    # In production, this would include database connections, API clients, etc.


# Simulated database of meter readings
_meter_readings_db: dict[str, list[dict]] = {
    "DE-001234567": [
        {
            "reading_value": Decimal("15234.5"),
            "reading_date": date(2025, 10, 15),
            "meter_type": MeterType.ELECTRICITY,
        },
        {
            "reading_value": Decimal("14890.2"),
            "reading_date": date(2025, 7, 15),
            "meter_type": MeterType.ELECTRICITY,
        },
    ],
    "DE-007654321": [
        {
            "reading_value": Decimal("8234.1"),
            "reading_date": date(2025, 11, 1),
            "meter_type": MeterType.GAS,
        },
    ],
}


meter_reading_agent = Agent(
    config.get_model(),
    deps_type=MeterReadingDeps,
    output_type=MeterReadingResponse,
    instructions="""You are an expert in meter reading management for the German energy market.
    
Your tasks:
- Help customers submit meter readings
- Validate readings for plausibility
- Answer questions about meter reading
- Support move-in/move-out readings

Important rules:
- Meter readings can never be lower than the previous reading
- Ask for clarification if values seem implausible (>50% deviation)
- Always record the reading date
- Provide special guidance for meter replacements

Always respond in English and be friendly and helpful.
""",
)


@meter_reading_agent.tool
async def submit_meter_reading(
    ctx: RunContext[MeterReadingDeps],
    meter_number: str,
    reading_value: float,
    meter_type: str = "strom",
    reading_date: str | None = None,
    is_move_out: bool = False,
    is_move_in: bool = False,
) -> dict:
    """Submit a new meter reading.
    
    Args:
        meter_number: The meter number (e.g., DE-001234567)
        reading_value: The current meter reading
        meter_type: Type of meter (strom=electricity, gas, wasser=water, waerme=heat)
        reading_date: Reading date in YYYY-MM-DD format (optional, default: today)
        is_move_out: True if this is a move-out reading
        is_move_in: True if this is a move-in reading
    """
    # Parse meter type
    try:
        m_type = MeterType(meter_type.lower())
    except ValueError:
        return {
            "success": False,
            "message": f"Unknown meter type: {meter_type}. Valid values: strom (electricity), gas, wasser (water), waerme (heat)",
        }
    
    # Parse reading date
    if reading_date:
        try:
            r_date = date.fromisoformat(reading_date)
        except ValueError:
            return {
                "success": False,
                "message": "Invalid date format. Please use YYYY-MM-DD.",
            }
    else:
        r_date = date.today()
    
    # Validate reading value
    reading_decimal = Decimal(str(reading_value))
    
    # Check against previous readings
    previous_readings = _meter_readings_db.get(meter_number, [])
    if previous_readings:
        last_reading = previous_readings[0]["reading_value"]
        if reading_decimal < last_reading:
            return {
                "success": False,
                "message": f"The meter reading ({reading_value}) is lower than the previous reading ({last_reading}). "
                          "Please verify your input. If the meter was replaced, please contact us.",
            }
        
        # Check for unusually high consumption
        consumption = reading_decimal - last_reading
        if consumption > last_reading * Decimal("0.5"):
            return {
                "success": False,
                "message": f"The consumption since the last reading ({consumption} kWh) seems unusually high. "
                          "Please verify the meter reading or contact our customer service.",
            }
    
    # Generate confirmation number
    confirmation = f"MR-{uuid.uuid4().hex[:8].upper()}"
    
    # Calculate estimated consumption
    estimated_consumption = None
    if previous_readings:
        estimated_consumption = reading_decimal - previous_readings[0]["reading_value"]
    
    # Store reading (simulated)
    if meter_number not in _meter_readings_db:
        _meter_readings_db[meter_number] = []
    
    _meter_readings_db[meter_number].insert(0, {
        "reading_value": reading_decimal,
        "reading_date": r_date,
        "meter_type": m_type,
        "is_move_out": is_move_out,
        "is_move_in": is_move_in,
        "confirmation": confirmation,
    })
    
    # Calculate next reading date
    next_reading = r_date + timedelta(days=180)  # 6 months
    
    reading_type = ""
    if is_move_in:
        reading_type = " (move-in reading)"
    elif is_move_out:
        reading_type = " (move-out reading)"
    
    return {
        "success": True,
        "message": f"Meter reading submitted successfully{reading_type}. Confirmation number: {confirmation}",
        "confirmation_number": confirmation,
        "estimated_consumption": float(estimated_consumption) if estimated_consumption else None,
        "next_reading_due": next_reading.isoformat(),
    }


@meter_reading_agent.tool
async def get_reading_history(
    ctx: RunContext[MeterReadingDeps],
    meter_number: str,
    limit: int = 5,
) -> dict:
    """Retrieve meter reading history.
    
    Args:
        meter_number: The meter number
        limit: Maximum number of results
    """
    readings = _meter_readings_db.get(meter_number, [])
    
    if not readings:
        return {
            "success": False,
            "message": f"No meter readings found for meter {meter_number}.",
            "readings": [],
        }
    
    # Format readings for display
    formatted_readings = []
    for r in readings[:limit]:
        formatted_readings.append({
            "date": r["reading_date"].isoformat(),
            "reading": float(r["reading_value"]),
            "type": r["meter_type"].value,
        })
    
    return {
        "success": True,
        "message": f"Found meter readings for {meter_number}:",
        "readings": formatted_readings,
    }


@meter_reading_agent.tool
async def validate_meter_number(
    ctx: RunContext[MeterReadingDeps],
    meter_number: str,
) -> dict:
    """Check if a meter number is valid.
    
    Args:
        meter_number: The meter number to validate
    """
    # Simple validation: German meter numbers typically start with DE-
    if not meter_number:
        return {
            "valid": False,
            "message": "Please enter a meter number.",
        }
    
    # Check format
    if meter_number.startswith("DE-") and len(meter_number) >= 10:
        return {
            "valid": True,
            "message": f"The meter number {meter_number} has a valid format.",
            "meter_exists": meter_number in _meter_readings_db,
        }
    
    return {
        "valid": False,
        "message": "The meter number should start with 'DE-' and have at least 10 characters.",
    }


@meter_reading_agent.tool
async def get_reading_tips(
    ctx: RunContext[MeterReadingDeps],
    meter_type: str = "strom",
) -> str:
    """Get tips for correctly reading your meter.
    
    Args:
        meter_type: Type of meter (strom=electricity, gas, wasser=water, waerme=heat)
    """
    tips = {
        "strom": """📊 Tips for Reading Your Electricity Meter:

1. **Note the meter number**: You'll find this on the meter's nameplate
2. **Read the meter value**: Read all digits before the decimal point
3. **For dual-rate meters**: Note both values (peak and off-peak)
4. **Digital meters**: Press the button if needed to display the current reading
5. **Take a photo**: We recommend taking a photo of the reading for your records

⚠️ Important: Do not include decimal places (usually marked in red).""",
        
        "gas": """🔥 Tips for Reading Your Gas Meter:

1. **Safety first**: The meter is usually located in the basement or utility room
2. **Only full cubic meters**: Read the black digits (not the red ones)
3. **Meter number**: Usually starts with a country code
4. **For modern meters**: Activate the display if needed

💡 Tip: A meter reader often comes for annual readings - but you can read it yourself anytime.""",
        
        "wasser": """💧 Tips for Reading Your Water Meter:

1. **Find the meter box**: Usually in the basement or garden (water pit)
2. **Read cubic meters**: The black numbers show full m³
3. **Ignore decimal places**: Don't include red digits
4. **Main water meter**: Only use this one for billing

🔧 In case of frost: Check if your meter is protected.""",
        
        "waerme": """🌡️ Tips for Reading Your Heat Meter:

1. **Activate display**: Often a button needs to be pressed
2. **Note the unit**: kWh or MWh - pay attention to the unit
3. **Non-return mechanism**: This meter can only count forward
4. **District heating**: Reading is usually done by the provider

📞 If unclear: Contact your heat provider.""",
    }
    
    return tips.get(meter_type.lower(), tips["strom"])
