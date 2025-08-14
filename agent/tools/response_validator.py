from langchain_core.tools import tool
import re
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Validation patterns based on real DialPad conversation evidence
VALIDATION_PATTERNS = {
    "commitment_violations": [
        # Email commitments
        r"\b(?:I'll|I will)\s+(?:email|send|forward)\s+you",
        r"\bI'll\s+(?:get back to you|follow up|reach out)",
        
        # Callback promises  
        r"\b(?:I'll|someone will)\s+call\s+you\s+back",
        r"\bI'll\s+have\s+someone\s+(?:call|contact)\s+you",
        
        # Scheduling commitments - UPDATED: more specific patterns
        r"\b(?:I'll|I can|let me)\s+schedule\s+(?:a|your|the)\s+(?:demo|meeting|call)",
        r"\blet me\s+book\s+(?:you|a|your)\s+(?:demo|meeting|appointment)",
        
        # Follow-up commitments
        r"\bI'll\s+(?:check on|follow up on|look into)\s+that",
        r"\bI'll\s+make sure\s+(?:you|that|this)",
        
        # External system access
        r"\bI'll\s+(?:update|check)\s+your\s+(?:CRM|account)(?!\s+with\s+us)",
        r"\blet me\s+access\s+your\s+(?!Telnyx|Salesforce)"
    ],
    
    "pricing_violations": [
        # Specific unauthorized quotes
        r"\byour\s+(?:price|cost|rate)\s+(?:would|will)\s+be\s+\$\d+",
        r"\bI\s+can\s+give\s+you\s+\d+%\s+discount(?!\s+if|\s+for\s+contract)",
        
        # Contract terms without qualification
        r"\bI\s+can\s+offer\s+you\s+a\s+\d+-?year\s+deal",
        r"\bno\s+setup\s+fees?\s+for\s+you(?!\s+with\s+contract)",
        
        # Direct billing promises
        r"\bI'll\s+(?:adjust|update|modify)\s+your\s+billing",
        r"\bI\s+can\s+(?:process|handle)\s+a\s+refund"
    ],
    
    "technical_violations": [
        # Feature promises
        r"\b(?:we're|I'm)\s+(?:adding|building)\s+that\s+feature",
        r"\bthat\s+(?:will|should)\s+be\s+available\s+(?:soon|next)",
        
        # Implementation commitments  
        r"\bI'll\s+(?:set up|configure|implement|get.*configured)\s+",
        r"\bI'll\s+get\s+that\s+(?:configured|set up)",
        r"\blet me\s+get\s+that\s+(?:configured|set up)",
        
        # Technical support
        r"\bI'll\s+(?:fix|resolve|troubleshoot)\s+(?:that|your)",
        r"\bI\s+can\s+help\s+you\s+(?:configure|set up|implement)"
    ],
    
    "information_violations": [
        # Document delivery
        r"\bI'll\s+(?:send|share|forward)\s+you\s+(?:documentation|whitepaper)",
        r"\blet me\s+send\s+you\s+(?:that|the)",
        
        # Data analysis promises
        r"\bI'll\s+(?:pull|analyze|review)\s+your\s+(?:reports|data|usage)",
        r"\bI\s+can\s+check\s+your\s+(?:account\s+history|call\s+logs)"
    ]
}

# Safe alternative responses
SAFE_ALTERNATIVES = {
    "commitment_violations": "I can't handle that directly, but I can transfer you to someone from our team who can help with that request right away.",
    "pricing_violations": "For product or pricing questions I'd recommend checking telnyx dot com slash pricing, it's not gonna be any different than what you see online. You can find all of our pricing and feature information on the website. The platform's built for self-service customers so you can find everything there.",
    "technical_violations": "For technical implementation support, I'd recommend reaching out to our support team who can assist with that. As a sales assistant, I'm not able to help with support related questions.",
    "information_violations": "I can transfer you to someone who can provide you with the specific information and documentation you need."
}

@tool
def response_validator(intended_response: str, conversation_context: str = "") -> Dict[str, Any]:
    """
    Validates Quinn's intended response against capability boundaries.
    
    Args:
        intended_response: What Quinn plans to say to the caller
        conversation_context: Current conversation context for validation
        
    Returns:
        Validation result with approved response or safe alternative
    """
    try:
        violations = []
        
        # Check each violation category
        for category, patterns in VALIDATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, intended_response, re.IGNORECASE):
                    violations.append({
                        "category": category,
                        "pattern": pattern,
                        "severity": "high" if category in ["pricing_violations", "commitment_violations"] else "medium"
                    })
                    logger.warning(f"Response validation violation: {category} - {pattern}")
                    break  # Only log first violation per category
        
        # Check for contract customer context (allows some pricing discussions)
        has_contract_context = _has_contract_qualification_context(intended_response, conversation_context)
        
        if violations:
            # Filter out pricing violations if properly qualified
            if has_contract_context:
                violations = [v for v in violations if not _is_qualified_pricing_discussion(v, intended_response)]
        
        if violations:
            # Get the most severe violation type
            primary_violation = max(violations, key=lambda v: {"high": 3, "medium": 2, "low": 1}[v["severity"]])
            safe_response = SAFE_ALTERNATIVES.get(primary_violation["category"], SAFE_ALTERNATIVES["commitment_violations"])
            
            # Log violation for monitoring
            _log_validation_violation(violations, intended_response, conversation_context)
            
            return {
                "approved": False,
                "violations": violations,
                "safe_response": safe_response,
                "original_response": intended_response
            }
        
        # Response is clean
        logger.info("Response validation passed")
        return {
            "approved": True,
            "response": intended_response,
            "violations": []
        }
        
    except Exception as e:
        logger.error(f"Response validation error: {str(e)}")
        # Fail safe - allow response but log error
        return {
            "approved": True,
            "response": intended_response,
            "validation_error": str(e),
            "fallback_used": True
        }

def _has_contract_qualification_context(response: str, context: str) -> bool:
    """Check if response has proper contract customer qualification context"""
    combined_text = f"{response} {context}".lower()
    qualification_indicators = [
        r"\$?1,?000.*per\s+month",
        r"contract\s+customer",
        r"high-?volume",
        r"enterprise\s+customer",
        r"spending\s+over.*\$?1,?000"
    ]
    return any(re.search(indicator, combined_text) for indicator in qualification_indicators)

def _is_qualified_pricing_discussion(violation: Dict[str, Any], response: str) -> bool:
    """Check if pricing violation is actually allowed due to proper qualification"""
    if violation["category"] != "pricing_violations":
        return False
    
    # Allow discount mentions if properly qualified
    if "discount" in violation["pattern"]:
        qualification_present = any(phrase in response.lower() for phrase in [
            "contract customer", "spending over", "$1000", "$1,000", "high volume", "enterprise"
        ])
        return qualification_present
    
    return False

def _log_validation_violation(violations: List[Dict[str, Any]], response: str, context: str):
    """Log validation violations for monitoring and improvement"""
    try:
        violation_log = {
            "timestamp": datetime.now().isoformat(),
            "violations": violations,
            "blocked_response": response[:200],  # First 200 chars for privacy
            "context_snippet": context[-100:] if context else "",  # Last 100 chars of context
            "violation_count": len(violations)
        }
        
        logger.warning(f"Response blocked by validation: {len(violations)} violations")
        # In production, this could be sent to monitoring system
        
    except Exception as e:
        logger.error(f"Error logging validation violation: {str(e)}")