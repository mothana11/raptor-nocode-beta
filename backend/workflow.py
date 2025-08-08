# workflow.py - FIXED INTELLIGENT WORKFLOW WITH PROPER LANGGRAPH
import os
import json
from typing import Dict, Any, List, Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated
from operator import add
import logging

logger = logging.getLogger(__name__)

# Import the real MCP tools
try:
    from backend.mcp_tools import get_real_mcp_tools
except ImportError:
    from mcp_tools import get_real_mcp_tools

class AgentState(TypedDict):
    """State for the travel agent workflow"""
    messages: Annotated[List[BaseMessage], add]
    next_step: Optional[str]

class IntelligentTravelAgent:
    """
    Intelligent travel agent using LangGraph properly
    Only calls tools when needed, no unnecessary loops
    """
    
    def __init__(self, openai_api_key: str):
        if not openai_api_key:
            raise ValueError("OpenAI API key is required")
            
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=openai_api_key
        )
        logger.info(f"🔍 Using model → {self.llm.model_name}")

        
        # Get REAL MCP tools
        self.tools = get_real_mcp_tools()
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # System prompt - SMART about when to use tools
        self.system_prompt = SystemMessage(content="""You are an intelligent travel assistant.

CRITICAL RULES:
1. For GREETINGS (hi, hello, hey) - just respond friendly, NO TOOLS
2. For TRAVEL queries - use appropriate tools (search_flights, search_hotels, etc.)
3. For GENERAL chat - respond helpfully without tools
4. NEVER loop unnecessarily - determine intent and act accordingly
5. Extract information from natural language intelligently (no regex/hardcoding)

WHEN TO USE TOOLS:
- Flight searches: When user asks about flights, flying, airlines
- Hotel searches: When user asks about hotels, accommodations, stays
- Bookings: When user wants to book after seeing results
- Itinerary: When user wants to plan a trip
- NEVER use tools for casual conversation

Be conversational and helpful. Only use tools when actually needed for travel tasks.""")
        
        # Build the workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with proper flow control"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self.agent_node)
        workflow.add_node("tools", ToolNode(self.tools))
        
        # Define the flow
        workflow.set_entry_point("agent")
        
        # Add conditional edges from agent
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        
        # Tools always go back to agent for response
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def agent_node(self, state: AgentState) -> AgentState:
        """
        Main agent node - decides what to do
        SMART: Only calls tools when needed
        """
        messages = state["messages"]
        
        # Add system prompt if this is the first call
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [self.system_prompt] + messages
        
        # Get LLM response
        response = self.llm_with_tools.invoke(messages)
        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info(f"🛠️  LLM requested tools: {response.tool_calls}")
        else:
            logger.info("ℹ️  No tool_calls in LLM response")

        
        # Return updated state with response
        return {"messages": [response]}
    
    def should_continue(self, state: AgentState) -> Literal["tools", "end"]:
        """
        Decide whether to use tools or end
        SMART: Ends conversation when no tools needed
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, execute them
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        # Otherwise, we're done - END the conversation
        return "end"
    
    def process_request(self, message: str, history: List[BaseMessage] = None) -> str:
        """
        Process a user request
        Returns the final response string
        """
        # Prepare messages
        initial_messages = history or []
        initial_messages.append(HumanMessage(content=message))
        
        # Run the workflow
        try:
            result = self.workflow.invoke(
                {"messages": initial_messages},
                config={"recursion_limit": 10}  # Reasonable limit
            )
            
            # Extract the final AI response
            if result and "messages" in result:
                # Find the last AI message
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage):
                        # Handle tool responses in content
                        if isinstance(msg.content, str):
                            return msg.content
                        elif isinstance(msg.content, list):
                            # Sometimes content is a list of text blocks
                            text_parts = []
                            for part in msg.content:
                                if isinstance(part, dict) and 'text' in part:
                                    text_parts.append(part['text'])
                                elif isinstance(part, str):
                                    text_parts.append(part)
                            return " ".join(text_parts)
                        else:
                            return str(msg.content)
            
            return "I'm here to help with your travel needs! You can ask me to search for flights, hotels, or help plan your trip."
            
        except Exception as e:
            if "recursion_limit" in str(e):
                return "I apologize, but I'm having trouble processing that request. Could you please rephrase it more simply?"
            else:
                raise e

def build_travel_workflow(openai_api_key: str):
    """Build the intelligent travel workflow"""
    agent = IntelligentTravelAgent(openai_api_key)
    return agent

def process_travel_request(message: str, openai_api_key: str, history: List = None) -> str:
    """
    Process travel request with intelligent workflow
    NO HARDCODING, proper LangGraph usage
    """
    if not openai_api_key:
        return "OpenAI API key required for intelligent processing"
    
    try:
        # Create the agent
        agent = IntelligentTravelAgent(openai_api_key)
        
        # Process the request
        response = agent.process_request(message, history)
        
        # Ensure we have a valid response
        if not response or len(response.strip()) < 2:
            # Fallback for empty responses
            if any(greeting in message.lower() for greeting in ['hi', 'hello', 'hey']):
                return "Hello! I'm your AI travel assistant. I can help you search for flights, find hotels, plan trips, and manage bookings. What would you like to do today?"
            else:
                return "I'm here to help with your travel needs. You can ask me to search for flights, hotels, or help plan your trip."
        
        return response
        
    except Exception as e:
        import logging
        logging.error(f"Error in travel request processing: {str(e)}")
        
        # User-friendly error messages
        if "rate_limit" in str(e).lower():
            return "I'm experiencing high demand right now. Please try again in a moment."
        elif "api" in str(e).lower():
            return "I'm having trouble connecting to travel services. Please check that all API keys are configured correctly."
        else:
            return f"I encountered an issue processing your request. Please try rephrasing or ask for something else. Error: {str(e)}"

# Export main functions
__all__ = ['build_travel_workflow', 'process_travel_request', 'IntelligentTravelAgent']