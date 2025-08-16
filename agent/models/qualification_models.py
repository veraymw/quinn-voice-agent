"""
Pydantic models for smart lead qualification system.

This module contains all the data models used for structured qualification
data extraction and decision making in the Quinn Voice Agent.
"""

from typing import Optional, Literal, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class BusinessQuality(BaseModel):
    """Assessment of business quality and potential"""
    
    quality_score: int = Field(
        0, ge=0, le=100,
        description="Overall business quality score (0-100)"
    )
    
    quality_indicators: List[str] = Field(
        default_factory=list,
        description="Positive quality indicators found"
    )
    
    growth_signals: List[str] = Field(
        default_factory=list,
        description="Growth and potential indicators"
    )
    
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Risk factors or concerns"
    )
    
    company_maturity: Literal["startup", "growth_stage", "established", "enterprise", "unknown"] = Field(
        "unknown",
        description="Company maturity assessment"
    )


class ExtractedQualificationData(BaseModel):
    """Core qualification data for lead assessment"""
    
    # Budget information
    monthly_budget: Optional[int] = Field(
        None,
        description="Monthly budget in USD (use highest figure if range)"
    )
    
    budget_context: Optional[str] = Field(
        None,
        description="Context around budget discussion"
    )
    
    # Volume information
    monthly_volume: Optional[int] = Field(
        None,
        description="Monthly volume (messages/calls/etc.)"
    )
    
    volume_type: Optional[str] = Field(
        None,
        description="Type of volume measurement"
    )
    
    # Additional qualifying metrics
    phone_numbers: Optional[int] = None
    countries: Optional[int] = None
    sim_cards: Optional[int] = None
    data_mb: Optional[int] = None
    voice_minutes: Optional[int] = None
    
    # Context factors
    use_case: Optional[str] = Field(
        None,
        description="Primary use case mentioned"
    )
    
    current_provider: Optional[str] = Field(
        None,
        description="Current communications provider"
    )
    
    urgency_signals: List[str] = Field(
        default_factory=list,
        description="Urgency indicators found"
    )
    
    # Authority and company context
    contact_title: Optional[str] = None
    decision_authority: Literal["high", "medium", "low", "unknown"] = "unknown"
    company_indicators: List[str] = Field(default_factory=list)
    
    # Business quality assessment
    business_quality: BusinessQuality = Field(default_factory=BusinessQuality)


class IntentClassification(BaseModel):
    """Dynamic intent classification for conversation context"""
    
    primary_intent: Literal["sales", "support", "other"] = Field(
        ...,
        description="Primary intent detected from conversation"
    )
    
    confidence: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Confidence in intent classification"
    )
    
    intent_reasoning: str = Field(
        ...,
        description="Why this intent was classified"
    )
    
    context_shift: bool = Field(
        False,
        description="Whether intent changed from previous classification"
    )
    
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence from conversation supporting this classification"
    )


class FollowUpQuestion(BaseModel):
    """Smart follow-up question when data is incomplete"""
    
    question: str = Field(
        ...,
        description="The follow-up question to ask"
    )
    
    reasoning: str = Field(
        ...,
        description="Why this question is important for qualification"
    )
    
    expected_info: str = Field(
        ...,
        description="What information this question aims to gather"
    )
    
    qualification_impact: Literal["high", "medium", "low"] = Field(
        ...,
        description="How much this info will impact qualification decision"
    )


class QualificationDecision(BaseModel):
    """Final qualification decision with intelligent routing and intent classification"""
    
    stage: Literal["SQL", "SSL", "DQ", "NEEDS_INFO"] = Field(
        ...,
        description="Qualification stage decision"
    )
    
    confidence: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Confidence in the decision"
    )
    
    reasoning: str = Field(
        ...,
        description="Clear reasoning for the decision"
    )
    
    # Intent classification (NEW - Dynamic intent detection)
    intent_classification: IntentClassification = Field(
        ...,
        description="Dynamic intent classification for this interaction"
    )
    
    # Transfer routing
    recommend_transfer: bool = Field(
        False,
        description="Whether to transfer the call"
    )
    
    transfer_target: Optional[Literal["AE", "BDR"]] = None
    
    # Follow-up handling
    follow_up_question: Optional[FollowUpQuestion] = Field(
        None,
        description="Smart follow-up if more info needed"
    )
    
    # Response guidance
    response_guidance: str = Field(
        ...,
        description="How Quinn should respond to the caller"
    )
    
    extracted_data: ExtractedQualificationData = Field(
        ...,
        description="All extracted qualification data"
    )
    
    # Routing guidance based on intent (NEW)
    routing_guidance: Optional[str] = Field(
        None,
        description="Specific routing guidance based on intent classification"
    )