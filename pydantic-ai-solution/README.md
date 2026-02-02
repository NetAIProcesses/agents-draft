# German Energy Market Multi-Agent System

🇩🇪 A multi-agent system for handling German energy market processes using Pydantic AI.

## Overview

This system uses three specialized agents to handle common customer service tasks:

| Agent | German Name | Description |
|-------|-------------|-------------|
| 📊 **Meter Reading** | Zählerstandserfassung | Submit meter readings, view history, get reading tips |
| 💰 **Prepayment** | Abschlagszahlung | Query/adjust monthly payments, change payment methods |
| ❓ **FAQ** | Häufig gestellte Fragen | Answer common questions about energy services |

An **Orchestrator** agent automatically routes customer requests to the appropriate specialized agent.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Customer Request                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                         │
│  • Analyzes request keywords                                 │
│  • Extracts identifiers (customer#, meter#)                  │
│  • Routes to appropriate agent                               │
└────────────┬──────────────────┬──────────────────┬──────────┘
             │                  │                  │
             ▼                  ▼                  ▼
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│ Meter Reading  │   │   Prepayment   │   │      FAQ       │
│     Agent      │   │     Agent      │   │     Agent      │
├────────────────┤   ├────────────────┤   ├────────────────┤
│ • Submit       │   │ • Query amount │   │ • Search FAQ   │
│ • History      │   │ • Adjust       │   │ • Categories   │
│ • Validate     │   │ • Payment      │   │ • Terms        │
│ • Tips         │   │   method       │   │ • Contact      │
└────────────────┘   └────────────────┘   └────────────────┘
```

## Requirements

- Python 3.14.2
- uv (package manager)
- OpenAI API key (or GitHub token for GitHub Models)

## Installation

```bash
# Navigate to the project
cd pydantic-ai-solution

# Install dependencies with uv
uv sync

# Copy environment file and add your API key
cp .env.example .env
# Edit .env with your API key
```

## Usage

### Demo Mode (Default)
Shows example requests for all three agents:

```bash
uv run main.py
```

### Interactive Mode
Chat with the system interactively:

```bash
uv run main.py --interactive
# or
uv run main.py -i
```

### Routing Demo
See how requests are classified:

```bash
uv run main.py --routing
# or
uv run main.py -r
```

## Example Interactions

### Meter Reading
```
Sie: Ich möchte meinen Zählerstand melden. Zähler DE-001234567, Stand 15500 kWh

🤖 [meter_reading]
   Zählerstand erfolgreich übermittelt. Bestätigungsnummer: ZS-A1B2C3D4
```

### Prepayment
```
Sie: Was ist mein aktueller Abschlag? Kundennummer K-12345

🤖 [prepayment]
   Ihr aktueller monatlicher Abschlag beträgt 95,00 EUR.
   Nächste Abbuchung: 01.03.2026
```

### FAQ
```
Sie: Was bedeutet Arbeitspreis auf meiner Rechnung?

🤖 [faq]
   Der Arbeitspreis ist der Preis pro verbrauchter Kilowattstunde (kWh).
   Er macht den größten Teil Ihrer Stromkosten aus.
```

## Project Structure

```
pydantic-ai-solution/
├── main.py                 # Main entry point
├── pyproject.toml          # Project dependencies
├── .env.example            # Environment template
├── README.md               # This file
└── src/
    ├── __init__.py
    ├── config.py           # Configuration settings
    ├── models.py           # Pydantic data models
    └── agents/
        ├── __init__.py
        ├── meter_reading_agent.py   # Zählerstandserfassung
        ├── prepayment_agent.py      # Abschlagszahlung
        ├── faq_agent.py             # FAQ handling
        └── orchestrator.py          # Request routing
```

## Configuration

Environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_NAME` | AI model to use | `openai:gpt-4o-mini` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GITHUB_TOKEN` | GitHub token (alternative) | - |
| `DEBUG` | Enable debug mode | `false` |
| `LANGUAGE` | Response language | `de` |

## Data Models

### Meter Reading (Zählerstand)
- `MeterReading` - Meter reading submission
- `MeterReadingResponse` - Processing response
- `MeterType` - strom, gas, wasser, waerme

### Prepayment (Abschlag)
- `PrepaymentInfo` - Current prepayment setup
- `PrepaymentAdjustmentRequest` - Change request
- `PrepaymentFrequency` - monatlich, vierteljährlich, etc.
- `PaymentMethod` - lastschrift, ueberweisung, dauerauftrag

### FAQ
- `FAQCategory` - rechnung, vertrag, umzug, tarif, etc.
- `FAQAnswer` - Structured answer with related info

## Extending the System

### Adding a New Agent

1. Create `src/agents/new_agent.py`
2. Define agent with `Agent()` and tools with `@agent.tool`
3. Add to `src/agents/__init__.py`
4. Update orchestrator routing logic
5. Add `AgentType` enum value

### Adding New FAQ Categories

Edit `_faq_knowledge_base` in `src/agents/faq_agent.py`:

```python
FAQCategory.NEW_CATEGORY: [
    {
        "question": "Your question?",
        "answer": "Your answer...",
        "keywords": ["keyword1", "keyword2"],
    },
],
```

## License

MIT License
