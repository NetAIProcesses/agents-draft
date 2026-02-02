"""Pydantic models for the energy processes domain."""

from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============ Client Models ============

class Client(BaseModel):
    """Client (customer) in the German energy market."""
    id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None
    address: str
    city: str
    postal_code: str
    country: str = "Germany"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ClientCreate(BaseModel):
    """Model for creating a new client."""
    name: str
    email: str
    phone: Optional[str] = None
    address: str
    city: str
    postal_code: str
    country: str = "Germany"


# ============ Contract Models ============

class Contract(BaseModel):
    """Energy supply contract."""
    id: Optional[int] = None
    client_id: int
    contract_number: str
    start_date: date
    end_date: Optional[date] = None
    annual_consumption_kwh: float
    unit_price_eur_kwh: float
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContractCreate(BaseModel):
    """Model for creating a new contract."""
    client_id: int
    contract_number: str
    start_date: date
    end_date: Optional[date] = None
    annual_consumption_kwh: float
    unit_price_eur_kwh: float
    status: str = "active"


# ============ Energy Meter Models ============

class EnergyMeter(BaseModel):
    """Energy meter device."""
    id: Optional[int] = None
    contract_id: int
    meter_number: str
    meter_type: str  # e.g., "smart", "analog", "digital"
    installation_date: date
    location: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EnergyMeterCreate(BaseModel):
    """Model for creating a new energy meter."""
    contract_id: int
    meter_number: str
    meter_type: str
    installation_date: date
    location: Optional[str] = None
    status: str = "active"


# ============ Meter Reading Models ============

class MeterReading(BaseModel):
    """Meter reading record (Zählerstand)."""
    id: Optional[int] = None
    meter_id: int
    reading_date: date
    kwh_consumption: float
    unit: str = "kWh"
    reading_type: Literal["actual", "estimated"] = "actual"
    created_at: Optional[datetime] = None


class MeterReadingCreate(BaseModel):
    """Model for creating a new meter reading."""
    meter_id: int
    reading_date: date
    kwh_consumption: float
    unit: str = "kWh"
    reading_type: Literal["actual", "estimated"] = "actual"


# ============ Prepayment Models (Abschlagszahlung) ============

class Prepayment(BaseModel):
    """Prepayment record (Abschlagszahlung) for German energy market."""
    id: Optional[int] = None
    contract_id: int
    month: str  # e.g., "January", "February"
    year: int
    forecasted_consumption_kwh: float
    unit_price_eur_kwh: float
    payment_amount_eur: float
    payment_status: Literal["pending", "paid", "overdue"] = "pending"
    payment_date: Optional[date] = None
    due_date: date
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PrepaymentCreate(BaseModel):
    """Model for creating a new prepayment."""
    contract_id: int
    month: str
    year: int
    forecasted_consumption_kwh: float
    unit_price_eur_kwh: float
    payment_amount_eur: float
    payment_status: str = "pending"
    due_date: date


# ============ Agent State Models ============

class AgentContext(BaseModel):
    """Context shared between agents."""
    client_id: Optional[int] = None
    contract_id: Optional[int] = None
    meter_id: Optional[int] = None
    current_process: Optional[str] = None
    error_message: Optional[str] = None


class ProcessResult(BaseModel):
    """Result of a process execution."""
    success: bool
    message: str
    data: Optional[dict] = None
