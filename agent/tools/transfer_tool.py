from langchain_core.tools import tool
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

# Enhanced transfer targets with intent-aware routing
TRANSFER_TARGETS = {
    "AE": {
        "name": "Account Executive Queue",
        "phone": "+1-555-0100",  # Replace with real AE queue number
        "description": "For qualified SQL leads (Score 80+)"
    },
    "BDR": {
        "name": "Business Development Rep Queue", 
        "phone": "+1-555-0200",  # Replace with real BDR queue number
        "description": "For urgent SSL/DQ leads or complex situations"
    },
    "SUPPORT": {
        "name": "Customer Support",
        "phone": "+1-555-0300",  # Replace with real support number
        "description": "For existing customer issues and technical support"
    },
    "BILLING": {
        "name": "Billing Support",
        "phone": "+1-555-0400",  # Replace with real billing number
        "description": "For billing questions and account management"
    }
}


@tool
def transfer_tool(qualification: str, urgency: str, reason: str, caller_info: str = "{}", 
                 intent_classification: str = "{}") -> str:
    """
    Determine call transfer routing based on qualification, urgency, and intent classification.
    
    Args:
        qualification: Lead qualification level (SQL, SSL, DQ)
        urgency: Urgency level (high, low)
        reason: Reason for transfer consideration
        caller_info: JSON string of caller information
        intent_classification: JSON string of intent classification data from qualification_tool
        
    Returns:
        JSON string with transfer decision and target information
    """
    try:
        # Parse caller info
        try:
            caller_data = json.loads(caller_info) if caller_info else {}
        except json.JSONDecodeError:
            caller_data = {}
        
        # Parse intent classification
        try:
            intent_data = json.loads(intent_classification) if intent_classification else {}
        except json.JSONDecodeError:
            intent_data = {}
        
        primary_intent = intent_data.get("primary_intent", "other")
        intent_confidence = intent_data.get("confidence", 0.0)
        
        logger.info(f"Transfer decision for {qualification} lead with {urgency} urgency and {primary_intent} intent (confidence: {intent_confidence:.2f})")
        
        # Intent-aware transfer logic
        should_transfer = False
        transfer_target = None
        transfer_reason = ""
        
        # Priority 1: Support intent - Route to support regardless of qualification
        if primary_intent == "support" and intent_confidence >= 0.7:
            should_transfer = True
            
            # Determine support type based on conversation content
            reason_lower = reason.lower()
            if any(word in reason_lower for word in ["billing", "invoice", "payment", "credit card"]):
                transfer_target = "BILLING"
                transfer_reason = "Support intent detected - routing to Billing Support for account issues"
            else:
                transfer_target = "SUPPORT"
                transfer_reason = "Support intent detected - routing to Customer Support for technical assistance"
                
        # Priority 2: Sales intent with qualification-based routing
        elif primary_intent == "sales" and intent_confidence >= 0.7:
            if qualification == "SQL":
                # High-value sales leads go to AE
                should_transfer = True
                transfer_target = "AE"
                transfer_reason = "Sales intent + SQL qualification - routing to Account Executive"
                
            elif qualification in ["SSL", "DQ"] and urgency == "high":
                # Urgent lower-qualified sales leads go to BDR
                should_transfer = True
                transfer_target = "BDR" 
                transfer_reason = "Sales intent + high urgency - routing to BDR for immediate assistance"
            else:
                # Continue conversation for discovery
                should_transfer = False
                transfer_reason = "Sales intent + low urgency - continuing discovery conversation"
                
        # Priority 3: Other intent or low confidence - Use traditional qualification logic
        else:
            if qualification == "SQL":
                should_transfer = True
                transfer_target = "AE"
                transfer_reason = "SQL qualification - routing to Account Executive (intent unclear)"
                
            elif qualification in ["SSL", "DQ"] and urgency == "high":
                should_transfer = True
                transfer_target = "BDR"
                transfer_reason = "High urgency situation - routing to BDR (intent unclear)"
            else:
                should_transfer = False
                transfer_reason = "Continuing conversation - unclear intent, additional discovery needed"
        
        # Get transfer target details
        target_info = None
        if should_transfer and transfer_target in TRANSFER_TARGETS:
            target_info = TRANSFER_TARGETS[transfer_target].copy()
            
            # Try to get specific AE from caller info if SQL
            if transfer_target == "AE" and caller_data.get("record", {}).get("AE_Phone"):
                target_info["phone"] = caller_data["record"]["AE_Phone"]
                target_info["name"] = f"{caller_data['record'].get('AE_Name', 'Account Executive')}"
                target_info["description"] = "Direct transfer to assigned Account Executive"
        
        result = {
            "should_transfer": should_transfer,
            "transfer_target": transfer_target,
            "transfer_reason": transfer_reason,
            "target_info": target_info,
            "qualification": qualification,
            "urgency": urgency,
            "original_reason": reason,
            
            # Intent classification information (NEW)
            "intent_classification": {
                "primary_intent": primary_intent,
                "confidence": intent_confidence,
                "reasoning": intent_data.get("intent_reasoning", "No intent reasoning available")
            },
            
            # Enhanced routing metadata
            "routing_logic": "intent_aware",
            "intent_confidence_threshold": 0.7,
            "routing_priority": (
                "support" if primary_intent == "support" and intent_confidence >= 0.7 else
                "sales_qualified" if primary_intent == "sales" and qualification == "SQL" else
                "traditional_qualification"
            )
        }
        
        if should_transfer:
            logger.info(f"Transfer approved: {transfer_target} - {transfer_reason}")
        else:
            logger.info("Transfer not needed - continuing conversation")
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in transfer tool: {str(e)}")
        error_result = {
            "should_transfer": False,
            "error": str(e),
            "transfer_reason": "Error occurred - continuing conversation"
        }
        return json.dumps(error_result, indent=2)