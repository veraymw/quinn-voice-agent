"""
Data models for Quinn Voice Agent.

This module contains all Pydantic models used for request/response handling
in the Quinn Voice Agent system, including Telnyx webhook integration.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union

# Request Models for Telnyx Webhook Tools (Simple Parameter Mode)

class SalesforceRequest(BaseModel):
    """
    Request model for Salesforce lookup tool.
    
    This tool is called immediately after greeting to check if the caller
    is an existing customer in the CRM system.
    """
    phone_number: str = Field(
        ..., 
        description="Phone number to lookup in Salesforce from {{telnyx_end_user_target}}"
    )
    call_control_id: Optional[str] = Field(
        None, 
        description="Call control identifier from Telnyx for tracking and logging"
    )


class AgentRequest(BaseModel):
    """
    Request model for Agent Reasoning tool.
    
    This is the central brain that handles knowledge queries, qualification
    scoring, and routing decisions using the LangChain agent system.
    
    Now includes Telnyx metadata.
    """
    conversation_context: str = Field(
        ..., 
        description="Current conversation transcript and context"
    )
    specific_query: str = Field(
        ..., 
        description="Type of analysis needed (e.g., 'score and routing recommendation', 'product pricing overview')"
    )
    caller_info: Optional[Union[str, Dict[str, Any]]] = Field(
        None, 
        description="Salesforce lookup result - can be string or dict format"
    )
    
    # NEW: Telnyx metadata for background processing
    call_control_id: Optional[str] = Field(
        None,
        description="Primary identifier for Telnyx Call Control API operations"
    )
    assistant_id: Optional[str] = Field(
        None,
        description="Telnyx AI assistant identifier"
    )
    call_session_id: Optional[str] = Field(
        None,
        description="Telnyx call session identifier"
    )
    call_leg_id: Optional[str] = Field(
        None,
        description="Telnyx call leg identifier"
    )
    to: Optional[str] = Field(
        None,
        description="Target phone number"
    )
    from_number: Optional[str] = Field(
        None,
        alias="from",
        description="Caller phone number (from is a Python keyword)"
    )
    telnyx_end_user_target: Optional[str] = Field(
        None,
        description="Caller's phone number (Telnyx format)"
    )
    telnyx_agent_target: Optional[str] = Field(
        None,
        description="Agent's phone number (Telnyx format)"
    )
    assistant_version_id: Optional[str] = Field(
        None,
        description="Version of the assistant being used"
    )
    
    def get_call_control_id(self) -> Optional[str]:
        """Get the primary identifier for sending results back to the call"""
        return self.call_control_id
    
    def get_caller_phone(self) -> Optional[str]:
        """Get the caller's phone number from available fields"""
        return self.telnyx_end_user_target or self.from_number
    
    def has_required_metadata(self) -> bool:
        """Check if we have the minimum metadata needed for background processing"""
        return bool(self.call_control_id)


class SlackNotificationRequest(BaseModel):
    """
    Request model for Slack notification tool.
    
    Sends formatted call summaries to the team channel for visibility
    and follow-up tracking.
    """
    caller_name: str = Field(
        ..., 
        description="Name of the caller from {{caller_name}} variable"
    )
    caller_company: Optional[str] = Field(
        None, 
        description="Company name from {{caller_company}} variable"
    )
    qualification: str = Field(
        ..., 
        description="Qualification level: SQL, SSL, or DQ"
    )
    score: int = Field(
        ..., 
        description="Qualification score 0-100"
    )
    urgency: str = Field(
        ..., 
        description="Urgency level: high or low"
    )
    duration: Optional[str] = Field(
        None, 
        description="Call duration from {{call_duration}}"
    )
    outcome: str = Field(
        ..., 
        description="Call outcome: Completed, Transferred, Follow-up"
    )
    summary: str = Field(
        ..., 
        description="Brief call summary"
    )
    transfer_target: Optional[str] = Field(
        None, 
        description="Transfer destination: AE, BDR, or null"
    )
    conversation_id: Optional[str] = Field(
        None, 
        description="Unique conversation identifier"
    )


class ActivityLogRequest(BaseModel):
    """
    Request model for Activity Logger tool.
    
    Logs all tool usage and conversation events to Google Sheets
    for analytics and performance tracking.
    """
    conversation_id: str = Field(
        ..., 
        description="Unique conversation identifier"
    )
    tool_used: str = Field(
        ..., 
        description="Name of the tool that was executed"
    )
    input_summary: str = Field(
        ..., 
        description="Brief description of tool input"
    )
    output_summary: str = Field(
        ..., 
        description="Brief description of tool output"
    )
    duration_ms: Optional[int] = Field(
        0, 
        description="Tool execution time in milliseconds"
    )
    status: str = Field(
        ..., 
        description="Execution status: success, error, timeout"
    )
    error: Optional[str] = Field(
        None, 
        description="Error message if status is error"
    )
    caller_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="Caller information object"
    )
    notes: Optional[str] = Field(
        None, 
        description="Additional notes or context"
    )


class ResponseValidationRequest(BaseModel):
    """
    Request model for Response Validation tool.
    
    Validates Quinn's intended responses against capability boundaries
    to prevent overcommitment and ensure appropriate responses.
    """
    intended_response: str = Field(
        ..., 
        description="Quinn's intended response to validate"
    )
    conversation_context: Optional[str] = Field(
        None, 
        description="Current conversation context for validation"
    )
    conversation_id: Optional[str] = Field(
        None, 
        description="Unique conversation identifier"
    )


# Response Models

class TelnyxToolResponse(BaseModel):
    """
    Standardized response model for all Telnyx webhook tools.
    
    This format ensures Quinn can properly process tool results and
    maintain dynamic variables across the conversation.
    """
    success: bool = Field(
        ..., 
        description="Whether the tool execution was successful"
    )
    data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Tool-specific response data"
    )
    dynamic_variables: Optional[Dict[str, Any]] = Field(
        None, 
        description="Variables for Telnyx to remember (e.g., caller_name, qualification_score)"
    )
    error: Optional[str] = Field(
        None, 
        description="Error message if success is False"
    )
    meta: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata (e.g., execution_time_ms)"
    )


# Dynamic Variables Schema (for documentation)

class DynamicVariables(BaseModel):
    """
    Schema for dynamic variables that Quinn remembers across tools.
    
    These variables are set by tool responses and used throughout
    the conversation for personalization and routing decisions.
    """
    # From Salesforce Lookup
    caller_name: Optional[str] = Field(None, description="Caller's full name")
    caller_company: Optional[str] = Field(None, description="Caller's company")
    caller_type: Optional[str] = Field(None, description="contact, lead, or unknown")
    ae_name: Optional[str] = Field(None, description="Account Executive name")
    ae_phone: Optional[str] = Field(None, description="AE direct phone for transfers")
    
    # From Agent Reasoning (Qualification)
    qualification_score: Optional[int] = Field(None, description="Score 0-100")
    qualification_level: Optional[str] = Field(None, description="SQL, SSL, or DQ")
    urgency_level: Optional[str] = Field(None, description="high or low")
    should_transfer: Optional[bool] = Field(None, description="Whether to transfer call")
    transfer_target: Optional[str] = Field(None, description="AE, BDR, or Human Agent")
    
    # Call Tracking
    call_duration: Optional[str] = Field(None, description="Total call duration")
    call_outcome: Optional[str] = Field(None, description="Final call outcome")
    conversation_summary: Optional[str] = Field(None, description="Brief call summary")


# Export all models for easy importing
__all__ = [
    "SalesforceRequest",
    "AgentRequest", 
    "SlackNotificationRequest",
    "ActivityLogRequest",
    "ResponseValidationRequest",
    "TelnyxToolResponse",
    "DynamicVariables"
]