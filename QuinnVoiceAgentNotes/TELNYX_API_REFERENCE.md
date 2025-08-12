# Telnyx Voice API & AI Assistant Reference

## Overview

This document provides comprehensive technical reference for Telnyx Voice API and AI Assistant capabilities, specifically tailored for Quinn Voice Agent testing and automation.

## Authentication

All API requests require authentication via Bearer token:

```bash
Authorization: Bearer YOUR_API_KEY
```

## Core API Endpoints

### 1. AI Assistant Management

#### Create AI Assistant
```http
POST /ai/assistants
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Quinn - Sales Qualification Agent",
  "model": "gpt-4o-mini",
  "instructions": "You are Quinn, an AI sales assistant for Telnyx...",
  "tools": [
    {
      "type": "webhook",
      "name": "Salesforce_Lookup",
      "url": "https://quinn-voice-agent-TelnyxViewer.replit.app/tools/salesforce-lookup",
      "method": "POST",
      "headers": {"Content-Type": "application/json"}
    }
  ],
  "voice": {
    "provider": "telnyx",
    "voice": "female_1",
    "speed": 1.0
  }
}
```

**Response:**
```json
{
  "id": "assistant_12345",
  "name": "Quinn - Sales Qualification Agent",
  "created_at": "2025-08-08T01:00:00Z",
  "status": "active"
}
```

#### Test Assistant Tool
```http
POST /ai/assistants/{assistant_id}/tools/{tool_id}/test
Content-Type: application/json
```

**Request Body:**
```json
{
  "arguments": {
    "phone_number": "+17249615289",
    "conversation_id": "test-123"
  },
  "dynamic_variables": {
    "telnyx_end_user_target": "+17249615289",
    "conversation_id": "test-123"
  }
}
```

**Response:**
```json
{
  "success": true,
  "status_code": 200,
  "content_type": "application/json",
  "response": "{\"success\":true,\"data\":{\"found\":true...}}",
  "request": {
    "url": "https://quinn-voice-agent-TelnyxViewer.replit.app/tools/salesforce-lookup",
    "method": "POST",
    "headers": {...},
    "body": {...}
  }
}
```

### 2. Voice Call Control

#### Start AI Assistant
```http
POST /calls/{call_control_id}/actions/ai_assistant_start
Content-Type: application/json
```

**Request Body:**
```json
{
  "assistant": {
    "id": "assistant_12345",
    "instructions": "Custom instructions for this call",
    "voice": {
      "provider": "telnyx",
      "voice": "female_1",
      "speed": 1.0
    }
  },
  "greeting": "Thanks for calling Telnyx! I'm Quinn. How can I help you today?",
  "interruption_threshold": 500,
  "transcription": {
    "model": "whisper"
  }
}
```

**Response:**
```json
{
  "result": "ok"
}
```

### 3. Webhook Events

#### Voice Webhook Payload Structure
```json
{
  "record_type": "event",
  "event_type": "call.conversation.started",
  "id": "webhook_12345",
  "occurred_at": "2025-08-08T01:00:00Z",
  "call_control_id": "call_abc123",
  "from": "+19296027097",
  "to": "+17249615289",
  "direction": "incoming",
  "state": "active",
  "payload": {
    "telnyx_end_user_target": "+19296027097",
    "telnyx_agent_target": "+17249615289",
    "assistant_id": "assistant_12345"
  }
}
```

#### Key Webhook Event Types
- `call.conversation.started` - AI conversation begins
- `call.conversation.ended` - AI conversation ends
- `call.conversation_insights.generated` - Post-call analytics
- `call.assistant.tool_called` - Tool execution events
- `call.assistant.tool_completed` - Tool completion events

## Quinn-Specific Integration

### Webhook Tool Endpoints

#### 1. Salesforce Lookup
```http
POST /tools/salesforce-lookup
```

**Expected Request:**
```json
{
  "phone_number": "{{telnyx_end_user_target}}",
  "conversation_id": "{{conversation_id}}"
}
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "found": true,
    "type": "lead",
    "record": {
      "Name": "Jesse Pechart",
      "Company": "Data Handler LLC",
      "Email": "jesse@datahandlerllc.com"
    }
  },
  "dynamic_variables": {
    "account_found": "true",
    "first_name": "Jesse",
    "last_name": "Pechart",
    "company": "Data Handler LLC",
    "email": "jesse@datahandlerllc.com"
  }
}
```

#### 2. Agent Reasoning
```http
POST /agent/think-and-act
```

**Expected Request:**
```json
{
  "conversation_context": "{{conversation_transcript}}",
  "specific_query": "score and routing recommendation",
  "caller_info": "{{caller_data}}",
  "conversation_id": "{{conversation_id}}"
}
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "decision": "Qualification Summary: Score: 65/100...",
    "reasoning": "Customer shows strong intent signals..."
  },
  "dynamic_variables": {
    "qualification_score": 65,
    "qualification_level": "SSL",
    "should_transfer": false,
    "urgency_level": "low"
  }
}
```

#### 3. Slack Notification
```http
POST /tools/slack-notify
```

**Expected Request:**
```json
{
  "caller_name": "{{first_name}} {{last_name}}",
  "qualification": "{{qualification_level}}",
  "score": "{{qualification_score}}",
  "outcome": "Continue conversation",
  "summary": "{{call_summary}}"
}
```

#### 4. Activity Logger
```http
POST /tools/log-activity
```

**Expected Request:**
```json
{
  "conversation_id": "{{conversation_id}}",
  "tool_used": "salesforce_lookup",
  "input_summary": "Phone lookup",
  "output_summary": "Found customer",
  "status": "success"
}
```

### Dynamic Variables Schema

Variables Quinn maintains across the conversation:

```json
{
  "account_found": "true|false",
  "first_name": "string",
  "last_name": "string", 
  "company": "string",
  "email": "string",
  "ae_name": "string",
  "qualification_score": "integer 0-100",
  "qualification_level": "SQL|SSL|DQ",
  "urgency_level": "high|low",
  "should_transfer": "boolean",
  "transfer_target": "AE|BDR|Human Agent"
}
```

## Rate Limits & Performance

- **Tool Testing API**: 100 requests/minute
- **Assistant Management**: 60 requests/minute  
- **Voice Control**: 300 requests/minute
- **Webhook Delivery**: 2-second timeout
- **Recommended Response Time**: <5s for direct tools, <15s for agent reasoning

## Error Codes

| Code | Description | Action |
|------|-------------|---------|
| 401 | Unauthorized | Check API key |
| 404 | Assistant/Tool not found | Verify IDs |
| 422 | Invalid request parameters | Check payload format |
| 429 | Rate limit exceeded | Implement backoff |
| 500 | Server error | Retry with exponential backoff |

## Best Practices

1. **Tool Testing**: Always test tools before production deployment
2. **Error Handling**: Implement graceful fallbacks for failed tools
3. **Dynamic Variables**: Use consistent naming across tools
4. **Webhook Security**: Validate webhook signatures in production
5. **Performance**: Keep tool responses under recommended timeouts
6. **Monitoring**: Track success rates and response times

## Testing Endpoints

All Quinn webhook tools are available at:
- Base URL: `https://quinn-voice-agent-TelnyxViewer.replit.app`
- Health Check: `GET /`
- Documentation: Built-in FastAPI docs at `/docs`

This reference enables comprehensive testing and integration with Quinn Voice Agent through Telnyx's platform.