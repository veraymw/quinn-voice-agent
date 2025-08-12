"""
Smart conversational lead qualification tool with AI-driven decision making.

This tool uses Instructor for structured data extraction and includes intelligent 
follow-up question generation when qualification data is incomplete or unclear.
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
    QualificationDecision
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
        
        self.client = instructor.from_openai(OpenAI(api_key=api_key))
        
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
        5. Note confidence levels - mark as "low" if information is vague or assumed
        
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
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ExtractedQualificationData,
                max_retries=2
            )
            
            logger.info(f"Extracted data: Budget=${extracted_data.monthly_budget}, Volume={extracted_data.monthly_volume}, Quality={extracted_data.business_quality.quality_score}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error in data extraction: {str(e)}")
            return ExtractedQualificationData()
    
    def make_qualification_decision(self, data: ExtractedQualificationData, 
                                  conversation_context: str) -> QualificationDecision:
        """Make intelligent qualification decision with follow-up handling"""
        
        system_prompt = f"""
        You are a smart Telnyx sales qualification agent. Make qualification decisions 
        using these precise rules and determine if follow-up questions are needed.

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
           - AI voice interest (strategic priority)
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
        (roughly 400K+ SMS messages or equivalent usage). If you're below that, 
        our self-service platform is the best way to get started immediately."
        
        For AI voice prospects: Prioritize as SQL even with lower volumes.
        For high-quality businesses: Ask smart follow-up questions to qualify properly.
        
        THRESHOLDS: {json.dumps(self.sql_thresholds, indent=2)}
        """
        
        user_prompt = f"""
        EXTRACTED DATA:
        {data.model_dump_json(indent=2)}
        
        CONVERSATION CONTEXT:
        {conversation_context}
        
        Make the qualification decision. If you need more information for a proper 
        decision (especially for promising businesses), generate a smart follow-up question
        that helps determine spend/usage levels or business quality.
        
        Consider:
        1. Does this meet clear SQL/SSL/DQ criteria?
        2. Is this a high-quality business that deserves more discovery?
        3. Would a follow-up question significantly improve qualification accuracy?
        4. What's the best way to handle this prospect?
        """
        
        try:
            decision = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=QualificationDecision,
                max_retries=2
            )
            
            # Set transfer routing based on stage
            if decision.stage == "SQL":
                decision.recommend_transfer = True
                decision.transfer_target = "AE"
            elif decision.stage == "SSL" and any("urgent" in sig.lower() for sig in data.urgency_signals):
                decision.recommend_transfer = True
                decision.transfer_target = "BDR"
            
            logger.info(f"Qualification decision: {decision.stage} - {decision.reasoning}")
            return decision
            
        except Exception as e:
            logger.error(f"Error in qualification decision: {str(e)}")
            return QualificationDecision(
                stage="DQ",
                confidence=0.0,
                reasoning=f"Processing error: {str(e)}",
                response_guidance="I apologize, but I'm having trouble processing your information. Let me connect you with someone who can help.",
                extracted_data=data
            )


# Initialize the smart qualification engine
smart_qualification_engine = SmartQualificationEngine()


@tool  
def qualification_tool(conversation_context: str, caller_info: str = "{}") -> str:
    """
    Qualify a lead based on conversation context and caller information.
    Returns qualification score, level, and routing recommendation.
    
    Uses smart AI-driven qualification with Instructor for structured data extraction
    and includes intelligent follow-up question generation when data is incomplete.
    
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
        
        logger.info(f"Processing smart qualification for conversation length: {len(conversation_context)}")
        
        # Extract comprehensive qualification data
        extracted_data = smart_qualification_engine.extract_qualification_data(
            conversation_context, 
            caller_data
        )
        
        # Make intelligent qualification decision
        decision = smart_qualification_engine.make_qualification_decision(
            extracted_data,
            conversation_context
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
            
            # Detailed extracted data
            "extracted_data": {
                "monthly_budget": extracted_data.monthly_budget,
                "budget_confidence": extracted_data.budget_confidence,
                "monthly_volume": extracted_data.monthly_volume,
                "volume_type": extracted_data.volume_type,
                "volume_confidence": extracted_data.volume_confidence,
                "use_case": extracted_data.use_case,
                "ai_voice_interest": extracted_data.ai_voice_interest,
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