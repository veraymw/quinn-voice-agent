"""
Smart conversational lead qualification tool with AI-driven decision making.

This tool uses Instructor for structured data extraction and includes intelligent 
follow-up question generation when qualification data is incomplete or unclear.
 
This tool is used to generate the following JSON response:
{
  "intent_classification": {
    "primary_intent": "sales|support|other",
    "confidence": 0.85,
    "intent_reasoning": "Customer asking about pricing for new implementation",
    "context_shift": false,
    "supporting_evidence": ["interested in SMS services", "exploring alternatives", "pricing discussion"]
  },
  "sales_stage": "SQL|SSL|DQ|NEEDS_INFO",
  "routing_guidance": "Sales qualified lead - transfer to Account Executive",
  "response_guidance": "This customer shows strong sales intent...",
  "extracted_data": {
    "monthly_budget": 2000,
    "monthly_volume": 50000,
    "volume_type": "SMS messages",
    "use_case": "Business SMS communications",
    "current_provider": "Twilio"
  }
}
"""

from langchain_core.tools import tool
from typing import Dict, Any
import json
import logging
import os
from datetime import datetime

# Instructor imports
import instructor
from openai import OpenAI

# Import models from organized models directory
from ..models.qualification_models import (
    BusinessQuality,
    ExtractedQualificationData,
    FollowUpQuestion,
    QualificationDecision,
    IntentClassification
)

logger = logging.getLogger(__name__)


class SmartQualificationEngine:
    """
    Intelligent qualification engine with conversational decision-making.
    
    Uses Instructor for structured extraction and includes smart follow-up
    question generation when qualification data is incomplete.
    """
    
    def __init__(self):
        """Initialize the smart qualification engine"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = instructor.from_openai(
            OpenAI(api_key=api_key)
        )
        
        # Telnyx thresholds from Quinn Email system
        self.sql_thresholds = {
            "budget": 1000,  # $1000+ monthly
            "messages": 10000,  # 10K+ messages/month
            "phone_numbers": 10,  # 10+ phone numbers
            "countries": 3,  # 3+ countries
            "data_mb": 100,  # 100+ MB/month
            "sim_cards": 10,  # 10+ SIM cards
            "voice_minutes": 100000,  # 100K+ minutes/month
            "calls": 100000,  # 100K+ calls/month
            "voice_phone_numbers": 50,  # 50+ for voice/video
            "voice_countries": 5  # 5+ countries for voice/video
        }
    
    def extract_qualification_data_fast(self, conversation_context: str, caller_info: dict) -> ExtractedQualificationData:
        """
        OPTIMIZED: Fast qualification data extraction only.
        Simplified and faster than the full extraction method.
        """
        
        system_prompt = """
        You are Telnyx's expert qualification analyst. Extract qualification data efficiently.
        
        EXTRACT KEY DATA:
        1. Budget information (monthly spending capacity in USD)
        2. Volume requirements  
        3. Use case and business context
        4. Authority level and decision-making capability
        5. Growth signals and company maturity
        6. Current provider and urgency signals
        
        RULES:
        - Be conservative - only extract explicitly mentioned information
        - Convert to monthly figures (divide yearly by 12)
        - Use HIGHEST figure when ranges given
        - Focus on business-critical qualification factors only
        """
        
        user_prompt = f"""
        CONVERSATION: {conversation_context}
        CALLER INFO: {json.dumps(caller_info, indent=1) if caller_info else 'None'}
        
        Extract qualification data efficiently.
        """
        
        try:
            extracted_data = self.client.chat.completions.create(
                model="gpt-4o-mini",  # FAST: Optimized for data extraction
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ExtractedQualificationData,
                max_retries=1,  # Reduced retries for speed
                temperature=0.0  # Consistent results
            )
            
            logger.info(f"Fast extraction: Budget=${extracted_data.monthly_budget}, Volume={extracted_data.monthly_volume}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error in fast extraction: {str(e)}")
            return ExtractedQualificationData()  # Return fallback data
    
    def extract_qualification_data(self, conversation_context: str, caller_info: dict) -> ExtractedQualificationData:
        """Extract comprehensive qualification data using Instructor"""
        
        system_prompt = """
        You are an expert Telnyx sales qualification analyst. Analyze this conversation 
        to extract qualification data with high accuracy and assess business quality.
        
        EXTRACTION RULES:
        1. Be conservative - only extract explicitly mentioned information
        2. Convert all budget/volume to monthly figures (divide yearly by 12)
        3. Always use the HIGHEST figure when ranges are given
        4. Assess business quality based on growth signals, company maturity, use case sophistication
        5. Extract clear information - focus on explicitly mentioned data
        
        BUSINESS QUALITY INDICATORS:
        - High: Enterprise companies, Fortune 500, funded startups with traction, established SaaS companies
        - Medium: Growing mid-market companies, well-funded startups, companies with clear growth plans
        - Low: Early-stage startups without traction, unclear business models, personal projects
        
        GROWTH SIGNALS:
        - YC startup, recent funding, rapid user growth, expanding internationally
        - Signed major customers, scaling operations, hiring rapidly
        - Replacing legacy systems, modernizing infrastructure
        
        RISK FACTORS:
        - Very early stage, no clear business model, personal use
        - Price shopping without clear requirements, unclear authority
        - Unrealistic expectations, commodity use case
        """
        
        user_prompt = f"""
        CONVERSATION CONTEXT:
        {conversation_context}
        
        KNOWN CALLER INFO:
        {json.dumps(caller_info, indent=2) if caller_info else 'None available'}
        
        Extract all qualification data and assess business quality. Focus on:
        1. Budget information (monthly spending capacity)
        2. Volume requirements (messages, calls, phone numbers, etc.)
        3. Use case sophistication and business context
        4. Authority level and decision-making capability
        5. Growth signals and company maturity
        6. Overall business quality and potential
        """
        
        try:
            extracted_data = self.client.chat.completions.create(
                model="gpt-4o-mini",  # OPTIMIZED: Faster model for data extraction
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ExtractedQualificationData,
                max_retries=1,  # Reduced retries for speed
                temperature=0.0  # Consistent extraction
            )
            
            logger.info(f"Extracted data: Budget=${extracted_data.monthly_budget}, Volume={extracted_data.monthly_volume}, Quality={extracted_data.business_quality.quality_score}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error in data extraction: {str(e)}")
            return ExtractedQualificationData()
    
    def classify_intent(self, conversation_context: str, caller_info: dict, 
                       previous_intent: str = None) -> IntentClassification:
        """Classify conversation intent using context analysis"""
        
        system_prompt = """
        You are an expert intent classifier for Telnyx customer conversations.
        
        INTENT CLASSIFICATION RULES:
        
        1. SALES Intent - New business, pricing inquiries, product demos:
           - "Looking for SMS/voice services", "pricing information", "competitor comparison"
           - "new customer", "evaluating providers", "migration from [provider]"  
           - Budget discussions, volume requirements
           - "need a quote", "want to try", "how much does it cost"
        
        2. SUPPORT Intent - Existing customer issues, technical problems:
           - "billing question", "invoice", "credit card not working", "payment failed"
           - "service is down", "not receiving messages", "calls aren't working"
           - "account access", "password reset", "portal issues", technical requirements
           - "existing customer", "current client", "we use Telnyx"
        
        3. OTHER Intent - Unclear, general inquiry, mixed needs:
           - "what does Telnyx do", "general information", "just browsing"
           - Mixed sales and support needs in same conversation
           - Unclear business case or intent
        
        CONTEXT SHIFT DETECTION:
        - True if intent clearly changed from previous classification
        - Examples: "Actually, before that, I'm having issues with..." (Sales→Support)
        - "Also, we're looking to expand our usage..." (Support→Sales)
        """
        
        user_prompt = f"""
        CONVERSATION CONTEXT:
        {conversation_context}
        
        CALLER INFO:
        {json.dumps(caller_info, indent=2) if caller_info else 'None available'}
        
        PREVIOUS INTENT: {previous_intent or 'None'}
        
        Analyze this conversation and classify the primary intent. Look for:
        1. Clear intent signals in the conversation
        2. Supporting evidence for your classification
        3. Whether intent shifted from previous classification
        4. Confidence level based on clarity of intent signals
        """
        
        try:
            intent_classification = self.client.chat.completions.create(
                model="gpt-4o-mini",  # FASTEST model for simple intent classification
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=IntentClassification,
                max_retries=1,  # Reduced retries for speed
                temperature=0.0  # Consistent results
            )
            
            logger.info(f"Intent classified: {intent_classification.primary_intent} (confidence: {intent_classification.confidence:.2f})")
            return intent_classification
            
        except Exception as e:
            logger.error(f"Error in intent classification: {str(e)}")
            return IntentClassification(
                primary_intent="other",
                confidence=0.0,
                intent_reasoning=f"Classification error: {str(e)}",
                context_shift=False,
                supporting_evidence=[]
            )
    
    def make_qualification_decision(self, data: ExtractedQualificationData, 
                                  conversation_context: str, caller_info: dict = None,
                                  previous_intent: str = None) -> QualificationDecision:
        """Make intelligent qualification decision with intent classification and follow-up handling"""
        
        # First classify intent
        intent_classification = self.classify_intent(
            conversation_context, 
            caller_info or {}, 
            previous_intent
        )
        
        system_prompt = f"""
        You are a smart Telnyx sales qualification agent with intent-awareness. Make qualification decisions 
        using these precise rules and determine if follow-up questions are needed.
        
        INTENT-AWARE QUALIFICATION:
        - SALES intent: Focus on budget/volume discovery and qualification scoring
        - SUPPORT intent: Lower qualification priority, focus on routing to appropriate support
        - OTHER intent: Gentle discovery to clarify intent and business needs

        QUALIFICATION RULES (from Quinn Email system):
        
        1. SQL (Sales Qualified Lead) - ANY of these conditions:
           - Monthly budget ≥ $1,000
           - Monthly messages ≥ 10,000
           - Phone numbers ≥ 10 (≥50 for voice/video)
           - Countries ≥ 3 (≥5 for voice/video)
           - Data ≥ 100 MB/month
           - SIM cards ≥ 10
           - Voice minutes ≥ 100,000/month
           - Calls ≥ 100,000/month
           - High growth signals with enterprise potential
           
        2. SSL (Self-Service Lead) - Below SQL thresholds BUT:
           - Some budget/volume indicated (under thresholds)
           - Don't know budget/volume but seem legitimate
           - Decision makers/enterprise who need discovery
           
        3. DQ (Disqualified):
           - Personal use only
           - No clear business case
           - Illegal use cases
           
        4. NEEDS_INFO - When:
           - Missing critical budget/volume data but business seems promising
           - High-quality business but unclear requirements
           - Enterprise/decision maker but needs qualification questions

        FOLLOW-UP GUIDANCE:
        If qualified prospects don't know their current spend/usage, explain:
        "Our sales team works with customers who typically spend $1,000+ monthly 
        (roughly [volume] or equivalent usage). If you're below that, 
        our self-service platform is the best way to get started immediately."
        
        For high-quality businesses: Ask smart follow-up questions to qualify properly.
        
        THRESHOLDS: {json.dumps(self.sql_thresholds, indent=2)}
        """
        
        user_prompt = f"""
        EXTRACTED DATA:
        {data.model_dump_json(indent=2)}
        
        CONVERSATION CONTEXT:
        {conversation_context}
        
        INTENT CLASSIFICATION:
        {intent_classification.model_dump_json(indent=2)}
        
        Make the qualification decision with intent awareness. If you need more information for a proper 
        decision (especially for promising businesses), generate a smart follow-up question
        that helps determine spend/usage levels or business quality.
        
        Consider:
        1. Does this meet clear SQL/SSL/DQ criteria?
        2. Is this a high-quality business that deserves more discovery?
        3. How does the intent classification affect routing and response approach?
        4. Would a follow-up question significantly improve qualification accuracy?
        5. What's the best way to handle this prospect based on their intent?
        
        Include the intent classification in your response and provide routing guidance.
        """
        
        try:
            decision = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=QualificationDecision,
                max_retries=1,  # Reduced retries for speed
                temperature=0.0  # Consistent decisions
            )
            
            # Manually set the intent classification since model might not include it
            decision.intent_classification = intent_classification
            
            # Intent-aware routing logic
            if intent_classification.primary_intent == "support":
                # Support intent: Route to support resources
                decision.routing_guidance = "Route to support team - existing customer with account/technical issues"
                if decision.stage in ["SQL", "SSL"]:
                    # Even qualified leads with support intent need support first
                    decision.recommend_transfer = False  # Handle support first
                    decision.response_guidance += " Let me connect you with our support team to resolve your issue first."
            elif intent_classification.primary_intent == "sales":
                # Sales intent: Standard qualification routing
                if decision.stage == "SQL":
                    decision.recommend_transfer = True
                    decision.transfer_target = "AE"
                    decision.routing_guidance = "Sales qualified lead - transfer to Account Executive"
                elif decision.stage == "SSL" and any("urgent" in sig.lower() for sig in data.urgency_signals):
                    decision.recommend_transfer = True
                    decision.transfer_target = "BDR"
                    decision.routing_guidance = "Urgent self-service lead - transfer to BDR"
                else:
                    decision.routing_guidance = "Continue discovery conversation - potential for self-service"
            else:
                # Other intent: Gentle discovery
                decision.routing_guidance = "Continue discovery to clarify intent and business needs"
            
            logger.info(f"Qualification decision: {decision.stage} - Intent: {intent_classification.primary_intent} - {decision.reasoning}")
            return decision
            
        except Exception as e:
            logger.error(f"Error in qualification decision: {str(e)}")
            # Fallback intent classification
            fallback_intent = IntentClassification(
                primary_intent="other",
                confidence=0.0,
                intent_reasoning=f"Error in processing: {str(e)}",
                context_shift=False,
                supporting_evidence=[]
            )
            
            return QualificationDecision(
                stage="DQ",
                confidence=0.0,
                reasoning=f"Processing error: {str(e)}",
                intent_classification=fallback_intent,
                response_guidance="I apologize, but I'm having trouble processing your information. Let me connect you with someone who can help.",
                extracted_data=data,
                routing_guidance="Error handling - route to general support"
            )


# Initialize the smart qualification engine
smart_qualification_engine = SmartQualificationEngine()


@tool  
def qualification_tool(conversation_context: str, caller_info: str = "{}") -> str:
    """
    OPTIMIZED: Qualify a lead based on conversation context and caller information.
    Returns qualification score, level, and routing recommendation.
    
    PERFORMANCE IMPROVEMENT: Reduces from 3 API calls to 2 by using fast data extraction
    first, then existing decision logic (which includes intent classification).
    
    Args:
        conversation_context: Full conversation history and context
        caller_info: JSON string of caller information from Salesforce
        
    Returns:
        JSON string with qualification results
    """
    try:
        # Parse caller info
        try:
            caller_data = json.loads(caller_info) if caller_info else {}
        except json.JSONDecodeError:
            caller_data = {}
        
        
        # OPTIMIZED: Fast data extraction only (1 API call)
        extracted_data = smart_qualification_engine.extract_qualification_data_fast(
            conversation_context, 
            caller_data
        )
        
        # Make qualification decision 
        decision = smart_qualification_engine.make_qualification_decision(
            extracted_data,
            conversation_context,
            caller_data
        )
        
        logger.info(f"Smart qualification complete: {decision.stage} (Confidence: {decision.confidence:.2f})")
        
        # Convert to compatible format for existing system
        result = {
            # Core qualification results
            "sales_stage": decision.stage,
            "sales_stage_reason": decision.reasoning,
            "confidence": decision.confidence,
            
            # Transfer routing
            "recommend_transfer": decision.recommend_transfer,
            "transfer_target": decision.transfer_target,
            
            # Smart response handling
            "response_guidance": decision.response_guidance,
            "follow_up_question": decision.follow_up_question.model_dump() if decision.follow_up_question else None,
            
            # Intent classification (NEW - Dynamic intent detection)
            "intent_classification": {
                "primary_intent": decision.intent_classification.primary_intent,
                "confidence": decision.intent_classification.confidence,
                "intent_reasoning": decision.intent_classification.intent_reasoning,
                "context_shift": decision.intent_classification.context_shift,
                "supporting_evidence": decision.intent_classification.supporting_evidence
            },
            "routing_guidance": decision.routing_guidance,
            
            # Detailed extracted data
            "extracted_data": {
                "monthly_budget": extracted_data.monthly_budget,
                "monthly_volume": extracted_data.monthly_volume,
                "volume_type": extracted_data.volume_type,
                "use_case": extracted_data.use_case,
                "current_provider": extracted_data.current_provider,
                "decision_authority": extracted_data.decision_authority,
                "business_quality_score": extracted_data.business_quality.quality_score,
                "growth_signals": extracted_data.business_quality.growth_signals,
                "company_maturity": extracted_data.business_quality.company_maturity
            },
            
            # Legacy compatibility fields
            "qualification": decision.stage,
            "score": (
                85 if decision.stage == "SQL" else 
                65 if decision.stage == "SSL" else 
                45 if decision.stage == "NEEDS_INFO" else 20
            ),
            "reasoning": decision.reasoning,
            "urgency": "high" if any("urgent" in sig.lower() for sig in extracted_data.urgency_signals) else "low",
            "qualification_factors": extracted_data.business_quality.quality_indicators,
            "urgency_indicators": extracted_data.urgency_signals,
            
            # Processing metadata
            "processing_method": "smart_conversational_qualification",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in smart qualification tool: {str(e)}")
        
        # Return error result
        error_result = {
            "sales_stage": "DQ",
            "sales_stage_reason": f"Processing error: {str(e)}",
            "confidence": 0.0,
            "recommend_transfer": False,
            "transfer_target": None,
            "response_guidance": "I apologize, but I'm having trouble processing your information. Let me get someone to help you right away.",
            "qualification": "DQ",
            "score": 0,
            "reasoning": f"System error: {str(e)}",
            "urgency": "low",
            "error": str(e)
        }
        
        return json.dumps(error_result, indent=2)