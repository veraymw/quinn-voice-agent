from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from typing import Dict, Any, List, Union
import json
import logging

from .tools.think_tool import think_tool
from .tools.qualification_tool import qualification_tool  
from .tools.transfer_tool import transfer_tool
from .tools.knowledge_tool import knowledge_tool
from .tools.response_validator import response_validator
from .tools.global_coverage_tool import global_coverage_tool

logger = logging.getLogger(__name__)


class QuinnAgent:
    """Modern LangGraph React Agent for Quinn Voice Assistant decision making"""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model,
            temperature=0.1,  # Low temperature for consistent sales decisions
            max_tokens=1000,  # Reasonable limit for voice call responses
            timeout=15,  # Voice call timeout optimization
        )
        
        # Initialize tools
        self.tools = [
            think_tool,
            qualification_tool,
            transfer_tool, 
            knowledge_tool,
            response_validator,
            global_coverage_tool
        ]
        
        # Create modern LangGraph agent (2025 best practice)  
        system_prompt = """You are Quinn, an AI sales assistant for Telnyx. You help qualify inbound sales calls and make intelligent routing decisions. Be concise and focused on voice call efficiency.

CRITICAL: Before providing any response to the caller, you MUST use the response_validator tool to check your intended response against capability boundaries. Only send validated responses to callers.

Validation Workflow:
1. Formulate your response
2. Call response_validator with your intended response and conversation context  
3. If approved=True: Use the validated response
4. If approved=False: Use the provided safe_response instead

You can ONLY:
- Look up customer info (Salesforce)
- Provide basic Telnyx product information and starting prices
- Check global coverage and number availability (using global_coverage_tool)
- Score and qualify leads
- Transfer calls to appropriate team members
- Send background team notifications

You CANNOT promise:
- Emails, callbacks, or follow-ups
- Specific pricing quotes or discounts (unless contract customer spending $1000+/month)
- Technical implementations or account modifications
- Access to external systems or detailed reports

Always use response validation to ensure you stay within these boundaries."""

        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt
        )
    
    async def think_and_act(
        self, 
        conversation_context: str, 
        caller_info: Union[str, Dict[str, Any]] = None,
        specific_query: str = None
    ) -> Dict[str, Any]:
        """
        Main entry point for agent decision making using modern LangGraph pattern
        
        Args:
            conversation_context: Full conversation history and context
            caller_info: Salesforce lookup results if available
            specific_query: Specific question or decision needed
            
        Returns:
            Agent's decision and reasoning
        """
        try:
            # Convert caller_info from string to dict if needed
            if isinstance(caller_info, str):
                # Parse string format like "Lead: Yimeng Wang, Company: NetEase Games, Status: SSL"
                try:
                    caller_dict = {}
                    if caller_info.strip():
                        parts = caller_info.split(", ")
                        for part in parts:
                            if ": " in part:
                                key, value = part.split(": ", 1)
                                caller_dict[key.strip()] = value.strip()
                        caller_info = caller_dict
                except Exception:
                    # If parsing fails, create a simple dict
                    caller_info = {"raw_info": caller_info}
            elif caller_info is None:
                caller_info = {}
            
            # Construct the input message for modern agent
            user_message = f"""Conversation Context: {conversation_context}
            
Caller Information: {json.dumps(caller_info, indent=2)}

{f"Specific Query: {specific_query}" if specific_query else ""}

Please analyze this conversation and determine what actions to take.
Consider: qualification level, urgency, next steps, and routing decisions."""
            
            logger.info("Quinn Agent processing conversation context")
            
            # Execute the modern LangGraph agent
            result = await self.agent.ainvoke({
                "messages": [{"role": "user", "content": user_message}]
            })
            
            # Extract final response from messages
            final_message = result["messages"][-1].content if result["messages"] else "No response"
            
            logger.info(f"Quinn Agent decision: {final_message}")
            
            return {
                "success": True,
                "decision": final_message,
                "reasoning": self._extract_reasoning_from_messages(result["messages"]),
                "actions_taken": self._extract_actions_from_messages(result["messages"])
            }
            
        except Exception as e:
            logger.error(f"Error in Quinn Agent decision making: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_action": "continue_conversation"
            }
    
    def _extract_reasoning_from_messages(self, messages: List) -> str:
        """Extract reasoning chain from LangGraph messages"""
        try:
            reasoning_steps = []
            for message in messages:
                if hasattr(message, 'content') and 'think' in message.content.lower():
                    reasoning_steps.append(message.content[:100] + "...")
            
            return " → ".join(reasoning_steps) if reasoning_steps else "Direct decision"
            
        except Exception as e:
            logger.error(f"Error extracting reasoning: {str(e)}")
            return "Reasoning unavailable"
    
    def _extract_actions_from_messages(self, messages: List) -> List[str]:
        """Extract list of actions taken by agent from messages"""
        try:
            actions = []
            for message in messages:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        actions.append(tool_call.get('name', 'unknown_tool'))
            
            return actions
            
        except Exception as e:
            logger.error(f"Error extracting actions: {str(e)}")
            return []