"""Data models for the German Energy Market agents."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# Meter Reading Models (Zählerstand)
# =============================================================================

class MeterType(str, Enum):
    """Types of meters in German energy market."""
    ELECTRICITY = "strom"  # Stromzähler
    GAS = "gas"  # Gaszähler
    WATER = "wasser"  # Wasserzähler
    HEAT = "waerme"  # Wärmezähler


class MeterReading(BaseModel):
    """A single meter reading submission."""
    
    meter_number: str = Field(..., description="Zählernummer")
    meter_type: MeterType = Field(..., description="Zählerart")
    reading_value: Decimal = Field(..., ge=0, description="Zählerstand in kWh/m³")
    reading_date: date = Field(default_factory=date.today, description="Ablesedatum")
    is_move_out: bool = Field(default=False, description="Auszugsablesung")
    is_move_in: bool = Field(default=False, description="Einzugsablesung")
    photo_attached: bool = Field(default=False, description="Foto beigefügt")


class MeterReadingResponse(BaseModel):
    """Response after processing a meter reading."""
    
    success: bool
    message: str
    confirmation_number: str | None = None
    estimated_consumption: Decimal | None = Field(
        None, description="Geschätzter Verbrauch seit letzter Ablesung"
    )
    next_reading_due: date | None = Field(
        None, description="Nächstes Ablesedatum"
    )


class MeterReadingQuery(BaseModel):
    """Query for meter reading history."""
    
    meter_number: str
    start_date: date | None = None
    end_date: date | None = None


# =============================================================================
# Prepayment Models (Abschlagszahlung)
# =============================================================================

class PrepaymentFrequency(str, Enum):
    """Payment frequency options."""
    MONTHLY = "monatlich"
    QUARTERLY = "vierteljährlich"
    SEMI_ANNUAL = "halbjährlich"
    ANNUAL = "jährlich"


class PaymentMethod(str, Enum):
    """Available payment methods."""
    DIRECT_DEBIT = "lastschrift"  # SEPA-Lastschrift
    BANK_TRANSFER = "ueberweisung"  # Überweisung
    STANDING_ORDER = "dauerauftrag"  # Dauerauftrag


class PrepaymentInfo(BaseModel):
    """Information about current prepayment setup."""
    
    customer_number: str = Field(..., description="Kundennummer")
    contract_number: str = Field(..., description="Vertragsnummer")
    current_amount: Decimal = Field(..., description="Aktueller Abschlagsbetrag in EUR")
    frequency: PrepaymentFrequency = Field(..., description="Zahlungsintervall")
    payment_method: PaymentMethod = Field(..., description="Zahlungsart")
    next_payment_date: date = Field(..., description="Nächster Zahlungstermin")
    annual_consumption_estimate: Decimal = Field(
        ..., description="Geschätzter Jahresverbrauch"
    )


class PrepaymentAdjustmentRequest(BaseModel):
    """Request to adjust prepayment amount."""
    
    customer_number: str
    new_amount: Decimal | None = Field(None, description="Gewünschter neuer Abschlag")
    reason: str | None = Field(None, description="Grund für Anpassung")
    apply_from: date | None = Field(None, description="Gültig ab")


class PrepaymentAdjustmentResponse(BaseModel):
    """Response after prepayment adjustment."""
    
    success: bool
    message: str
    old_amount: Decimal | None = None
    new_amount: Decimal | None = None
    effective_date: date | None = None
    confirmation_number: str | None = None


class PrepaymentCalculation(BaseModel):
    """Calculated prepayment recommendation."""
    
    recommended_amount: Decimal
    calculation_basis: str
    current_price_per_kwh: Decimal
    estimated_annual_cost: Decimal
    comparison_to_current: str


# =============================================================================
# FAQ Models (Häufig gestellte Fragen)
# =============================================================================

class FAQCategory(str, Enum):
    """FAQ categories for German energy market."""
    BILLING = "rechnung"  # Rechnungsfragen
    CONTRACT = "vertrag"  # Vertragsfragen
    MOVING = "umzug"  # Umzugsfragen
    TARIFF = "tarif"  # Tarifwechsel
    PAYMENT = "zahlung"  # Zahlungsfragen
    METER = "zaehler"  # Zählerfragen
    OUTAGE = "stoerung"  # Störungsmeldungen
    GREEN_ENERGY = "oekostrom"  # Ökostrom
    GENERAL = "allgemein"  # Allgemeine Fragen


class FAQQuestion(BaseModel):
    """A frequently asked question."""
    
    question: str
    category: FAQCategory
    keywords: list[str] = Field(default_factory=list)


class FAQAnswer(BaseModel):
    """Answer to a FAQ."""
    
    answer: str
    category: FAQCategory
    related_links: list[str] = Field(default_factory=list)
    contact_required: bool = Field(
        default=False, 
        description="Whether customer should contact support"
    )
    relevant_forms: list[str] = Field(default_factory=list)


# =============================================================================
# Orchestrator Models
# =============================================================================

class AgentType(str, Enum):
    """Types of agents in the system."""
    METER_READING = "meter_reading"
    PREPAYMENT = "prepayment"
    FAQ = "faq"


class CustomerContext(BaseModel):
    """Customer context for agent interactions."""
    
    customer_number: str | None = None
    contract_number: str | None = None
    language: Literal["de", "en"] = "de"
    session_id: str | None = None


class AgentResponse(BaseModel):
    """Unified response from any agent."""
    
    agent_type: AgentType
    success: bool
    message: str
    data: dict | None = None
    follow_up_required: bool = False
    suggested_next_action: str | None = None
