"""Prepayment Agent (Abschlagszahlung).

This agent handles all prepayment related tasks for the German energy market:
- Query current prepayment amount
- Request prepayment adjustments
- Calculate recommended prepayment
- Manage payment methods
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import uuid

from pydantic_ai import Agent, RunContext

from ..config import config
from ..models import (
    PrepaymentAdjustmentResponse,
    PrepaymentFrequency,
    PaymentMethod,
    CustomerContext,
)


@dataclass
class PrepaymentDeps:
    """Dependencies for the prepayment agent."""
    
    customer_context: CustomerContext
    # MCP database functions will be available as tools


prepayment_agent = Agent(
    config.get_model(),
    deps_type=PrepaymentDeps,
    output_type=PrepaymentAdjustmentResponse,
    instructions="""You are an expert in prepayment/advance payment management for the German energy market.

Your tasks:
- Inform customers about their current prepayment amount
- Calculate recommended prepayment adjustments
- Process change requests
- Explain the different payment methods

Important rules:
- The prepayment should cover the estimated annual consumption
- Warn if prepayment is too low (back-payment risk)
- Point out potential refunds if prepayment is too high
- Minimum prepayment: 25 EUR per month
- Maximum adjustment: ±50% without review

Annual cost calculation:
- (Annual consumption × energy price) + (base price × 12) = annual costs
- Monthly prepayment = annual costs ÷ 12

Always respond in English and be friendly and helpful.
""",
)


@prepayment_agent.tool
async def get_current_prepayment(
    ctx: RunContext[PrepaymentDeps],
    contract_number: str,
) -> dict:
    """Retrieve current prepayment information from MCP database.
    
    Args:
        contract_number: The contract number (e.g., CONT-2024-001)
    """
    try:
        # Query contract and client information
        query = """
            SELECT c.contract_number, c.annual_consumption_kwh, c.unit_price_eur_kwh, c.status,
                   cl.name, cl.email,
                   p.payment_amount_eur, p.payment_status, p.due_date
            FROM contracts c
            JOIN clients cl ON c.client_id = cl.id
            LEFT JOIN prepayment p ON c.id = p.contract_id 
                AND p.year = EXTRACT(YEAR FROM CURRENT_DATE)
                AND p.month = TO_CHAR(CURRENT_DATE, 'Month')
            WHERE c.contract_number = $1 AND c.status = 'active'
        """
        
        # Note: In practice, this would use the MCP database connection
        # For now, return a placeholder response indicating MCP integration
        return {
            "success": True,
            "message": f"MCP database integration ready for contract {contract_number}. Use MCP tools to query contracts and prepayment tables.",
            "data": {
                "contract_number": contract_number,
                "note": "This agent is now configured to use the MCP Energy database. Use the available MCP tools for actual database operations."
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving prepayment information: {str(e)}",
        }


@prepayment_agent.tool
async def calculate_recommended_prepayment(
    ctx: RunContext[PrepaymentDeps],
    contract_number: str,
    new_annual_consumption: float | None = None,
) -> dict:
    """Calculate the recommended prepayment amount using MCP database.
    
    Args:
        contract_number: The contract number
        new_annual_consumption: Optional new estimated annual consumption in kWh
    """
    try:
        # Note: In practice, this would query the MCP database for contract details
        # For now, provide guidance on using MCP tools
        return {
            "success": True,
            "message": f"Ready to calculate prepayment for contract {contract_number}.",
            "calculation": {
                "note": "Use MCP tools to query contracts table for annual_consumption_kwh and unit_price_eur_kwh, then calculate: (consumption × price) ÷ 12 months",
                "mcp_query": f"SELECT annual_consumption_kwh, unit_price_eur_kwh FROM contracts WHERE contract_number = '{contract_number}'",
                "formula": "monthly_prepayment = (annual_consumption_kwh × unit_price_eur_kwh) ÷ 12"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error calculating prepayment: {str(e)}",
        }


@prepayment_agent.tool
async def request_prepayment_adjustment(
    ctx: RunContext[PrepaymentDeps],
    contract_number: str,
    new_amount: float,
    reason: str | None = None,
) -> dict:
    """Request a change in prepayment amount using MCP database.
    
    Args:
        contract_number: The contract number
        new_amount: The desired new prepayment amount in EUR
        reason: Optional reason for the adjustment
    """
    try:
        new_amount_decimal = Decimal(str(new_amount))
        
        # Validate minimum
        if new_amount_decimal < Decimal("25"):
            return {
                "success": False,
                "message": "The minimum prepayment is 25 EUR per month.",
            }
        
        # Generate confirmation and dates
        confirmation = f"PA-{uuid.uuid4().hex[:8].upper()}"
        effective_date = date.today() + timedelta(days=14)  # 2 weeks notice
        current_month = date.today().strftime("%B")
        current_year = date.today().year
        
        return {
            "success": True,
            "message": "Prepayment adjustment request prepared.",
            "details": {
                "new_prepayment": float(new_amount_decimal),
                "effective_from": effective_date.isoformat(),
                "confirmation_number": confirmation,
                "reason": reason or "Customer request",
                "note": "Use MCP tools to update or insert into prepayment table",
                "mcp_query": f"UPDATE prepayment SET payment_amount_eur = {new_amount} WHERE contract_id = (SELECT id FROM contracts WHERE contract_number = '{contract_number}') AND month = '{current_month}' AND year = {current_year}"
            },
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing prepayment adjustment: {str(e)}",
        }


@prepayment_agent.tool
async def change_payment_method(
    ctx: RunContext[PrepaymentDeps],
    contract_number: str,
    new_method: str,
    iban: str | None = None,
) -> dict:
    """Change the payment method for prepayments using MCP database.
    
    Args:
        contract_number: The contract number
        new_method: New payment method (direct_debit, bank_transfer, standing_order)
        iban: IBAN for direct debit (required only for direct_debit)
    """
    try:
        # Validate payment method
        valid_methods = ["direct_debit", "bank_transfer", "standing_order"]
        if new_method.lower() not in valid_methods:
            return {
                "success": False,
                "message": f"Invalid payment method: {new_method}. Valid options: {', '.join(valid_methods)}",
            }
        
        # Validate IBAN for direct debit
        if new_method.lower() == "direct_debit":
            if not iban:
                return {
                    "success": False,
                    "message": "For direct debit, we need your IBAN.",
                }
            # Simple IBAN validation
            if not iban.startswith("DE") or len(iban) != 22:
                return {
                    "success": False,
                    "message": "Please enter a valid German IBAN (DE + 20 digits).",
                }
        
        confirmation = f"PM-{uuid.uuid4().hex[:8].upper()}"
        
        result = {
            "success": True,
            "message": "Payment method change request prepared.",
            "details": {
                "new_payment_method": new_method,
                "confirmation_number": confirmation,
                "note": "Use MCP tools to update client or add payment method information to database",
                "contract_number": contract_number
            },
        }
        
        if new_method.lower() == "direct_debit":
            result["details"]["sepa_note"] = (
                "The SEPA direct debit mandate will be sent to you by mail. "
                "The switch will take effect after we receive the signed mandate."
            )
        elif new_method.lower() == "bank_transfer":
            result["details"]["payment_info"] = {
                "recipient": "Stadtwerke Musterstadt GmbH",
                "iban": "DE89 3704 0044 0532 0130 00",
                "reference": f"Prepayment {contract_number}",
            }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error changing payment method: {str(e)}",
        }


@prepayment_agent.tool
async def get_payment_history(
    ctx: RunContext[PrepaymentDeps],
    contract_number: str,
    months: int = 6,
) -> dict:
    """Retrieve payment history from MCP database.
    
    Args:
        contract_number: The contract number
        months: Number of months for the history
    """
    try:
        # Note: In practice, this would query the MCP database for payment history
        # For now, provide guidance on using MCP tools
        return {
            "success": True,
            "message": f"Ready to retrieve payment history for contract {contract_number} for the last {months} months.",
            "data": {
                "note": "Use MCP tools to query prepayment table for historical payment data",
                "mcp_query": f"SELECT month, year, payment_amount_eur, payment_status, payment_date, due_date FROM prepayment WHERE contract_id = (SELECT id FROM contracts WHERE contract_number = '{contract_number}') ORDER BY year DESC, month DESC LIMIT {months}",
                "contract_number": contract_number
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving payment history: {str(e)}",
        }


@prepayment_agent.tool
async def query_prepayment_database(
    ctx: RunContext[PrepaymentDeps],
    action: str,
    contract_number: str = "",
    year: int = 0,
    month: str = "",
) -> dict:
    """Query the MCP Energy database for prepayment information.
    
    Args:
        action: The action to perform (current, history, outstanding, all_contracts)
        contract_number: The contract number (required for specific queries)
        year: Year for filtering (optional)
        month: Month for filtering (optional)
    """
    try:
        current_year = date.today().year
        current_month = date.today().strftime("%B")
        
        if action == "current" and contract_number:
            return {
                "success": True,
                "message": f"To get current prepayment for {contract_number}:",
                "mcp_query": f"SELECT p.payment_amount_eur, p.payment_status, p.due_date, c.annual_consumption_kwh, c.unit_price_eur_kwh FROM prepayment p JOIN contracts c ON p.contract_id = c.id WHERE c.contract_number = '{contract_number}' AND p.year = {current_year} AND p.month = '{current_month}'",
                "note": "Use mcp_energy_proces_execute_select to run this query"
            }
        elif action == "outstanding":
            return {
                "success": True,
                "message": "To find outstanding prepayments:",
                "mcp_query": "SELECT c.contract_number, p.payment_amount_eur, p.due_date, p.month, p.year FROM prepayment p JOIN contracts c ON p.contract_id = c.id WHERE p.payment_status = 'pending' AND p.due_date < CURRENT_DATE",
                "note": "This shows overdue prepayments across all contracts"
            }
        elif action == "all_contracts":
            return {
                "success": True,
                "message": "To list all contracts with current prepayment status:",
                "mcp_query": f"SELECT c.contract_number, cl.name, p.payment_amount_eur, p.payment_status FROM contracts c JOIN clients cl ON c.client_id = cl.id LEFT JOIN prepayment p ON c.id = p.contract_id AND p.year = {current_year} AND p.month = '{current_month}' WHERE c.status = 'active'",
                "note": "Shows all active contracts and their current prepayment status"
            }
        elif action == "history" and contract_number:
            query_year = year if year > 0 else current_year
            return {
                "success": True,
                "message": f"To get prepayment history for {contract_number}:",
                "mcp_query": f"SELECT month, year, payment_amount_eur, payment_status, payment_date, due_date FROM prepayment WHERE contract_id = (SELECT id FROM contracts WHERE contract_number = '{contract_number}') AND year = {query_year} ORDER BY month",
                "note": f"Shows prepayment history for year {query_year}"
            }
        else:
            return {
                "success": False,
                "message": "Invalid action or missing parameters. Supported actions: current, history, outstanding, all_contracts"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error querying prepayment database: {str(e)}",
        }


@prepayment_agent.tool  
async def submit_prepayment_to_mcp(
    ctx: RunContext[PrepaymentDeps],
    contract_number: str,
    payment_amount: float,
    month: str = "",
    year: int = 0,
    payment_status: str = "pending"
) -> dict:
    """Submit or update a prepayment entry in the MCP database.
    
    Args:
        contract_number: The contract number
        payment_amount: The prepayment amount in EUR
        month: Month name (e.g., "February") or empty for current month
        year: Year or 0 for current year
        payment_status: Payment status (pending, paid, overdue)
    """
    try:
        if not contract_number or payment_amount <= 0:
            return {
                "success": False,
                "message": "Valid contract number and positive payment amount required."
            }
        
        use_month = month if month else date.today().strftime("%B")
        use_year = year if year > 0 else date.today().year
        due_date = date.today() + timedelta(days=30)  # 30 days from now
        
        confirmation = f"PP-{uuid.uuid4().hex[:8].upper()}"
        
        return {
            "success": True,
            "message": f"Ready to submit prepayment {payment_amount} EUR for contract {contract_number}",
            "confirmation_number": confirmation,
            "details": {
                "contract_number": contract_number,
                "payment_amount": payment_amount,
                "month": use_month,
                "year": use_year,
                "due_date": due_date.isoformat(),
                "status": payment_status
            },
            "mcp_queries": {
                "find_contract": f"SELECT id FROM contracts WHERE contract_number = '{contract_number}'",
                "insert_prepayment": f"INSERT INTO prepayment (contract_id, month, year, forecasted_consumption_kwh, unit_price_eur_kwh, payment_amount_eur, payment_status, due_date) VALUES (contract_id, '{use_month}', {use_year}, 0, 0, {payment_amount}, '{payment_status}', '{due_date}')",
                "note": "Use mcp_energy_proces_execute_write to insert the prepayment record"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error preparing prepayment submission: {str(e)}"
        }


@prepayment_agent.tool
async def calculate_prepayment_from_mcp(
    ctx: RunContext[PrepaymentDeps],
    contract_number: str,
    new_annual_consumption: float = 0,
) -> dict:
    """Calculate prepayment using live data from MCP database.
    
    Args:
        contract_number: The contract number
        new_annual_consumption: Override consumption estimate (kWh) or 0 to use contract value
    """
    try:
        return {
            "success": True,
            "message": f"To calculate prepayment for {contract_number}:",
            "calculation_steps": [
                "1. Query contract: SELECT annual_consumption_kwh, unit_price_eur_kwh FROM contracts WHERE contract_number = ?",
                "2. Calculate annual cost: consumption × price",
                "3. Calculate monthly prepayment: annual_cost ÷ 12",
                "4. Round up to nearest EUR"
            ],
            "mcp_query": f"SELECT annual_consumption_kwh, unit_price_eur_kwh FROM contracts WHERE contract_number = '{contract_number}'",
            "formula": "monthly_prepayment = CEILING((annual_consumption_kwh × unit_price_eur_kwh) ÷ 12)",
            "note": "Use mcp_energy_proces_execute_select to get contract data, then apply the formula"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error calculating prepayment: {str(e)}"
        }
