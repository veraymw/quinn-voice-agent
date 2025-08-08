from langchain_core.tools import tool
from typing import Dict, Any
import json
import logging
import re

logger = logging.getLogger(__name__)


@tool  
def qualification_tool(conversation_context: str, caller_info: str = "{}") -> str:
    """
    Qualify a lead based on conversation context and caller information.
    Returns qualification score, level, and routing recommendation.
    
    Args:
        conversation_context: Full conversation history and context
        caller_info: JSON string of caller information from Salesforce
        
    Returns:
        JSON string with qualification results
    """
    try:
        # Parse caller info if provided
        try:
            caller_data = json.loads(caller_info) if caller_info else {}
        except json.JSONDecodeError:
            caller_data = {}
        
        logger.info(f"Qualifying lead with context length: {len(conversation_context)}")
        
        # Initialize scoring
        score = 0
        qualification_factors = []
        urgency_indicators = []
        
        # Company size indicators (20 points max)
        company_signals = [
            ("enterprise", 20), ("corporation", 15), ("inc.", 10), 
            ("llc", 8), ("startup", 5), ("consulting", 3)
        ]
        
        context_lower = conversation_context.lower()
        for signal, points in company_signals:
            if signal in context_lower:
                score += points
                qualification_factors.append(f"Company type: {signal} (+{points})")
                break
        
        # Use case quality (25 points max) 
        high_value_use_cases = [
            ("voice api", 25), ("messaging api", 20), ("sip trunking", 20),
            ("contact center", 18), ("pbx", 15), ("sms api", 12),
            ("international", 10), ("compliance", 8)
        ]
        
        for use_case, points in high_value_use_cases:
            if use_case in context_lower:
                score += points
                qualification_factors.append(f"Use case: {use_case} (+{points})")
                break
        
        # Volume/scale indicators (20 points max)
        volume_patterns = [
            (r"million", 20), (r"thousand", 15), (r"hundreds?", 10),
            (r"bulk", 12), (r"high.?volume", 15), (r"scale", 8)
        ]
        
        for pattern, points in volume_patterns:
            if re.search(pattern, context_lower):
                score += points
                qualification_factors.append(f"Volume indicator: {pattern} (+{points})")
                break
        
        # Budget/timeline indicators (15 points max)
        budget_signals = [
            ("budget approved", 15), ("need asap", 12), ("this quarter", 10),
            ("pricing", 8), ("quote", 6), ("proposal", 5)
        ]
        
        for signal, points in budget_signals:
            if signal in context_lower:
                score += points
                qualification_factors.append(f"Budget/timeline: {signal} (+{points})")
                break
        
        # Existing customer bonus (10 points)
        if caller_data.get("type") == "contact":
            score += 10
            qualification_factors.append("Existing customer (+10)")
        
        # Authority indicators (10 points max)
        authority_titles = [
            ("cto", 10), ("ceo", 10), ("director", 8), ("manager", 6),
            ("lead", 4), ("senior", 3)
        ]
        
        for title, points in authority_titles:
            if title in context_lower:
                score += points
                qualification_factors.append(f"Authority level: {title} (+{points})")
                break
        
        # Determine urgency
        urgency_keywords = [
            "urgent", "asap", "immediately", "emergency", "down", "broken",
            "deadline", "launch", "go-live", "critical"
        ]
        
        urgency = "high" if any(keyword in context_lower for keyword in urgency_keywords) else "low"
        
        if urgency == "high":
            urgency_indicators.append("Urgent language detected")
        
        # Determine qualification level
        if score >= 80:
            qualification = "SQL"
            recommend_transfer = True
            transfer_target = "AE"
        elif score >= 50:
            qualification = "SSL" 
            recommend_transfer = urgency == "high"
            transfer_target = "BDR" if urgency == "high" else None
        else:
            qualification = "DQ"
            recommend_transfer = False
            transfer_target = None
        
        result = {
            "score": score,
            "qualification": qualification,
            "urgency": urgency,
            "recommend_transfer": recommend_transfer,
            "transfer_target": transfer_target,
            "qualification_factors": qualification_factors,
            "urgency_indicators": urgency_indicators,
            "reasoning": f"Score {score}/100: {qualification} with {urgency} urgency"
        }
        
        logger.info(f"Qualification result: {qualification} (Score: {score})")
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in qualification tool: {str(e)}")
        error_result = {
            "score": 0,
            "qualification": "DQ",
            "urgency": "low", 
            "recommend_transfer": False,
            "transfer_target": None,
            "error": str(e)
        }
        return json.dumps(error_result, indent=2)