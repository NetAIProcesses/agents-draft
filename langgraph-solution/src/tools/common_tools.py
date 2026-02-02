"""Common tools shared across agents."""

from langchain_core.tools import tool
from src.mcp_client import mcp_client


@tool
async def get_client_by_id(client_id: int) -> dict:
    """
    Retrieve a client by their ID.
    
    Args:
        client_id: The unique identifier of the client.
    
    Returns:
        Client information including name, email, address, etc.
    """
    result = await mcp_client.execute_select(
        "SELECT * FROM clients WHERE id = $1",
        [client_id]
    )
    return result


@tool
async def get_contract_by_id(contract_id: int) -> dict:
    """
    Retrieve a contract by its ID.
    
    Args:
        contract_id: The unique identifier of the contract.
    
    Returns:
        Contract information including client_id, contract_number, pricing, etc.
    """
    result = await mcp_client.execute_select(
        "SELECT * FROM contracts WHERE id = $1",
        [contract_id]
    )
    return result


@tool
async def get_contracts_by_client(client_id: int) -> dict:
    """
    Retrieve all contracts for a specific client.
    
    Args:
        client_id: The unique identifier of the client.
    
    Returns:
        List of contracts for the client.
    """
    result = await mcp_client.execute_select(
        "SELECT * FROM contracts WHERE client_id = $1 ORDER BY start_date DESC",
        [client_id]
    )
    return result


@tool
async def search_clients(search_term: str) -> dict:
    """
    Search for clients by name or email.
    
    Args:
        search_term: The search term to match against client name or email.
    
    Returns:
        List of matching clients.
    """
    result = await mcp_client.execute_select(
        """
        SELECT * FROM clients 
        WHERE name ILIKE $1 OR email ILIKE $1 
        ORDER BY name
        LIMIT 20
        """,
        [f"%{search_term}%"]
    )
    return result


@tool
async def get_client_with_contracts(client_id: int) -> dict:
    """
    Retrieve a client with all their active contracts.
    
    Args:
        client_id: The unique identifier of the client.
    
    Returns:
        Client information with associated contracts.
    """
    result = await mcp_client.execute_select(
        """
        SELECT 
            c.*,
            json_agg(
                json_build_object(
                    'id', co.id,
                    'contract_number', co.contract_number,
                    'start_date', co.start_date,
                    'end_date', co.end_date,
                    'status', co.status,
                    'annual_consumption_kwh', co.annual_consumption_kwh,
                    'unit_price_eur_kwh', co.unit_price_eur_kwh
                )
            ) FILTER (WHERE co.id IS NOT NULL) as contracts
        FROM clients c
        LEFT JOIN contracts co ON c.id = co.client_id
        WHERE c.id = $1
        GROUP BY c.id
        """,
        [client_id]
    )
    return result
