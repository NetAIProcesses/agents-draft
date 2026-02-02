"""Tools for prepayment (Abschlagszahlung) process in the German energy market."""

from datetime import date
from typing import Optional
from langchain_core.tools import tool
from src.mcp_client import mcp_client


@tool
async def get_prepayments(
    contract_id: int,
    year: Optional[int] = None
) -> dict:
    """
    Retrieve prepayment records (Abschlagszahlungen) for a contract.
    
    Args:
        contract_id: The unique identifier of the contract.
        year: Optional year to filter prepayments.
    
    Returns:
        List of prepayment records for the contract.
    """
    if year:
        result = await mcp_client.execute_select(
            """
            SELECT * FROM prepayment 
            WHERE contract_id = $1 AND year = $2
            ORDER BY year DESC, 
                     CASE month 
                         WHEN 'January' THEN 1
                         WHEN 'February' THEN 2
                         WHEN 'March' THEN 3
                         WHEN 'April' THEN 4
                         WHEN 'May' THEN 5
                         WHEN 'June' THEN 6
                         WHEN 'July' THEN 7
                         WHEN 'August' THEN 8
                         WHEN 'September' THEN 9
                         WHEN 'October' THEN 10
                         WHEN 'November' THEN 11
                         WHEN 'December' THEN 12
                     END
            """,
            [contract_id, year]
        )
    else:
        result = await mcp_client.execute_select(
            """
            SELECT * FROM prepayment 
            WHERE contract_id = $1
            ORDER BY year DESC, 
                     CASE month 
                         WHEN 'January' THEN 1
                         WHEN 'February' THEN 2
                         WHEN 'March' THEN 3
                         WHEN 'April' THEN 4
                         WHEN 'May' THEN 5
                         WHEN 'June' THEN 6
                         WHEN 'July' THEN 7
                         WHEN 'August' THEN 8
                         WHEN 'September' THEN 9
                         WHEN 'October' THEN 10
                         WHEN 'November' THEN 11
                         WHEN 'December' THEN 12
                     END
            """,
            [contract_id]
        )
    return result


@tool
async def create_prepayment(
    contract_id: int,
    month: str,
    year: int,
    forecasted_consumption_kwh: float,
    unit_price_eur_kwh: float,
    payment_amount_eur: float,
    due_date: str
) -> dict:
    """
    Create a new prepayment (Abschlagszahlung) record.
    
    Args:
        contract_id: The unique identifier of the contract.
        month: The month name (e.g., "January", "February").
        year: The year (e.g., 2026).
        forecasted_consumption_kwh: Expected consumption for the month in kWh.
        unit_price_eur_kwh: Price per kWh in EUR.
        payment_amount_eur: Total prepayment amount in EUR.
        due_date: Payment due date in ISO format (YYYY-MM-DD).
    
    Returns:
        Confirmation of the created prepayment.
    """
    result = await mcp_client.execute_write(
        """
        INSERT INTO prepayment (
            contract_id, month, year, forecasted_consumption_kwh,
            unit_price_eur_kwh, payment_amount_eur, due_date, payment_status
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending')
        RETURNING *
        """,
        [contract_id, month, year, forecasted_consumption_kwh, 
         unit_price_eur_kwh, payment_amount_eur, due_date]
    )
    return result


@tool
async def update_prepayment_status(
    prepayment_id: int,
    status: str,
    payment_date: Optional[str] = None
) -> dict:
    """
    Update the status of a prepayment (e.g., mark as paid).
    
    Args:
        prepayment_id: The unique identifier of the prepayment.
        status: New status - "pending", "paid", or "overdue".
        payment_date: The actual payment date in ISO format (required if status is "paid").
    
    Returns:
        Updated prepayment record.
    """
    if status == "paid" and payment_date:
        result = await mcp_client.execute_write(
            """
            UPDATE prepayment 
            SET payment_status = $1, payment_date = $2, updated_at = CURRENT_TIMESTAMP
            WHERE id = $3
            RETURNING *
            """,
            [status, payment_date, prepayment_id]
        )
    else:
        result = await mcp_client.execute_write(
            """
            UPDATE prepayment 
            SET payment_status = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
            RETURNING *
            """,
            [status, prepayment_id]
        )
    return result


@tool
async def calculate_prepayment_amount(
    contract_id: int
) -> dict:
    """
    Calculate the recommended monthly prepayment amount based on contract and historical consumption.
    Uses the German market standard calculation method.
    
    Args:
        contract_id: The unique identifier of the contract.
    
    Returns:
        Calculated prepayment recommendation with breakdown.
    """
    result = await mcp_client.execute_select(
        """
        WITH contract_info AS (
            SELECT 
                c.id,
                c.annual_consumption_kwh,
                c.unit_price_eur_kwh
            FROM contracts c
            WHERE c.id = $1
        ),
        actual_consumption AS (
            SELECT 
                COALESCE(SUM(mr.kwh_consumption), 0) as total_actual_kwh,
                COUNT(DISTINCT mr.id) as reading_count,
                MIN(mr.reading_date) as first_reading,
                MAX(mr.reading_date) as last_reading
            FROM contract_info ci
            JOIN energy_meters em ON em.contract_id = ci.id
            JOIN meter_readings mr ON mr.meter_id = em.id
            WHERE mr.reading_date >= CURRENT_DATE - INTERVAL '12 months'
        )
        SELECT 
            ci.id as contract_id,
            ci.annual_consumption_kwh as contract_annual_kwh,
            ci.unit_price_eur_kwh,
            ac.total_actual_kwh as last_12_months_kwh,
            ac.reading_count,
            CASE 
                WHEN ac.reading_count > 6 THEN ac.total_actual_kwh
                ELSE ci.annual_consumption_kwh
            END as estimated_annual_kwh,
            ROUND(
                (CASE 
                    WHEN ac.reading_count > 6 THEN ac.total_actual_kwh
                    ELSE ci.annual_consumption_kwh
                END * ci.unit_price_eur_kwh / 12)::numeric, 2
            ) as recommended_monthly_prepayment_eur,
            ROUND(
                (CASE 
                    WHEN ac.reading_count > 6 THEN ac.total_actual_kwh
                    ELSE ci.annual_consumption_kwh
                END * ci.unit_price_eur_kwh / 12 * 1.1)::numeric, 2
            ) as recommended_with_buffer_eur
        FROM contract_info ci
        CROSS JOIN actual_consumption ac
        """,
        [contract_id]
    )
    return result


@tool
async def get_pending_prepayments(
    contract_id: Optional[int] = None,
    include_overdue: bool = True
) -> dict:
    """
    Get all pending prepayments, optionally filtered by contract.
    
    Args:
        contract_id: Optional contract ID to filter results.
        include_overdue: Whether to include overdue payments (default: True).
    
    Returns:
        List of pending (and optionally overdue) prepayments.
    """
    statuses = "('pending', 'overdue')" if include_overdue else "('pending')"
    
    if contract_id:
        result = await mcp_client.execute_select(
            f"""
            SELECT 
                p.*,
                c.contract_number,
                cl.name as client_name,
                cl.email as client_email,
                CASE 
                    WHEN p.due_date < CURRENT_DATE AND p.payment_status = 'pending' 
                    THEN 'overdue'
                    ELSE p.payment_status
                END as current_status,
                CASE 
                    WHEN p.due_date < CURRENT_DATE 
                    THEN CURRENT_DATE - p.due_date
                    ELSE 0
                END as days_overdue
            FROM prepayment p
            JOIN contracts c ON p.contract_id = c.id
            JOIN clients cl ON c.client_id = cl.id
            WHERE p.contract_id = $1 
              AND p.payment_status IN {statuses}
            ORDER BY p.due_date
            """,
            [contract_id]
        )
    else:
        result = await mcp_client.execute_select(
            f"""
            SELECT 
                p.*,
                c.contract_number,
                cl.name as client_name,
                cl.email as client_email,
                CASE 
                    WHEN p.due_date < CURRENT_DATE AND p.payment_status = 'pending' 
                    THEN 'overdue'
                    ELSE p.payment_status
                END as current_status,
                CASE 
                    WHEN p.due_date < CURRENT_DATE 
                    THEN CURRENT_DATE - p.due_date
                    ELSE 0
                END as days_overdue
            FROM prepayment p
            JOIN contracts c ON p.contract_id = c.id
            JOIN clients cl ON c.client_id = cl.id
            WHERE p.payment_status IN {statuses}
            ORDER BY p.due_date
            """,
            []
        )
    return result


@tool
async def get_prepayment_summary(contract_id: int, year: int) -> dict:
    """
    Get a summary of prepayments for a contract in a specific year.
    
    Args:
        contract_id: The unique identifier of the contract.
        year: The year to summarize.
    
    Returns:
        Summary including total paid, pending, and comparison with actual consumption.
    """
    result = await mcp_client.execute_select(
        """
        WITH prepayment_stats AS (
            SELECT 
                contract_id,
                COUNT(*) as total_prepayments,
                SUM(payment_amount_eur) as total_amount_eur,
                SUM(forecasted_consumption_kwh) as total_forecasted_kwh,
                SUM(CASE WHEN payment_status = 'paid' THEN payment_amount_eur ELSE 0 END) as paid_amount_eur,
                SUM(CASE WHEN payment_status = 'pending' THEN payment_amount_eur ELSE 0 END) as pending_amount_eur,
                SUM(CASE WHEN payment_status = 'overdue' THEN payment_amount_eur ELSE 0 END) as overdue_amount_eur,
                COUNT(CASE WHEN payment_status = 'paid' THEN 1 END) as paid_count,
                COUNT(CASE WHEN payment_status = 'pending' THEN 1 END) as pending_count,
                COUNT(CASE WHEN payment_status = 'overdue' THEN 1 END) as overdue_count
            FROM prepayment
            WHERE contract_id = $1 AND year = $2
            GROUP BY contract_id
        ),
        actual_consumption AS (
            SELECT 
                COALESCE(SUM(mr.kwh_consumption), 0) as actual_kwh
            FROM contracts c
            JOIN energy_meters em ON em.contract_id = c.id
            JOIN meter_readings mr ON mr.meter_id = em.id
            WHERE c.id = $1 
              AND EXTRACT(YEAR FROM mr.reading_date) = $2
        )
        SELECT 
            ps.*,
            ac.actual_kwh,
            ROUND((ps.total_forecasted_kwh - ac.actual_kwh)::numeric, 2) as consumption_difference_kwh,
            c.unit_price_eur_kwh,
            ROUND((ac.actual_kwh * c.unit_price_eur_kwh)::numeric, 2) as actual_cost_eur,
            ROUND((ps.paid_amount_eur - ac.actual_kwh * c.unit_price_eur_kwh)::numeric, 2) as balance_eur
        FROM prepayment_stats ps
        CROSS JOIN actual_consumption ac
        JOIN contracts c ON ps.contract_id = c.id
        """,
        [contract_id, year]
    )
    return result
