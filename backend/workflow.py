from __future__ import annotations
from typing import List, TypedDict

from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition

try:
    # For Railway deployment (running from project root)
    from backend.mcp_tools import ALL_TOOLS
except ImportError:
    # For local development (running from backend directory)
    from mcp_tools import ALL_TOOLS

class AgentState(TypedDict):
    messages: List[BaseMessage]


def build_travel_workflow(openai_api_key: str):
    """
    Build a travel workflow that minimizes API calls while still being helpful
    """
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        temperature=0.7, 
        api_key=openai_api_key,
        max_tokens=300,  # Limit response length to reduce costs
        timeout=10  # Add timeout to prevent hanging
    )

    # Only use essential tools to reduce API calls
    essential_tools = [
        tool for tool in ALL_TOOLS 
        if tool.name in ['search_flights', 'search_hotels', 'book_flight', 'book_hotel']
    ]

    # Create a more controlled agent with limited tool usage
    agent = create_react_agent(
        llm,
        essential_tools,  # Use only essential tools
        prompt="""You are TravelGPT, an expert travel assistant. 

CRITICAL: Minimize tool usage to avoid API rate limits.

RULES:
1. ONLY use tools when the user explicitly requests specific searches or bookings
2. For general questions, respond directly without calling tools
3. If user says "hi" or general greetings, respond helpfully without tools
4. Use search_flights ONLY when user provides origin, destination, and dates
5. Use search_hotels ONLY when user provides location and dates
6. Use booking tools ONLY when user confirms a specific option
7. For everything else, provide helpful guidance and ask for specifics

TOOL USAGE GUIDELINES:
- search_flights: Only when user gives origin + destination + date
- search_hotels: Only when user gives location + check-in/out dates  
- book_flight: Only when user chooses a specific flight option
- book_hotel: Only when user chooses a specific hotel option

CONVERSATION RULES:
1. Listen to user choices - if they say "option 3", use exactly option 3
2. Remember context throughout conversation
3. Remember travel companions mentioned
4. Be specific and accurate
5. Ask clarifying questions instead of guessing
6. No markdown formatting - write in natural paragraphs

For general travel questions, weather, tips, or planning advice, respond directly with your knowledge instead of using tools.

Be helpful, efficient, and conservative with tool usage.""",
        interrupt_before=["tools"],  # Add control point before tool execution
        debug=False  # Disable debug to reduce noise
    )

    return agent 