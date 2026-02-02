"""German Energy Market Multi-Agent System.

This is the main entry point for the multi-agent system that handles:
- Meter Readings
- Prepayment Management
- FAQ (Frequently Asked Questions)

Run with:
    uv run main.py

Or in interactive mode:
    uv run main.py --interactive
"""

import asyncio
import sys

from src.agents import handle_customer_request, orchestrator_agent
from src.agents.orchestrator import OrchestratorDeps
from src.models import CustomerContext


async def demo_requests():
    """Run demo requests to showcase the multi-agent system."""
    
    print("=" * 70)
    print("🇩🇪 German Energy Market Multi-Agent System")
    print("=" * 70)
    print()
    
    # Demo requests for each agent type
    demo_messages = [
        # Meter Reading Examples
        ("I want to submit my meter reading. Meter number DE-001234567, reading 15500 kWh",
         "📊 Submit Meter Reading"),
        
        ("How do I read my electricity meter correctly?",
         "📊 Reading Tips"),
        
        # Prepayment Examples  
        ("What is my current prepayment? Customer number K-12345",
         "💰 Query Prepayment"),
        
        ("I want to change my prepayment to 110 euros. Customer number K-12345",
         "💰 Change Prepayment"),
        
        # FAQ Examples
        ("What does energy price mean on my bill?",
         "❓ Explain Term"),
        
        ("How can I cancel my contract?",
         "❓ Contract Question"),
        
        ("What do I need to consider when moving?",
         "❓ Moving Question"),
    ]
    
    customer_ctx = CustomerContext(
        customer_number="K-12345",
        language="en",
    )
    
    for message, description in demo_messages:
        print(f"\n{'─' * 70}")
        print(f"📨 {description}")
        print(f"{'─' * 70}")
        print(f"Customer: {message}")
        print()
        
        try:
            response = await handle_customer_request(message, customer_ctx)
            
            print(f"🤖 Agent: {response.agent_type.value}")
            print(f"✅ Success: {'Yes' if response.success else 'No'}")
            print(f"\n💬 Response:\n{response.message}")
            
            if response.data:
                print(f"\n📋 Details:")
                for key, value in response.data.items():
                    if key not in ['answer', 'message']:
                        print(f"   • {key}: {value}")
                        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("=" * 70)
    print("Demo completed!")
    print("=" * 70)


async def interactive_mode():
    """Run in interactive mode where user can type messages."""
    
    print("=" * 70)
    print("🇩🇪 German Energy Market Multi-Agent System")
    print("   Interactive Mode")
    print("=" * 70)
    print()
    print("Enter your question (or 'exit' to quit):")
    print()
    
    customer_ctx = CustomerContext(language="en")
    
    while True:
        try:
            message = input("You: ").strip()
            
            if not message:
                continue
                
            if message.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye! 👋")
                break
            
            print()
            response = await handle_customer_request(message, customer_ctx)
            
            print(f"🤖 [{response.agent_type.value}]")
            print(f"   {response.message}")
            
            if response.follow_up_required:
                print("\n   ℹ️  For further assistance, please contact our customer service.")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


async def routing_demo():
    """Demo to show how routing works."""
    
    print("=" * 70)
    print("🔀 Routing Demo - Shows how requests are classified")
    print("=" * 70)
    print()
    
    test_messages = [
        "My meter reading is 12345",
        "Can I lower my prepayment?",
        "How much does electricity cost?",
        "I'm moving next month",
        "Meter DE-001234567 reading 15000",
        "Change IBAN for direct debit",
        "What is green electricity?",
    ]
    
    customer_ctx = CustomerContext()
    deps = OrchestratorDeps(customer_context=customer_ctx)
    
    for msg in test_messages:
        result = await orchestrator_agent.run(msg, deps=deps)
        routing = result.output
        
        print(f"📨 \"{msg}\"")
        print(f"   → Agent: {routing.agent_type.value}")
        print(f"   → Confidence: {routing.confidence:.0%}")
        print(f"   → Reasoning: {routing.reasoning}")
        print()


def main():
    """Main entry point."""
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--interactive', '-i']:
            asyncio.run(interactive_mode())
        elif sys.argv[1] in ['--routing', '-r']:
            asyncio.run(routing_demo())
        elif sys.argv[1] in ['--help', '-h']:
            print(__doc__)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Available options: --interactive, --routing, --help")
    else:
        asyncio.run(demo_requests())


if __name__ == "__main__":
    main()
