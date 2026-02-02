# German Energy Market Multi-Agent System

A LangGraph-based multi-agent system for handling energy market processes in Germany, specifically:
- **Meter Reading (Zählerablesung)** - Recording and validating meter readings
- **Prepayment (Abschlagszahlung)** - Managing monthly advance payments
- **FAQ (Häufige Fragen)** - Answering common questions about energy services

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Supervisor Agent                          │
│         (Routes requests to specialized agents)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
┌─────────────┐ ┌───────────┐ ┌─────────────┐
│ Meter       │ │Prepayment │ │ FAQ         │
│ Reading     │ │ Agent     │ │ Agent       │
│ Agent       │ │           │ │             │
└─────────────┘ └───────────┘ └─────────────┘
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │   MCP Database Client   │
         │   (Energy Processes DB) │
         └─────────────────────────┘
```

## Features

### Meter Reading Agent
- Record new meter readings (actual or estimated)
- Validate readings against historical data
- View consumption history
- Detect anomalies in consumption patterns

### Prepayment Agent
- Calculate recommended monthly prepayment amounts
- Track payment status (pending, paid, overdue)
- Generate annual settlement summaries
- Compare forecasted vs. actual consumption

### FAQ Agent
- Answer frequently asked questions about energy services
- Topics include: electricity pricing, provider switching, smart meters, billing, contracts
- Provide helpful explanations in German

## Installation

```bash
# Navigate to project folder
cd langgraph-solution

# Using uv package manager
uv sync
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```env
# MCP Database Configuration
MCP_BASE_URL=http://192.168.68.126/agents-db-mcp

# LLM Provider: "openai" or "anthropic"
LLM_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# Anthropic Configuration (optional)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

## Usage

### Interactive Chat Mode
```bash
uv run python main.py
```

### Programmatic Usage
```python
import asyncio
from src.main import process_single_query

async def main():
    response = await process_single_query("Was ist mein aktueller Zählerstand?")
    print(response)

asyncio.run(main())
```

## Project Structure

```
langgraph-solution/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration settings
│   ├── graph.py            # LangGraph workflow definition
│   ├── llm.py              # LLM initialization
│   ├── main.py             # Main application entry
│   ├── mcp_client.py       # MCP database client
│   ├── models.py           # Pydantic data models
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── meter_reading_agent.py
│   │   ├── prepayment_agent.py
│   │   └── supervisor_agent.py
│   └── tools/
│       ├── __init__.py
│       ├── common_tools.py
│       ├── meter_reading_tools.py
│       └── prepayment_tools.py
├── main.py                 # Entry point
├── pyproject.toml
├── .env.example
└── README.md
```

## Database Schema

The system connects to a PostgreSQL database via MCP with the following tables:
- `clients` - Customer information
- `contracts` - Energy supply contracts
- `energy_meters` - Meter devices
- `meter_readings` - Consumption readings
- `prepayment` - Monthly advance payments
- `audit_log` - Change tracking

## Example Queries

```
# Meter Reading (Zählerablesung)
"Zeig mir die letzten Zählerstände für Vertrag 1"
"Ich möchte einen Zählerstand von 12500 kWh für Zähler 3 erfassen"
"Validiere bitte den Verbrauch von 800 kWh für diesen Monat"

# Prepayment (Abschlagszahlung)
"Was ist mein empfohlener monatlicher Abschlag?"
"Welche Zahlungen sind noch offen?"
"Zeig mir die Jahresübersicht für 2025"
```

## License

Private - Internal Use Only
