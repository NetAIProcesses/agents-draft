"""Main entry point for the German Energy Market Multi-Agent System."""

import asyncio
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage

from src.graph import build_workflow
from src.llm import get_default_llm


async def chat_loop():
    """Interactive chat loop with the multi-agent system."""
    print("=" * 60)
    print("  German Energy Market Multi-Agent System")
    print("  (Meter Reading & Prepayment)")
    print("=" * 60)
    print("\nWelcome! I am your assistant for energy questions.")
    print("You can ask me about the following topics:")
    print("  • Meter Reading (meter readings, consumption)")
    print("  • Prepayment (monthly payments, status)")
    print("  • FAQ (general questions about energy)")
    print("\nType 'exit' or 'quit' to exit.\n")
    
    # Initialize LLM and workflow
    llm = get_default_llm()
    workflow = build_workflow(llm)
    
    # Initialize state
    state = {
        "messages": [],
        "next_agent": "",
        "current_agent": "",
        "context": {},
    }
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("\nGoodbye! Have a nice day.")
                break
            
            # Add user message to state
            state["messages"] = list(state["messages"]) + [HumanMessage(content=user_input)]
            
            # Run the workflow
            print("\n[Processing request...]")
            result = await workflow.ainvoke(state)
            
            # Update state
            state = result
            
            # Extract and print the last AI response
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            if ai_messages:
                last_response = ai_messages[-1]
                print(f"\nAssistant: {last_response.content}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[Error: {e}]")
            print("Please try again.")


async def process_single_query(query: str) -> str:
    """
    Process a single query and return the response.
    
    Args:
        query: The user query to process.
    
    Returns:
        The agent's response.
    """
    llm = get_default_llm()
    workflow = build_workflow(llm)
    
    state = {
        "messages": [HumanMessage(content=query)],
        "next_agent": "",
        "current_agent": "",
        "context": {},
    }
    
    result = await workflow.ainvoke(state)
    
    ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
    if ai_messages:
        return ai_messages[-1].content
    
    return "No response received."


def main():
    """Main entry point."""
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
