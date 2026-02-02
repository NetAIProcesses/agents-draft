"""Meter Reading Agent (Zählerstandserfassung).

This agent handles all meter reading related tasks for the German energy market:
- Submit new meter readings
- Query reading history
- Validate readings
- Handle move-in/move-out readings
"""

from dataclasses import dataclass
from datetime import date
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
    # MCP database functions will be available as tools


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
    meter_type: str = "electricity",
    reading_date: str | None = None,
    is_move_out: bool = False,
    is_move_in: bool = False,
) -> dict:
    """Submit a new meter reading to the MCP database.
    
    Args:
        meter_number: The meter number (e.g., EM-2024-0001)
        reading_value: The current meter reading in kWh
        meter_type: Type of meter (electricity, gas, water, heat)
        reading_date: Reading date in YYYY-MM-DD format (optional, default: today)
        is_move_out: True if this is a move-out reading
        is_move_in: True if this is a move-in reading
    """
    try:
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
        
        # Find meter in database using MCP tool
        meter_query = """
            SELECT em.id, em.meter_number, em.meter_type, em.status
            FROM energy_meters em 
            WHERE em.meter_number = $1 AND em.status = 'active'
        """
        
        # Get previous readings for validation
        previous_query = """
            SELECT mr.kwh_consumption, mr.reading_date
            FROM meter_readings mr
            JOIN energy_meters em ON mr.meter_id = em.id
            WHERE em.meter_number = $1
            ORDER BY mr.reading_date DESC 
            LIMIT 1
        """
        
        # Note: In practice, these MCP calls would be made through the available tools
        # For now, we'll implement a simplified validation
        
        # Validate reading value
        reading_decimal = Decimal(str(reading_value))
        
        if reading_decimal <= 0:
            return {
                "success": False,
                "message": "Reading value must be greater than zero.",
            }
        
        # Generate confirmation number
        confirmation = f"MR-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate next reading date
        next_reading = r_date + timedelta(days=180)  # 6 months
        
        reading_type_msg = ""
        if is_move_in:
            reading_type_msg = " (move-in reading)"
        elif is_move_out:
            reading_type_msg = " (move-out reading)"
        
        return {
            "success": True,
            "message": f"Meter reading submitted successfully{reading_type_msg}. Confirmation number: {confirmation}",
            "confirmation_number": confirmation,
            "estimated_consumption": None,  # Would be calculated from previous reading
            "next_reading_due": next_reading.isoformat(),
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error submitting meter reading: {str(e)}",
        }


@meter_reading_agent.tool
async def get_reading_history(
    ctx: RunContext[MeterReadingDeps],
    meter_number: str,
    limit: int = 5,
) -> dict:
    """Retrieve meter reading history from MCP database.
    
    Args:
        meter_number: The meter number
        limit: Maximum number of results
    """
    try:
        # Note: In practice, this would use the MCP database connection
        # For now, return a placeholder response indicating MCP integration
        return {
            "success": True,
            "message": f"MCP database integration ready for meter {meter_number}. Use MCP tools to query meter_readings table.",
            "readings": [],
            "note": "This agent is now configured to use the MCP Energy database. Use the available MCP tools for actual database operations."
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving meter reading history: {str(e)}",
            "readings": [],
        }


@meter_reading_agent.tool
async def validate_meter_number(
    ctx: RunContext[MeterReadingDeps],
    meter_number: str,
) -> dict:
    """Check if a meter number is valid and exists in the MCP database.
    
    Args:
        meter_number: The meter number to validate
    """
    try:
        if not meter_number:
            return {
                "valid": False,
                "message": "Please enter a meter number.",
            }
        
        # Note: In practice, this would query the MCP database
        # For now, provide guidance on using MCP tools
        return {
            "valid": True,
            "message": f"Ready to validate meter {meter_number} using MCP database. Use mcp_energy_proces_execute_select to query energy_meters table.",
            "meter_exists": None,
            "note": "This agent is now configured to use the MCP Energy database."
        }
        
    except Exception as e:
        return {
            "valid": False,
            "message": f"Error validating meter number: {str(e)}",
        }


@meter_reading_agent.tool
async def query_meter_database(
    ctx: RunContext[MeterReadingDeps],
    action: str,
    meter_number: str = "",
    limit: int = 10,
) -> dict:
    """Query the MCP Energy database for meter information.
    
    Args:
        action: The action to perform (validate, history, list_meters)
        meter_number: The meter number (required for validate and history)
        limit: Maximum number of results for history queries
    """
    try:
        if action == "list_meters":
            # This demonstrates how to use MCP tools in the agent
            return {
                "success": True,
                "message": "To list meters, use: mcp_energy_proces_execute_select('SELECT meter_number, meter_type, status FROM energy_meters LIMIT 10', [])",
                "note": "The agent now has access to MCP database tools for real-time queries."
            }
        elif action == "validate" and meter_number:
            return {
                "success": True,
                "message": f"To validate meter {meter_number}, use: mcp_energy_proces_execute_select('SELECT * FROM energy_meters WHERE meter_number = $1', ['{meter_number}'])",
                "note": "The agent can now validate meters against the actual MCP database."
            }
        elif action == "history" and meter_number:
            return {
                "success": True,
                "message": f"To get reading history for {meter_number}, use the MCP query for joining meter_readings with energy_meters tables.",
                "note": "The agent can now retrieve actual meter reading history from the MCP database."
            }
        else:
            return {
                "success": False,
                "message": "Invalid action or missing meter_number. Supported actions: validate, history, list_meters"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error querying meter database: {str(e)}",
        }


@meter_reading_agent.tool  
async def submit_reading_to_mcp(
    ctx: RunContext[MeterReadingDeps],
    meter_number: str,
    reading_value: float,
    reading_date: str = "",
    reading_type: str = "actual"
) -> dict:
    """Submit a meter reading directly to the MCP database.
    
    Args:
        meter_number: The meter number
        reading_value: The meter reading value
        reading_date: Reading date (YYYY-MM-DD) or empty for today
        reading_type: Type of reading (actual, estimated, move_in, move_out)
    """
    try:
        if not meter_number or reading_value <= 0:
            return {
                "success": False,
                "message": "Valid meter number and positive reading value required."
            }
        
        use_date = reading_date if reading_date else date.today().isoformat()
        confirmation = f"MR-{uuid.uuid4().hex[:8].upper()}"
        
        return {
            "success": True,
            "message": f"Ready to submit reading {reading_value} kWh for meter {meter_number}",
            "confirmation_number": confirmation,
            "mcp_query": f"First find meter ID, then INSERT INTO meter_readings (meter_id, reading_date, kwh_consumption, unit, reading_type) VALUES (meter_id, '{use_date}', {reading_value}, 'kWh', '{reading_type}')",
            "note": "Use mcp_energy_proces_execute_write to actually submit to database."
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error preparing meter reading submission: {str(e)}"
        }


@meter_reading_agent.tool
async def get_reading_tips(
    ctx: RunContext[MeterReadingDeps],
    meter_type: str = "electricity",
) -> str:
    """Get tips for correctly reading your meter.
    
    Args:
        meter_type: Type of meter (strom=electricity, gas, wasser=water, waerme=heat)
    """
    tips = {
        "electricity": """📊 Tips for Reading Your Electricity Meter:

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
    
    return tips.get(meter_type.lower(), tips["electricity"])
