from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
import asyncio
from datetime import datetime
import json

# Import our components
from config import settings
from salesforce_lookup import SalesforceLookup
from agent.quinn_agent import QuinnAgent
from direct_tools.slack_notification import SlackNotificationTool
from direct_tools.sheets_logger import SheetsLogger

# Import data models
from core.data import (
    SalesforceRequest,
    AgentRequest,
    SlackNotificationRequest,
    ActivityLogRequest,
    TelnyxToolResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Quinn Voice Agent",
    description="AI-powered sales agent with LangChain reasoning and direct tools",
    version="1.0.0"
)

# Global instances (initialized on startup)
salesforce_client = None
quinn_agent = None
slack_tool = None
sheets_logger = None



@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup"""
    global salesforce_client, quinn_agent, slack_tool, sheets_logger
    
    try:
        # Initialize Salesforce client
        salesforce_client = SalesforceLookup(
            username=settings.salesforce_username,
            password=settings.salesforce_password,
            security_token=settings.salesforce_security_token,
            domain=settings.salesforce_domain
        )
        
        # Initialize Quinn Agent
        quinn_agent = QuinnAgent(
            openai_api_key=settings.openai_api_key,
            model=settings.openai_model
        )
        
        # Initialize Slack tool
        slack_tool = SlackNotificationTool(
            bot_token=settings.slack_bot_token,
            default_channel=settings.slack_channel_id
        )
        
        # Initialize Sheets logger
        sheets_logger = SheetsLogger(
            service_account_json=settings.google_service_account_json,
            spreadsheet_id=settings.google_sheets_id
        )
        
        logger.info("All Quinn components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        raise


# Health check endpoint
@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Quinn Voice Agent",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# Salesforce lookup endpoint (Direct tool)
@app.post("/tools/salesforce-lookup", response_model=TelnyxToolResponse)
async def salesforce_lookup_endpoint(
    request: SalesforceRequest,
    background_tasks: BackgroundTasks
) -> TelnyxToolResponse:
    """Look up caller information in Salesforce"""
    start_time = datetime.now()
    
    try:
        if not salesforce_client:
            return TelnyxToolResponse(
                success=False,
                error="Salesforce client not initialized",
                dynamic_variables={"caller_type": "unknown"}
            )
        
        result = await salesforce_client.lookup_phone_number(request.phone_number)
        
        # Extract dynamic variables for Telnyx (match expected format)
        record = result.get("record", {}) if result.get("found") else {}
        name_parts = record.get("Name", "").split(" ", 1) if record.get("Name") else ["", ""]
        
        dynamic_variables = {
            "account_found": "true" if result.get("found") else "false",
            "first_name": name_parts[0] if len(name_parts) > 0 else "",
            "last_name": name_parts[1] if len(name_parts) > 1 else "",
            "email": record.get("Email", ""),
            "company": record.get("Company", ""),
            "ae_phone": record.get("AE_Phone", ""),
            "ae_name": record.get("AE_Name", "")
        }
        
        # Log activity in background
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        background_tasks.add_task(
            log_activity_background,
            conversation_id=request.conversation_id or "unknown",
            tool_used="salesforce_lookup",
            input_summary=f"Phone: {request.phone_number}",
            output_summary=f"Found: {result.get('found', False)} - {dynamic_variables['first_name']} {dynamic_variables['last_name']}",
            duration_ms=duration_ms,
            caller_info=result
        )
        
        return TelnyxToolResponse(
            success=True,
            data=result,
            dynamic_variables=dynamic_variables,
            meta={"execution_time_ms": duration_ms}
        )
        
    except Exception as e:
        logger.error(f"Error in Salesforce lookup: {str(e)}")
        
        # Log error in background
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        background_tasks.add_task(
            log_activity_background,
            conversation_id=request.conversation_id or "unknown",
            tool_used="salesforce_lookup",
            input_summary=f"Phone: {request.phone_number}",
            output_summary="Error occurred",
            duration_ms=duration_ms,
            status="error",
            error=str(e)
        )
        
        return TelnyxToolResponse(
            success=False,
            error=str(e),
            dynamic_variables={"caller_type": "unknown"},
            meta={"execution_time_ms": duration_ms}
        )


# Agent reasoning endpoint (Agentic tool)
@app.post("/agent/think-and-act", response_model=TelnyxToolResponse)
async def agent_think_and_act_endpoint(
    request: AgentRequest,
    background_tasks: BackgroundTasks
) -> TelnyxToolResponse:
    """LangChain agent reasoning and decision making"""
    start_time = datetime.now()
    
    try:
        if not quinn_agent:
            return TelnyxToolResponse(
                success=False,
                error="Quinn agent not initialized"
            )
        
        result = await quinn_agent.think_and_act(
            conversation_context=request.conversation_context,
            caller_info=request.caller_info,
            specific_query=request.specific_query
        )
        
        # Extract dynamic variables from agent reasoning
        dynamic_variables = {}
        
        # Parse qualification results using a more robust approach
        try:
            # Check if qualification tools were used
            actions_taken = result.get("actions_taken", [])
            decision_text = result.get("decision", "")
            
            if "qualification_tool" in actions_taken or "score" in request.specific_query.lower():
                # Try to extract structured qualification data
                
                # Look for score patterns (e.g., "Score: 85", "score of 72")
                import re
                score_match = re.search(r'score:?\s*(\d+)', decision_text, re.IGNORECASE)
                if score_match:
                    score = int(score_match.group(1))
                    dynamic_variables["qualification_score"] = score
                    
                    # Determine qualification level based on score
                    if score >= 80:
                        dynamic_variables["qualification_level"] = "SQL"
                    elif score >= 50:
                        dynamic_variables["qualification_level"] = "SSL"
                    else:
                        dynamic_variables["qualification_level"] = "DQ"
                
                # Look for explicit qualification mentions
                if "SQL" in decision_text:
                    dynamic_variables["qualification_level"] = "SQL"
                    if "qualification_score" not in dynamic_variables:
                        dynamic_variables["qualification_score"] = 85
                elif "SSL" in decision_text:
                    dynamic_variables["qualification_level"] = "SSL"
                    if "qualification_score" not in dynamic_variables:
                        dynamic_variables["qualification_score"] = 65
                elif "DQ" in decision_text or "disqualified" in decision_text.lower():
                    dynamic_variables["qualification_level"] = "DQ"
                    if "qualification_score" not in dynamic_variables:
                        dynamic_variables["qualification_score"] = 25
                
                # Check urgency
                urgency_keywords = ["urgent", "asap", "immediately", "emergency", "high urgency"]
                if any(keyword in decision_text.lower() for keyword in urgency_keywords):
                    dynamic_variables["urgency_level"] = "high"
                else:
                    dynamic_variables["urgency_level"] = "low"
                
                # Check transfer recommendations
                if "transfer" in decision_text.lower() or "route" in decision_text.lower():
                    dynamic_variables["should_transfer"] = True
                    if "account executive" in decision_text.lower() or "AE" in decision_text:
                        dynamic_variables["transfer_target"] = "AE"
                    elif "BDR" in decision_text or "business development" in decision_text.lower():
                        dynamic_variables["transfer_target"] = "BDR"
                    else:
                        dynamic_variables["transfer_target"] = "Human Agent"
                else:
                    dynamic_variables["should_transfer"] = False
                    
        except Exception as parse_error:
            logger.warning(f"Could not parse qualification data: {parse_error}")
        
        # Log activity in background
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        background_tasks.add_task(
            log_activity_background,
            conversation_id=request.conversation_id or "unknown",
            tool_used="agent_reasoning",
            input_summary=f"Query: {request.specific_query} | Context: {len(request.conversation_context)} chars",
            output_summary=f"Decision: {result.get('decision', 'Unknown')[:100]}",
            duration_ms=duration_ms,
            caller_info=request.caller_info
        )
        
        return TelnyxToolResponse(
            success=True,
            data=result,
            dynamic_variables=dynamic_variables,
            meta={"execution_time_ms": duration_ms}
        )
        
    except Exception as e:
        logger.error(f"Error in agent reasoning: {str(e)}")
        
        # Log error in background
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        background_tasks.add_task(
            log_activity_background,
            conversation_id=request.conversation_id or "unknown",
            tool_used="agent_reasoning",
            input_summary=f"Query: {request.specific_query}",
            output_summary="Error occurred",
            duration_ms=duration_ms,
            status="error",
            error=str(e)
        )
        
        return TelnyxToolResponse(
            success=False,
            error=str(e),
            meta={"execution_time_ms": duration_ms}
        )


# Slack notification endpoint (Direct tool)
@app.post("/tools/slack-notify", response_model=TelnyxToolResponse)
async def slack_notification_endpoint(
    request: SlackNotificationRequest,
    background_tasks: BackgroundTasks
) -> TelnyxToolResponse:
    """Send call summary to Slack"""
    start_time = datetime.now()
    
    try:
        if not slack_tool:
            return TelnyxToolResponse(
                success=False,
                error="Slack tool not initialized"
            )
        
        result = await slack_tool.send_call_summary(
            caller_name=request.caller_name,
            caller_company=request.caller_company,
            qualification=request.qualification,
            score=request.score,
            urgency=request.urgency,
            duration=request.duration,
            outcome=request.outcome,
            summary=request.summary,
            transfer_target=request.transfer_target,
            conversation_id=request.conversation_id
        )
        
        # Log activity in background
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        background_tasks.add_task(
            log_activity_background,
            conversation_id=request.conversation_id or "unknown",
            tool_used="slack_notification",
            input_summary=f"Caller: {request.caller_name} ({request.qualification})",
            output_summary=f"Sent: {result.get('success', False)}",
            duration_ms=duration_ms
        )
        
        return TelnyxToolResponse(
            success=result.get("success", False),
            data=result,
            meta={"execution_time_ms": duration_ms}
        )
        
    except Exception as e:
        logger.error(f"Error sending Slack notification: {str(e)}")
        
        # Log error in background
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        background_tasks.add_task(
            log_activity_background,
            conversation_id=request.conversation_id or "unknown",
            tool_used="slack_notification",
            input_summary=f"Caller: {request.caller_name}",
            output_summary="Error occurred",
            duration_ms=duration_ms,
            status="error",
            error=str(e)
        )
        
        return TelnyxToolResponse(
            success=False,
            error=str(e),
            meta={"execution_time_ms": duration_ms}
        )


# Activity logging endpoint (Direct tool)
@app.post("/tools/log-activity", response_model=TelnyxToolResponse)
async def log_activity_endpoint(request: ActivityLogRequest) -> TelnyxToolResponse:
    """Log activity to Google Sheets"""
    try:
        if not sheets_logger:
            return TelnyxToolResponse(
                success=False,
                error="Sheets logger not initialized"
            )
        
        result = await sheets_logger.log_activity(
            conversation_id=request.conversation_id,
            tool_used=request.tool_used,
            input_summary=request.input_summary,
            output_summary=request.output_summary,
            duration_ms=request.duration_ms,
            status=request.status,
            error=request.error,
            caller_info=request.caller_info,
            notes=request.notes
        )
        
        return TelnyxToolResponse(
            success=result.get("success", False),
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")
        return TelnyxToolResponse(
            success=False,
            error=str(e)
        )


# Test endpoints for development
@app.get("/test/salesforce/{phone}")
async def test_salesforce_lookup(phone: str):
    """Test Salesforce lookup"""
    if not salesforce_client:
        raise HTTPException(status_code=500, detail="Salesforce client not initialized")
    
    return await salesforce_client.lookup_phone_number(phone)


@app.get("/test/sheets-stats")
async def test_sheets_stats():
    """Test Google Sheets statistics"""
    if not sheets_logger:
        raise HTTPException(status_code=500, detail="Sheets logger not initialized")
    
    return await sheets_logger.get_call_stats(days=7)


# Background task for logging
async def log_activity_background(
    conversation_id: str,
    tool_used: str,
    input_summary: str,
    output_summary: str,
    duration_ms: int = 0,
    status: str = "success",
    error: str = None,
    caller_info: Dict[str, Any] = None,
    notes: str = None
):
    """Background task to log activity without blocking main response"""
    try:
        if sheets_logger:
            await sheets_logger.log_activity(
                conversation_id=conversation_id,
                tool_used=tool_used,
                input_summary=input_summary,
                output_summary=output_summary,
                duration_ms=duration_ms,
                status=status,
                error=error,
                caller_info=caller_info,
                notes=notes
            )
    except Exception as e:
        logger.error(f"Background logging failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )