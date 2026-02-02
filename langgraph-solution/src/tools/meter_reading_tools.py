"""Tools for meter reading (Zählerablesung) process."""

from datetime import date
from typing import Optional, Literal
from langchain_core.tools import tool
from src.mcp_client import mcp_client


@tool
async def get_meter_readings(
    meter_id: int,
    limit: int = 12
) -> dict:
    """
    Retrieve meter readings for a specific meter.
    
    Args:
        meter_id: The unique identifier of the energy meter.
        limit: Maximum number of readings to return (default: 12 for yearly view).
    
    Returns:
        List of meter readings ordered by date (most recent first).
    """
    result = await mcp_client.execute_select(
        """
        SELECT * FROM meter_readings 
        WHERE meter_id = $1 
        ORDER BY reading_date DESC 
        LIMIT $2
        """,
        [meter_id, limit]
    )
    return result


@tool
async def create_meter_reading(
    meter_id: int,
    reading_date: str,
    kwh_consumption: float,
    reading_type: str = "actual"
) -> dict:
    """
    Create a new meter reading (Zählerstand erfassen).
    
    Args:
        meter_id: The unique identifier of the energy meter.
        reading_date: The date of the reading in ISO format (YYYY-MM-DD).
        kwh_consumption: The consumption value in kWh.
        reading_type: Type of reading - "actual" or "estimated".
    
    Returns:
        Confirmation of the created meter reading.
    """
    result = await mcp_client.execute_write(
        """
        INSERT INTO meter_readings (meter_id, reading_date, kwh_consumption, unit, reading_type)
        VALUES ($1, $2, $3, 'kWh', $4)
        RETURNING *
        """,
        [meter_id, reading_date, kwh_consumption, reading_type]
    )
    return result


@tool
async def get_meters_by_contract(contract_id: int) -> dict:
    """
    Retrieve all energy meters associated with a contract.
    
    Args:
        contract_id: The unique identifier of the contract.
    
    Returns:
        List of energy meters for the contract.
    """
    result = await mcp_client.execute_select(
        """
        SELECT * FROM energy_meters 
        WHERE contract_id = $1 AND status = 'active'
        ORDER BY meter_number
        """,
        [contract_id]
    )
    return result


@tool
async def get_consumption_history(
    meter_id: int,
    start_date: str,
    end_date: str
) -> dict:
    """
    Get consumption history for a meter within a date range.
    
    Args:
        meter_id: The unique identifier of the energy meter.
        start_date: Start date in ISO format (YYYY-MM-DD).
        end_date: End date in ISO format (YYYY-MM-DD).
    
    Returns:
        Consumption data with totals and average consumption.
    """
    result = await mcp_client.execute_select(
        """
        SELECT 
            meter_id,
            COUNT(*) as reading_count,
            SUM(kwh_consumption) as total_consumption_kwh,
            AVG(kwh_consumption) as avg_consumption_kwh,
            MIN(reading_date) as first_reading,
            MAX(reading_date) as last_reading,
            json_agg(
                json_build_object(
                    'date', reading_date,
                    'consumption', kwh_consumption,
                    'type', reading_type
                ) ORDER BY reading_date
            ) as readings
        FROM meter_readings
        WHERE meter_id = $1 
          AND reading_date BETWEEN $2 AND $3
        GROUP BY meter_id
        """,
        [meter_id, start_date, end_date]
    )
    return result


@tool
async def validate_meter_reading(
    meter_id: int,
    new_reading: float,
    reading_date: str
) -> dict:
    """
    Validate a new meter reading against historical data.
    Checks for plausibility based on previous readings.
    
    Args:
        meter_id: The unique identifier of the energy meter.
        new_reading: The new consumption value in kWh to validate.
        reading_date: The date of the new reading in ISO format.
    
    Returns:
        Validation result with plausibility check.
    """
    result = await mcp_client.execute_select(
        """
        WITH last_readings AS (
            SELECT 
                kwh_consumption,
                reading_date,
                reading_type
            FROM meter_readings
            WHERE meter_id = $1 AND reading_date < $2
            ORDER BY reading_date DESC
            LIMIT 3
        ),
        stats AS (
            SELECT 
                AVG(kwh_consumption) as avg_consumption,
                STDDEV(kwh_consumption) as stddev_consumption,
                MAX(kwh_consumption) as max_consumption,
                MIN(kwh_consumption) as min_consumption
            FROM meter_readings
            WHERE meter_id = $1
        )
        SELECT 
            (SELECT json_agg(last_readings.*) FROM last_readings) as previous_readings,
            s.avg_consumption,
            s.stddev_consumption,
            s.max_consumption,
            s.min_consumption,
            CASE 
                WHEN $3::float > COALESCE(s.avg_consumption * 3, 10000) THEN 'suspicious_high'
                WHEN $3::float < COALESCE(s.avg_consumption * 0.1, 0) THEN 'suspicious_low'
                ELSE 'valid'
            END as validation_status
        FROM stats s
        """,
        [meter_id, reading_date, new_reading]
    )
    return result


@tool
async def get_meter_details(meter_id: int) -> dict:
    """
    Get detailed information about a specific meter including contract and client info.
    
    Args:
        meter_id: The unique identifier of the energy meter.
    
    Returns:
        Complete meter information with associated contract and client details.
    """
    result = await mcp_client.execute_select(
        """
        SELECT 
            em.*,
            c.contract_number,
            c.status as contract_status,
            c.unit_price_eur_kwh,
            cl.name as client_name,
            cl.address as client_address,
            cl.city as client_city,
            cl.postal_code as client_postal_code
        FROM energy_meters em
        JOIN contracts c ON em.contract_id = c.id
        JOIN clients cl ON c.client_id = cl.id
        WHERE em.id = $1
        """,
        [meter_id]
    )
    return result
