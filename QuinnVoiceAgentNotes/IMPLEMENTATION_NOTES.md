# Quinn Voice Agent - Implementation Notes

## 🏗️ Architecture Overview

**Hybrid Agentic System**: Combines intelligent LangChain reasoning with fast direct webhook tools

```
Telnyx AI Assistant (Quinn) 
    ↓ (webhooks)
FastAPI Service (Replit)
    ├── Agentic Tools (LangChain React Agent)
    │   ├── Think Tool (internal reasoning)
    │   ├── Qualification Tool (lead scoring)
    │   ├── Transfer Tool (routing decisions)  
    │   └── Knowledge Tool (product info)
    └── Direct Tools (Always fast)
        ├── Salesforce Lookup (proven from quinnline)
        ├── Slack Notifications (call summaries)
        └── Google Sheets Logging (activity tracking)
```

## 📋 Telnyx Portal Configuration

### Add These Webhook Tools to Quinn:

**1. Salesforce Lookup** (Always first call)
- Name: "Salesforce Lookup"
- URL: `https://your-replit-url.com/tools/salesforce-lookup`
- Description: "Look up caller information in CRM"

**2. Agent Reasoning** (For complex decisions)
- Name: "Agent Reasoning" 
- URL: `https://your-replit-url.com/agent/think-and-act`
- Description: "Analyze conversation and make smart decisions"

**3. Slack Notification** (Call summaries)
- Name: "Slack Notification"
- URL: `https://your-replit-url.com/tools/slack-notify`
- Description: "Send call summary to team channel"

**4. Activity Logger** (Track everything)
- Name: "Activity Logger"
- URL: `https://your-replit-url.com/tools/log-activity`
- Description: "Log conversation activities"

## 🤖 Agent Decision Logic

### Qualification Scoring (0-100 points):
- **Company Size**: enterprise(20), corporation(15), startup(5)
- **Use Cases**: voice api(25), messaging api(20), contact center(18)
- **Volume Indicators**: million(20), thousands(15), high-volume(15)
- **Budget/Timeline**: budget approved(15), need asap(12), this quarter(10)
- **Existing Customer**: contact record(10)
- **Authority Level**: cto/ceo(10), director(8), manager(6)

### Transfer Routing Logic:
- **SQL (80+)**: Always transfer to AE (regardless of urgency)
- **SSL/DQ + High Urgency**: Transfer to BDR queue
- **SSL/DQ + Low Urgency**: Continue conversation with Quinn

### Urgency Detection:
Keywords: urgent, asap, immediately, emergency, down, broken, deadline, launch

## 🛠️ Tool Implementation Details

### LangChain Agent Tools:

**Think Tool**: Internal reasoning for complex sales situations
- Analyzes qualification level, urgency, interest signals
- Provides structured recommendations
- Used by other tools for decision support

**Qualification Tool**: Rule-based lead scoring
- Processes conversation context + caller info
- Returns score, qualification level, urgency assessment
- Factors in existing customer status, use cases, budget signals

**Transfer Tool**: Smart routing decisions
- Input: qualification level, urgency, reason
- Logic: SQL→AE, Urgent SSL/DQ→BDR, Others→Continue
- Can route to specific AE if found in Salesforce

**Knowledge Tool**: Product information and pricing
- Telnyx product knowledge base (Voice, Messaging, SIP, etc.)
- FAQ responses for common questions
- Competitive pricing information

### Direct Webhook Tools:

**Salesforce Lookup** (Copied from proven quinnline code):
- Parallel async search across Contacts & Leads
- Multiple phone field matching (Phone, MobilePhone, custom fields)
- Returns flattened data with AE information
- Cached phone normalization for performance

**Slack Notifications**:
- Formatted call summaries with qualification emojis
- Channel: `#quinn-voice-calls` (configurable)
- Urgent alerts with @here mentions
- Includes conversation ID for tracking

**Google Sheets Logger**:
- Two worksheets: Activity_Log & Call_Summaries
- Real-time activity logging for every tool use
- Call analytics and conversion tracking
- Async background logging for performance

## 🚀 Deployment Process

### 1. Replit Setup:
1. Import this repository to Replit
2. Set environment variables in Secrets:
   ```
   SALESFORCE_USERNAME=your_username
   SALESFORCE_PASSWORD=your_password
   SALESFORCE_SECURITY_TOKEN=your_token
   OPENAI_API_KEY=sk-your_key
   SLACK_BOT_TOKEN=xoxb-your_token
   GOOGLE_SHEETS_ID=your_sheet_id
   GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account"...}
   ```
3. Run project → Note your Replit URL

### 2. Google Sheets Setup:
1. Create new Google Sheets document
2. Create service account with Sheets API access
3. Share sheet with service account email
4. Copy sheet ID from URL

### 3. Slack Setup:
1. Create Slack app with bot token
2. Add to workspace and desired channel
3. Grant permissions: chat:write, channels:read

### 4. Telnyx Configuration:
- Add webhook tools to Quinn using URLs above
- Test each tool individually in Telnyx portal
- Configure tool descriptions and parameters

## 📊 Testing Strategy

### Individual Tool Testing:
```bash
# Test Salesforce lookup
curl https://your-replit-url.com/test/salesforce/+1234567890

# Test agent reasoning
curl -X POST https://your-replit-url.com/agent/think-and-act \
  -H "Content-Type: application/json" \
  -d '{"conversation_context": "Caller from Acme Corp asking about voice API pricing"}'

# Test Slack notification
curl -X POST https://your-replit-url.com/tools/slack-notify \
  -H "Content-Type: application/json" \
  -d '{"caller_name": "John Doe", "qualification": "SQL", "score": 85}'
```

### Conversation Flow Testing:
1. **Call Start**: Salesforce lookup should happen immediately
2. **Qualification**: Agent should score based on conversation context
3. **Transfer Decisions**: Should follow routing logic correctly
4. **Logging**: Every tool use should appear in Google Sheets
5. **Slack Summary**: Should receive formatted notification

## ⚡ Performance Optimizations

### Speed Considerations:
- **Salesforce Lookup**: Cached phone normalization, parallel queries
- **Agent Reasoning**: Limited to 5 iterations, gpt-4o-mini for speed
- **Background Logging**: Async operations don't block responses
- **Error Handling**: Graceful fallbacks, never break conversation

### Voice Call Best Practices:
- Sub-second response times for direct tools
- Agent reasoning happens async when possible
- Progressive qualification throughout conversation
- Smart tool selection based on context

## 📈 Monitoring & Analytics

### Google Sheets Tracking:
- **Activity Log**: Every tool use with timing and status
- **Call Summaries**: Complete conversation outcomes and scoring
- **Performance Metrics**: Tool response times and success rates

### Slack Notifications:
- Real-time call summaries with qualification status
- Urgent alerts for high-priority situations
- Team visibility into Quinn's performance

### Success Metrics:
- Qualification accuracy (SQL identification rate)
- Transfer success rate (qualified leads reaching AEs)
- Response time performance (sub-second for direct tools)
- Conversation completion rate

## 🔧 Customization Points

### Easy Modifications:
1. **Qualification Rules**: Update scoring in `qualification_tool.py`
2. **Transfer Targets**: Modify phone numbers in `transfer_tool.py`
3. **Knowledge Base**: Expand product info in `knowledge_tool.py`
4. **Slack Formatting**: Customize messages in `slack_notification.py`

### Adding New Tools:
1. Create tool function with `@tool` decorator
2. Add to `quinn_agent.py` tools list
3. Create FastAPI endpoint in `main.py`
4. Add to Telnyx portal configuration

## 🎯 Production Readiness

### Security:
- Environment variables for all secrets
- Input validation with Pydantic models
- Error handling without exposing internals

### Reliability:
- Graceful error fallbacks
- Background task error handling
- Connection retry logic for external APIs

### Scalability:
- Async operations throughout
- Efficient database queries
- Background logging to prevent blocking

This implementation provides a production-ready Quinn Voice Agent that combines intelligent reasoning with reliable webhook tools, optimized for voice call performance and comprehensive tracking.