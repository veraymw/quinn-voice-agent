from langchain_core.tools import tool
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

# Mock phone numbers for transfer targets (replace with real numbers)
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
    }
}


@tool
def transfer_tool(qualification: str, urgency: str, reason: str, caller_info: str = "{}") -> str:
    """
    Determine call transfer routing based on qualification and urgency.
    
    Args:
        qualification: Lead qualification level (SQL, SSL, DQ)
        urgency: Urgency level (high, low)
        reason: Reason for transfer consideration
        caller_info: JSON string of caller information
        
    Returns:
        JSON string with transfer decision and target information
    """
    try:
        # Parse caller info
        try:
            caller_data = json.loads(caller_info) if caller_info else {}
        except json.JSONDecodeError:
            caller_data = {}
        
        logger.info(f"Transfer decision for {qualification} lead with {urgency} urgency")
        
        # Transfer logic based on qualification and urgency
        should_transfer = False
        transfer_target = None
        transfer_reason = ""
        
        if qualification == "SQL":
            # SQL always goes to AE regardless of urgency
            should_transfer = True
            transfer_target = "AE"
            transfer_reason = "Qualified SQL lead - routing to Account Executive"
            
        elif qualification in ["SSL", "DQ"] and urgency == "high":
            # High urgency SSL/DQ goes to BDR
            should_transfer = True
            transfer_target = "BDR"
            transfer_reason = "High urgency situation - routing to BDR for immediate assistance"
            
        else:
            # SSL/DQ with low urgency continues with Quinn
            should_transfer = False
            transfer_reason = "Continuing conversation with Quinn - no transfer needed"
        
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
            "original_reason": reason
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