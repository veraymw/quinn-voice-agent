from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import logging

logger = logging.getLogger(__name__)

# Global LLM instance for think tool (can be shared across tools)
_think_llm = None

def get_think_llm(api_key: str, model: str = "gpt-4o-mini"):
    """Get or create the LLM instance for thinking"""
    global _think_llm
    if _think_llm is None:
        _think_llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=0.3,  # Slightly higher for creative reasoning
            max_tokens=500
        )
    return _think_llm


@tool
def think_tool(reasoning_prompt: str) -> str:
    """
    Internal reasoning tool for complex sales decisions.
    Use this when you need to think through qualification, urgency, or routing decisions.
    
    Args:
        reasoning_prompt: What you want to think about or analyze
        
    Returns:
        Structured reasoning and conclusions
    """
    try:
        from config import settings
        
        llm = get_think_llm(settings.openai_api_key, settings.openai_model)
        
        # Enhanced prompt for sales-specific reasoning
        enhanced_prompt = f"""
        You are Quinn's internal reasoning system. Analyze this sales situation and provide clear, actionable insights.
        
        Context: {reasoning_prompt}
        
        Please analyze:
        1. Caller's qualification level (Enterprise, Mid-market, SMB, or Not qualified)
        2. Urgency indicators (Immediate need, Exploring, Future planning)
        3. Interest signals (Strong, Medium, Weak)
        4. Next best action recommendation
        5. Reasoning for your assessment
        
        Provide a structured response with clear recommendations.
        """
        
        result = llm.invoke(enhanced_prompt)
        
        logger.info("Think tool processed reasoning request")
        return result.content
        
    except Exception as e:
        logger.error(f"Error in think tool: {str(e)}")
        return f"Unable to process reasoning: {str(e)}"