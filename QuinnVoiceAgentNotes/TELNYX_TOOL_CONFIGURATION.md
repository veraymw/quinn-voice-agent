# Telnyx Portal Tool Configuration Guide

This guide provides the exact configurations needed for each webhook tool in the Telnyx AI Assistant portal using **Simple Parameter Mode**.

## Prerequisites

1. **Deploy your backend** to Replit and note your URL (e.g., `https://your-project.replit.app`)
2. **Set environment variables** in Replit Secrets
3. **Test your endpoints** are accessible

## Tool Configuration Overview

Your updated backend now:
- ✅ Uses Pydantic models for type safety and validation
- ✅ Returns `TelnyxToolResponse` format with dynamic variables
- ✅ Properly extracts qualification data for Quinn to remember
- ✅ Handles both simple parameters and complex objects

## 1. Salesforce Lookup Tool

**Purpose:** Look up caller information in CRM immediately after greeting

### Configuration:
- **Tool Name:** `salesforce_lookup`
- **URL:** `https://your-replit-url.com/tools/salesforce-lookup`
- **Method:** POST
- **Headers:** `Content-Type: application/json`

### Parameters:

| Name | Type | Required | Value | Description |
|------|------|----------|--------|-------------|
| `phone_number` | string | ✅ Yes | `{{telnyx_end_user_target}}` | The caller's phone number |
| `conversation_id` | string | ❌ No | `{{conversation_id}}` | Unique conversation identifier |

### Expected Dynamic Variables Set:
- `{{caller_name}}` - Name from Salesforce
- `{{caller_company}}` - Company name
- `{{caller_type}}` - "contact", "lead", or "unknown"
- `{{ae_name}}` - Account Executive name
- `{{ae_phone}}` - AE direct phone for transfers

### When Quinn Calls This:
```
After greeting: "Do you already have a Telnyx account?"
If YES: "One moment while I pull up your record." → Call this tool
```

---

## 2. Agent Reasoning Tool

**Purpose:** Central brain for knowledge, qualification, and routing decisions

### Configuration:
- **Tool Name:** `agent_reasoning`
- **URL:** `https://your-replit-url.com/agent/think-and-act`
- **Method:** POST
- **Headers:** `Content-Type: application/json`

### Parameters:

| Name | Type | Required | Value | Description |
|------|------|----------|--------|-------------|
| `conversation_context` | string | ✅ Yes | `{{conversation_history}}` | Current conversation transcript |
| `specific_query` | string | ✅ Yes | *Set by Quinn* | Analysis type needed |
| `caller_info` | object | ❌ No | `{{salesforce_result}}` | Salesforce lookup result |
| `conversation_id` | string | ❌ No | `{{conversation_id}}` | Conversation identifier |

### Example `specific_query` Values:
```
"provide Voice API pricing overview for US and EU with key features"
"score and routing recommendation"
"compare SIP trunking vs Voice API for contact centers"
"next best action for urgent porting issue"
```

### Expected Dynamic Variables Set:
- `{{qualification_score}}` - Score 0-100
- `{{qualification_level}}` - "SQL", "SSL", or "DQ"
- `{{urgency_level}}` - "high" or "low"
- `{{should_transfer}}` - true/false
- `{{transfer_target}}` - "AE", "BDR", or "Human Agent"

### When Quinn Calls This:
```
- When needing product information or pricing
- When ready to score and route the lead
- For complex decision-making scenarios
```

---

## 3. Slack Notification Tool

**Purpose:** Send call summaries to team channel

### Configuration:
- **Tool Name:** `slack_notification`
- **URL:** `https://your-replit-url.com/tools/slack-notify`
- **Method:** POST
- **Headers:** `Content-Type: application/json`

### Parameters:

| Name | Type | Required | Value | Description |
|------|------|----------|--------|-------------|
| `caller_name` | string | ✅ Yes | `{{caller_name}}` | Caller's name |
| `caller_company` | string | ❌ No | `{{caller_company}}` | Company name |
| `qualification` | string | ✅ Yes | `{{qualification_level}}` | SQL, SSL, or DQ |
| `score` | number | ✅ Yes | `{{qualification_score}}` | Score 0-100 |
| `urgency` | string | ✅ Yes | `{{urgency_level}}` | high or low |
| `duration` | string | ❌ No | `{{call_duration}}` | Call duration |
| `outcome` | string | ✅ Yes | *Set by Quinn* | Completed/Transferred/Follow-up |
| `summary` | string | ✅ Yes | *Set by Quinn* | Brief call summary |
| `transfer_target` | string | ❌ No | `{{transfer_target}}` | AE/BDR/null |
| `conversation_id` | string | ❌ No | `{{conversation_id}}` | Conversation ID |

### When Quinn Calls This:
```
- End of call (always)
- High urgency situations requiring team attention
```

---

## 4. Activity Logger Tool

**Purpose:** Log all tool usage to Google Sheets for analytics

### Configuration:
- **Tool Name:** `activity_logger`
- **URL:** `https://your-replit-url.com/tools/log-activity`
- **Method:** POST
- **Headers:** `Content-Type: application/json`

### Parameters:

| Name | Type | Required | Value | Description |
|------|------|----------|--------|-------------|
| `conversation_id` | string | ✅ Yes | `{{conversation_id}}` | Conversation identifier |
| `tool_used` | string | ✅ Yes | *Set by Quinn* | Tool name executed |
| `input_summary` | string | ✅ Yes | *Set by Quinn* | Brief input description |
| `output_summary` | string | ✅ Yes | *Set by Quinn* | Brief output description |
| `duration_ms` | number | ❌ No | *Set by Quinn* | Execution time |
| `status` | string | ✅ Yes | *Set by Quinn* | success/error/timeout |
| `error` | string | ❌ No | *Set by Quinn* | Error message if any |
| `caller_info` | object | ❌ No | `{{caller_info}}` | Caller information |
| `notes` | string | ❌ No | *Set by Quinn* | Additional context |

### When Quinn Calls This:
```
- After each tool execution (best effort)
- End of call summary
```

---

## Backend Response Format

Your updated backend returns this structure for all tools:

```json
{
  "success": true,
  "data": {
    // Tool-specific response data
  },
  "dynamic_variables": {
    // Variables Quinn should remember
    "caller_name": "John Smith",
    "qualification_score": 85,
    "qualification_level": "SQL",
    "urgency_level": "high",
    "should_transfer": true,
    "transfer_target": "AE"
  },
  "meta": {
    "execution_time_ms": 450
  }
}
```

## Updated Prompt Variables

With these tools, Quinn can now use these variables throughout the conversation:

### From Salesforce Lookup:
- `{{caller_name}}` - "John Smith"
- `{{caller_company}}` - "Acme Corp"
- `{{caller_type}}` - "contact"/"lead"/"unknown"
- `{{ae_name}}` - "Sarah Johnson"
- `{{ae_phone}}` - "+14155551234"

### From Agent Reasoning:
- `{{qualification_score}}` - 85
- `{{qualification_level}}` - "SQL"
- `{{urgency_level}}` - "high"
- `{{should_transfer}}` - true
- `{{transfer_target}}` - "AE"

### System Variables:
- `{{conversation_id}}` - Unique conversation ID
- `{{telnyx_end_user_target}}` - Caller's phone
- `{{call_duration}}` - Call duration
- `{{conversation_history}}` - Recent transcript

## Tool Orchestration Flow

```
1. Call Start → Salesforce Lookup
   ↓ Sets: caller_name, caller_company, ae_phone, etc.

2. Problem Solving → Agent Reasoning (as needed)
   ↓ Sets: qualification_score, qualification_level, etc.

3. Routing Decision → Transfer Logic using variables
   ↓ If {{should_transfer}} = true → Transfer to {{ae_phone}} or AE queue

4. Call End → Slack Notification + Activity Logger
   ↓ Uses all collected variables for comprehensive summary
```

## Testing Your Configuration

### 1. Test Individual Tools:
```bash
# Test Salesforce Lookup
curl -X POST https://your-replit-url.com/tools/salesforce-lookup \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+14155550123"}'

# Test Agent Reasoning
curl -X POST https://your-replit-url.com/agent/think-and-act \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_context": "Caller from Acme Corp asking about 500k SMS/month",
    "specific_query": "score and routing recommendation"
  }'
```

### 2. Verify Dynamic Variables:
- Check that responses include `dynamic_variables` object
- Ensure variable names match what Quinn expects
- Test variable persistence across multiple tool calls

### 3. Full Call Flow Test:
1. Place test call to Quinn
2. Verify Salesforce lookup happens immediately
3. Check that qualification variables are set correctly
4. Confirm transfer routing uses the variables
5. Validate Slack notification contains all data

## Troubleshooting

### Common Issues:

1. **Variables not persisting:** Check `dynamic_variables` in response format
2. **Tool timeouts:** Ensure endpoints respond in <3 seconds
3. **Missing data:** Verify Pydantic model validation is passing
4. **Transfer not working:** Check `{{ae_phone}}` variable is set correctly

### Debug Mode:
Check your Replit logs to see:
- Incoming requests from Telnyx
- Dynamic variables being set
- Tool execution times
- Any parsing errors

Your backend is now ready for the Simple Parameter Mode with full variable support!