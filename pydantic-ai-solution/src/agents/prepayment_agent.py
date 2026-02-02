"""Prepayment Agent (Abschlagszahlung).

This agent handles all prepayment related tasks for the German energy market:
- Query current prepayment amount
- Request prepayment adjustments
- Calculate recommended prepayment
- Manage payment methods
"""

from dataclasses import dataclass
from datetime import date, timedelta
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
    # In production: database connections, payment APIs, etc.


# Simulated customer database
_customer_db: dict[str, dict] = {
    "K-12345": {
        "name": "Max Mustermann",
        "contract_number": "V-98765",
        "current_prepayment": Decimal("95.00"),
        "frequency": PrepaymentFrequency.MONTHLY,
        "payment_method": PaymentMethod.DIRECT_DEBIT,
        "next_payment_date": date(2026, 3, 1),
        "annual_consumption": Decimal("3500"),  # kWh
        "tariff": "ÖkoStrom Basis",
        "price_per_kwh": Decimal("0.32"),
        "base_price_monthly": Decimal("9.90"),
    },
    "K-67890": {
        "name": "Erika Musterfrau",
        "contract_number": "V-54321",
        "current_prepayment": Decimal("150.00"),
        "frequency": PrepaymentFrequency.MONTHLY,
        "payment_method": PaymentMethod.BANK_TRANSFER,
        "next_payment_date": date(2026, 3, 15),
        "annual_consumption": Decimal("5200"),  # kWh
        "tariff": "Strom Flex",
        "price_per_kwh": Decimal("0.34"),
        "base_price_monthly": Decimal("12.90"),
    },
}


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
    customer_number: str,
) -> dict:
    """Retrieve current prepayment information.
    
    Args:
        customer_number: The customer number (e.g., K-12345)
    """
    customer = _customer_db.get(customer_number)
    
    if not customer:
        return {
            "success": False,
            "message": f"Customer with number {customer_number} not found. "
                      "Please verify your customer number.",
        }
    
    return {
        "success": True,
        "message": "Current prepayment information:",
        "data": {
            "customer": customer["name"],
            "contract_number": customer["contract_number"],
            "current_prepayment": float(customer["current_prepayment"]),
            "payment_interval": customer["frequency"].value,
            "payment_method": customer["payment_method"].value,
            "next_payment": customer["next_payment_date"].isoformat(),
            "tariff": customer["tariff"],
            "estimated_annual_consumption_kwh": float(customer["annual_consumption"]),
        },
    }


@prepayment_agent.tool
async def calculate_recommended_prepayment(
    ctx: RunContext[PrepaymentDeps],
    customer_number: str,
    new_annual_consumption: float | None = None,
) -> dict:
    """Calculate the recommended prepayment amount.
    
    Args:
        customer_number: The customer number
        new_annual_consumption: Optional new estimated annual consumption in kWh
    """
    customer = _customer_db.get(customer_number)
    
    if not customer:
        return {
            "success": False,
            "message": f"Customer {customer_number} not found.",
        }
    
    # Use provided consumption or existing estimate
    consumption = Decimal(str(new_annual_consumption)) if new_annual_consumption else customer["annual_consumption"]
    
    # Calculate annual costs
    energy_costs = consumption * customer["price_per_kwh"]
    base_costs = customer["base_price_monthly"] * 12
    total_annual = energy_costs + base_costs
    
    # Calculate monthly prepayment (rounded up to full euro)
    monthly = (total_annual / 12).quantize(Decimal("1"), rounding="ROUND_UP")
    
    # Compare to current
    current = customer["current_prepayment"]
    difference = monthly - current
    
    if difference > 0:
        comparison = f"Increase of {difference:.2f} EUR recommended"
        warning = "With a prepayment that's too low, you risk a back-payment at the annual settlement."
    elif difference < 0:
        comparison = f"Decrease of {abs(difference):.2f} EUR possible"
        warning = "You're paying more than necessary and will receive a refund at the annual settlement."
    else:
        comparison = "Your current prepayment is optimal"
        warning = None
    
    result = {
        "success": True,
        "message": "Prepayment calculation:",
        "calculation": {
            "estimated_annual_consumption_kwh": float(consumption),
            "energy_price_cents_kwh": float(customer["price_per_kwh"] * 100),
            "energy_costs_annual": float(energy_costs),
            "base_price_annual": float(base_costs),
            "total_costs_annual": float(total_annual),
            "recommended_monthly_prepayment": float(monthly),
            "current_prepayment": float(current),
            "comparison": comparison,
        },
    }
    
    if warning:
        result["calculation"]["note"] = warning
    
    return result


@prepayment_agent.tool
async def request_prepayment_adjustment(
    ctx: RunContext[PrepaymentDeps],
    customer_number: str,
    new_amount: float,
    reason: str | None = None,
) -> dict:
    """Request a change in prepayment amount.
    
    Args:
        customer_number: The customer number
        new_amount: The desired new prepayment amount in EUR
        reason: Optional reason for the adjustment
    """
    customer = _customer_db.get(customer_number)
    
    if not customer:
        return {
            "success": False,
            "message": f"Customer {customer_number} not found.",
        }
    
    new_amount_decimal = Decimal(str(new_amount))
    current = customer["current_prepayment"]
    
    # Validate minimum
    if new_amount_decimal < Decimal("25"):
        return {
            "success": False,
            "message": "The minimum prepayment is 25 EUR per month.",
        }
    
    # Check for extreme changes
    change_percent = abs((new_amount_decimal - current) / current * 100)
    
    if change_percent > 50:
        return {
            "success": False,
            "message": f"A change of more than 50% ({change_percent:.1f}%) requires review. "
                      "Please contact our customer service at 0800-123456.",
            "requires_review": True,
        }
    
    # Process adjustment
    confirmation = f"PA-{uuid.uuid4().hex[:8].upper()}"
    effective_date = date.today() + timedelta(days=14)  # 2 weeks notice
    
    # Update database (simulated)
    _customer_db[customer_number]["current_prepayment"] = new_amount_decimal
    
    return {
        "success": True,
        "message": "Prepayment adjustment requested successfully.",
        "details": {
            "old_prepayment": float(current),
            "new_prepayment": float(new_amount_decimal),
            "difference": float(new_amount_decimal - current),
            "effective_from": effective_date.isoformat(),
            "confirmation_number": confirmation,
            "reason": reason or "Customer request",
        },
    }


@prepayment_agent.tool
async def change_payment_method(
    ctx: RunContext[PrepaymentDeps],
    customer_number: str,
    new_method: str,
    iban: str | None = None,
) -> dict:
    """Change the payment method for prepayments.
    
    Args:
        customer_number: The customer number
        new_method: New payment method (lastschrift=direct debit, ueberweisung=bank transfer, dauerauftrag=standing order)
        iban: IBAN for direct debit (required only for lastschrift)
    """
    customer = _customer_db.get(customer_number)
    
    if not customer:
        return {
            "success": False,
            "message": f"Customer {customer_number} not found.",
        }
    
    try:
        method = PaymentMethod(new_method.lower())
    except ValueError:
        return {
            "success": False,
            "message": f"Invalid payment method: {new_method}. "
                      "Valid options: lastschrift (direct debit), ueberweisung (bank transfer), dauerauftrag (standing order)",
        }
    
    # Validate IBAN for direct debit
    if method == PaymentMethod.DIRECT_DEBIT:
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
    
    old_method = customer["payment_method"]
    _customer_db[customer_number]["payment_method"] = method
    
    confirmation = f"PM-{uuid.uuid4().hex[:8].upper()}"
    
    result = {
        "success": True,
        "message": "Payment method changed successfully.",
        "details": {
            "old_payment_method": old_method.value,
            "new_payment_method": method.value,
            "confirmation_number": confirmation,
        },
    }
    
    if method == PaymentMethod.DIRECT_DEBIT:
        result["details"]["note"] = (
            "The SEPA direct debit mandate will be sent to you by mail. "
            "The switch will take effect after we receive the signed mandate."
        )
    elif method == PaymentMethod.BANK_TRANSFER:
        result["details"]["payment_info"] = {
            "recipient": "Stadtwerke Musterstadt GmbH",
            "iban": "DE89 3704 0044 0532 0130 00",
            "reference": f"Prepayment {customer['contract_number']}",
            "amount": float(customer["current_prepayment"]),
        }
    
    return result


@prepayment_agent.tool
async def get_payment_history(
    ctx: RunContext[PrepaymentDeps],
    customer_number: str,
    months: int = 6,
) -> dict:
    """Retrieve payment history.
    
    Args:
        customer_number: The customer number
        months: Number of months for the history
    """
    customer = _customer_db.get(customer_number)
    
    if not customer:
        return {
            "success": False,
            "message": f"Customer {customer_number} not found.",
        }
    
    # Generate simulated payment history
    payments = []
    payment_date = date.today()
    amount = customer["current_prepayment"]
    
    for i in range(months):
        payment_date = payment_date.replace(day=1) - timedelta(days=1)
        payment_date = payment_date.replace(day=min(15, payment_date.day))
        
        payments.append({
            "date": payment_date.isoformat(),
            "amount": float(amount),
            "status": "processed",
            "payment_method": customer["payment_method"].value,
        })
    
    return {
        "success": True,
        "message": f"Payment history for the last {months} months:",
        "payments": payments,
        "total": float(amount * months),
    }
