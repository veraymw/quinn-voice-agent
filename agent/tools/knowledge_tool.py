from langchain_core.tools import tool
import logging
import json

logger = logging.getLogger(__name__)

# Telnyx product knowledge base (simplified version)
# In production, this could be a vector database or API call
TELNYX_KNOWLEDGE = {
    "voice_api": {
        "description": "Programmable Voice API for making and receiving calls",
        "pricing": "Starting at $0.004/minute for US calls",
        "features": ["Global coverage", "Real-time webhooks", "Call recording", "Conference calling"],
        "use_cases": ["Contact centers", "Notifications", "Two-way calling", "IVR systems"]
    },
    "messaging_api": {
        "description": "SMS and MMS messaging API with global reach", 
        "pricing": "Starting at $0.0035/SMS in US",
        "features": ["10DLC support", "Short codes", "MMS", "Global coverage"],
        "use_cases": ["Notifications", "Marketing", "Two-factor auth", "Customer support"]
    },
    "sip_trunking": {
        "description": "Enterprise-grade SIP trunking service",
        "pricing": "Starting at $0.75/channel/month + usage",
        "features": ["Global connectivity", "Failover", "Real-time analytics", "99.99% uptime"],
        "use_cases": ["PBX connectivity", "Contact centers", "Enterprise voice"]
    },
    "wireless": {
        "description": "IoT and connectivity solutions",
        "pricing": "Custom pricing based on usage",
        "features": ["Global coverage", "Private networks", "SIM management", "Real-time data"],
        "use_cases": ["IoT devices", "Fleet management", "Connected vehicles", "Asset tracking"]
    },
    "verification": {
        "description": "Phone number verification and fraud prevention",
        "pricing": "Starting at $0.01/verification",
        "features": ["SMS/Voice verification", "Fraud detection", "Global coverage", "APIs"],
        "use_cases": ["User verification", "Two-factor auth", "Account security"]
    }
}

# Common pricing and feature questions
FAQ_RESPONSES = {
    "pricing": "Telnyx offers competitive usage-based pricing. Voice starts at $0.004/min, SMS at $0.0035/message. Enterprise customers get volume discounts and custom pricing.",
    "coverage": "We provide global coverage with direct connections to carriers in 60+ countries, ensuring high quality and competitive rates worldwide.",
    "support": "24/7/365 technical support with dedicated customer success managers for enterprise accounts. Average response time under 1 hour.",
    "integration": "RESTful APIs with comprehensive documentation, SDKs in multiple languages, and webhook support for real-time events.",
    "reliability": "99.99% uptime SLA with redundant infrastructure across multiple data centers and automatic failover.",
    "compliance": "SOC 2 Type II, HIPAA, PCI DSS compliant. GDPR and CCPA compliant for data protection."
}


@tool
def knowledge_tool(query: str) -> str:
    """
    Get information about Telnyx products, pricing, features, and capabilities.
    
    Args:
        query: Question about Telnyx products, pricing, or features
        
    Returns:
        Relevant product information and details
    """
    try:
        query_lower = query.lower()
        logger.info(f"Knowledge query: {query}")
        
        # Check for specific products
        for product_key, product_info in TELNYX_KNOWLEDGE.items():
            product_name = product_key.replace("_", " ")
            if product_name in query_lower or any(keyword in query_lower for keyword in product_key.split("_")):
                
                response = f"""
**{product_name.title()} Information:**

{product_info['description']}

**Pricing:** {product_info['pricing']}

**Key Features:**
{chr(10).join([f"• {feature}" for feature in product_info['features']])}

**Common Use Cases:**
{chr(10).join([f"• {use_case}" for use_case in product_info['use_cases']])}
                """.strip()
                
                logger.info(f"Found specific product info for: {product_name}")
                return response
        
        # Check for general FAQ topics
        for topic, response in FAQ_RESPONSES.items():
            if topic in query_lower:
                logger.info(f"Found FAQ info for: {topic}")
                return f"**{topic.title()}:** {response}"
        
        # Handle comparison questions
        if "compare" in query_lower or "vs" in query_lower:
            return """
**Product Comparison:**

• **Voice API**: Best for call applications, IVR, contact centers
• **Messaging API**: Ideal for notifications, marketing, 2FA
• **SIP Trunking**: Enterprise PBX connectivity and voice infrastructure  
• **Wireless**: IoT connectivity and device management
• **Verification**: Identity verification and fraud prevention

Would you like detailed information about any specific product?
            """.strip()
        
        # Handle pricing questions
        if any(word in query_lower for word in ["price", "cost", "pricing", "rate"]):
            return """
**Telnyx Pricing Overview:**

• **Voice API**: $0.004/minute (US), competitive global rates
• **Messaging API**: $0.0035/SMS (US), volume discounts available
• **SIP Trunking**: $0.75/channel/month + usage
• **Custom Enterprise Pricing**: Available for high-volume customers

All pricing is usage-based with no setup fees or monthly minimums. Enterprise customers receive volume discounts and dedicated support.
            """.strip()
        
        # Default response for unmatched queries
        logger.info("General knowledge response provided")
        return """
I can help you with information about:

• **Voice API** - Programmable calling and voice applications
• **Messaging API** - SMS/MMS messaging solutions  
• **SIP Trunking** - Enterprise voice connectivity
• **Wireless** - IoT and connectivity solutions
• **Verification** - Phone number verification and security

I can also provide details about pricing, coverage, integration, support, and compliance.

What specific information would you like to know about?
        """.strip()
        
    except Exception as e:
        logger.error(f"Error in knowledge tool: {str(e)}")
        return f"I'm sorry, I encountered an error retrieving that information. Please try asking your question in a different way, or I can connect you with a specialist who can help."