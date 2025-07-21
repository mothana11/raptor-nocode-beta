from __future__ import annotations
from typing import List, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
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
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=openai_api_key)

    tools = [
        ALL_TOOLS["search_flights"],
        ALL_TOOLS["book_flight"],
        ALL_TOOLS["search_hotels"],
        ALL_TOOLS["book_hotel"],
        ALL_TOOLS["cancel_or_modify_booking"],
        ALL_TOOLS["check_booking_status"]
    ]

    # Agent that can decide when to call tools (ReAct pattern)
    agent = create_react_agent(
        llm,
        tools,
        prompt="""You are TravelGPT, an expert travel assistant and concierge. 

I have access to detailed user context including:
- Personal profile (name, nationality, loyalty status)
- Travel preferences (seating, meals, accommodation style)
- Travel history (past trips, ratings, destinations)
- Active bookings (current and upcoming travel)

I use this context to provide personalized recommendations and assistance. I should:
1. Reference user preferences when making suggestions
2. Consider past travel patterns and ratings
3. Acknowledge loyalty status and frequent flyer benefits
4. Be aware of existing bookings when helping with new travel
5. Provide contextual advice based on travel history

I have comprehensive travel tools available:
- Flight search and hotel booking
- Car rental search and activity booking (tours, restaurants, attractions, shows)
- Travel insurance quotes and visa requirement checks
- Currency conversion and weather forecasts
- Travel alerts and booking management (check status, modify, cancel)

CRITICAL CONVERSATION RULES:
1. ALWAYS listen to user choices - if they say "option 3", use option 3 exactly as shown
2. NEVER make up information - use the tools to get real data
3. REMEMBER context throughout the conversation - if user mentions Detroit, don't switch to New York
4. When user specifies traveling with someone (brother, family), REMEMBER this for all subsequent bookings
5. Use search_flights tool FIRST, then book_flight tool with the exact option number they choose
6. Be consistent - don't keep changing flight options or prices
7. If user corrects information (like changing departure city), start fresh with the correct info
8. Pay attention to details - remember companion travelers, preferences, etc.

TOOL USAGE:
- Use search_flights to show options FIRST
- Use book_flight with the option number when user chooses
- Don't automatically book hotels unless requested
- Ask for clarification when needed, but respect explicit user choices

I respond in natural, conversational language like a professional travel agent. I do NOT use any markdown formatting including:
- No ### headers or ## subheadings
- No **bold text** or *italic text* 

I write in clear, flowing sentences and paragraphs that sound completely natural and human.""",
    )

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(tools))

    # Entry point - use "agent" as the starting node
    graph.set_entry_point("agent")

    # Conditional edge from agent: if tools required -> tools else end
    graph.add_conditional_edges("agent", tools_condition, {
        "tools": "tools",
        "__end__": "__end__",
    })

    # After tools execution, go back to agent for further reasoning
    graph.add_edge("tools", "agent")

    return graph.compile() 