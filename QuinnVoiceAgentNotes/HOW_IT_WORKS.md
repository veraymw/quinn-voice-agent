# How Quinn Voice Agent Works

## Project Architecture Overview

Quinn Voice Agent is a **hybrid intelligent system** that combines:
- **Telnyx Voice Platform** (handles the actual phone call)
- **FastAPI Backend** (your intelligent decision-making layer)
- **LangChain Agent** (internal reasoning and tool orchestration)
- **Direct Tools** (fast external integrations)

## System Architecture Diagram

```
Incoming Call Flow:

Caller dials Telnyx number
    ↓
Telnyx Voice Platform (Quinn AI Agent)
    ↓
Webhook calls to FastAPI Backend (Replit)
    ↓
┌─────────────────────────────────────────┐
│ FastAPI Server (main.py)                │
│                                         │
│ ┌─────────────┐  ┌────────────────────┐ │
│ │ Direct Tools│  │ LangChain Agent    │ │
│ │             │  │ (Quinn Reasoning)  │ │
│ │ • Salesforce│  │                    │ │
│ │ • Slack     │  │ ┌────────────────┐ │ │
│ │ • Sheets    │  │ │ Internal Tools │ │ │
│ │             │  │ │ • think_tool   │ │ │
│ │             │  │ │ • qualification│ │ │
│ │             │  │ │ • transfer     │ │ │
│ │             │  │ │ • knowledge    │ │ │
│ │             │  │ └────────────────┘ │ │
│ └─────────────┘  └────────────────────┘ │
└─────────────────────────────────────────┘
    ↓
Return decisions/data to Telnyx
    ↓
Continue conversation or Transfer to Human
    ↓
End-of-call logging and notifications
```

## Component Breakdown

### 1. **Telnyx Voice Platform** (Front-end)
- Receives incoming calls to your phone number
- Runs Quinn AI agent with your custom system prompt
- Handles voice synthesis (TTS) and speech recognition (STT)
- Makes webhook calls to your backend for complex decisions
- Can transfer calls to human agents when needed

### 2. **FastAPI Backend** (`main.py`) (Brain)
**Location:** `/Users/verawang/Desktop/Projects/QuinnVoiceAgent/main.py`

**Webhook Endpoints:**
- `/tools/salesforce-lookup` - Look up caller in CRM
- `/agent/think-and-act` - Central reasoning and decision-making
- `/tools/slack-notify` - Send team notifications
- `/tools/log-activity` - Log activities to Google Sheets

### 3. **Internal Agent System** (`agent/`)
```
agent/
├── quinn_agent.py          # LangChain ReAct agent coordinator
└── tools/
    ├── think_tool.py        # GPT-powered reasoning for complex decisions
    ├── qualification_tool.py # Lead scoring algorithm (0-100 points)
    ├── transfer_tool.py     # Routing decision logic (SQL/SSL/DQ)
    └── knowledge_tool.py    # Telnyx product knowledge base
```

### 4. **Direct Tools** (`direct_tools/`)
```
direct_tools/
├── salesforce_lookup.py    # Fast CRM integration
├── slack_notification.py   # Team notifications with rich formatting
└── sheets_logger.py        # Analytics and activity logging
```

## Complete Call Flow

### Phase 1: Call Initiation & Identity Discovery
```
1. Caller dials your Telnyx number
2. Telnyx answers and starts Quinn AI agent
3. Quinn greets and asks about existing account
4. IMMEDIATE Salesforce lookup via webhook

Example:
Caller: "Hi, I need help with SMS pricing"
Quinn: "I'd be happy to help! Do you already have a Telnyx account?"
Caller: "Yes, we do"
Quinn: "One moment while I pull up your record..."

[Webhook] POST /tools/salesforce-lookup 
Request: {"phone_number": "+1234567890"}
Response: {
  "found": true, 
  "record": {
    "Name": "John Smith", 
    "Company": "Acme Corp",
    "AE_Name": "Sarah Johnson",
    "AE_Phone": "+14155551234"
  }
}

Quinn: "Great! I see you're John from Acme Corp. What can I help you with regarding SMS?"
```

### Phase 2: Problem Solving + Progressive Qualification
Quinn listens to the need and uses intelligent tool selection:

```
Caller: "We need to send about 500k SMS per month to US and UK customers"
Quinn: "I can help with that. Let me get you accurate pricing..."

[Webhook] POST /agent/think-and-act 
Request: {
  "conversation_context": "John from Acme Corp needs 500k SMS/mo US+UK",
  "caller_info": {"Name": "John Smith", "Company": "Acme Corp"},
  "specific_query": "provide Messaging API pricing for US+UK at 500k volume with qualification assessment"
}

Backend Processing:
1. knowledge_tool → Gets Messaging API pricing and features
2. qualification_tool → Scores lead based on volume (500k = high value)
3. Returns structured response

Response: {
  "success": true,
  "decision": "Messaging API: $0.0035 US, $0.05 UK. High volume qualifies for enterprise pricing.",
  "qualification_data": {
    "score": 75,
    "level": "SSL", 
    "urgency": "low"
  }
}

Quinn: "For that volume, you'd pay about $1,750 for US messages and roughly $25k for UK. With your volume, you'd qualify for enterprise pricing which could reduce those rates significantly..."
```

### Phase 3: Routing Decision
Based on qualification score, urgency, and business rules:

```
[Webhook] POST /agent/think-and-act
Request: {
  "conversation_context": "John, Acme Corp, 500k SMS/mo, enterprise volume",
  "specific_query": "final qualification score and routing recommendation"
}

Backend Processing:
1. qualification_tool → Final scoring (company size + volume + use case)
2. transfer_tool → Routing logic based on score and urgency

Response: {
  "qualification": "SQL", 
  "score": 85, 
  "should_transfer": true, 
  "transfer_target": "AE",
  "reasoning": "High volume + enterprise company = qualified lead"
}

Quinn: "Based on your requirements, I'll connect you with Sarah Johnson, your account executive, who can create a custom enterprise solution. Transferring you now."

[Telnyx Transfer] → Sarah's direct line (+14155551234)
```

### Phase 4: Call Completion & Team Notification
Whether transferred or conversation completed:

```
[Webhook] POST /tools/slack-notify 
Request: {
  "caller_name": "John Smith",
  "caller_company": "Acme Corp",
  "qualification": "SQL", 
  "score": 85,
  "urgency": "low",
  "duration": "4m30s",
  "outcome": "Transferred to AE",
  "summary": "Acme Corp needs 500k SMS/mo enterprise solution - high value opportunity",
  "transfer_target": "AE",
  "conversation_id": "call_20241201_143022"
}

Slack Message Posted:
📞 Quinn Call Summary
Caller: John Smith (Acme Corp)
Qualification: 🟢 SQL (Score: 85)
Duration: 4m30s
Outcome: Transferred to AE ➡️ Sarah Johnson
Summary: Acme Corp needs 500k SMS/mo enterprise solution - high value opportunity

[Webhook] POST /tools/log-activity
Request: {
  "conversation_id": "call_20241201_143022",
  "tool_used": "final_summary",
  "input_summary": "Call completion",
  "output_summary": "SQL transferred to AE",
  "caller_info": {"Name": "John Smith", "Company": "Acme Corp"},
  "notes": "High value SMS opportunity"
}
```

## Key Design Principles

### 1. **Speed-Optimized Architecture**
- **Direct tools** (Salesforce, Slack, Sheets) provide sub-second responses
- **Agent Reasoning** only called when complex logic is needed
- **Parallel processing** where possible (async operations)
- **Background logging** doesn't block conversation flow

### 2. **Hybrid Intelligence**
- **Rule-based qualification** for consistency and speed
- **LLM reasoning** for edge cases and complex decisions
- **Structured product knowledge** for accurate information
- **Transfer logic** based on proven sales methodology

### 3. **Real-World Integration**
- **Salesforce integration** provides existing customer context
- **Slack notifications** give team visibility and enable quick handoffs
- **Google Sheets logging** enables analytics and performance tracking
- **Telnyx transfer system** seamlessly routes to appropriate human agents

## Qualification Scoring System

### Scoring Factors (0-100 points):
- **Company Size**: enterprise(20), corporation(15), startup(5)
- **Use Cases**: voice api(25), messaging api(20), contact center(18)
- **Volume Indicators**: million(20), thousands(15), high-volume(15)
- **Budget/Timeline**: budget approved(15), need asap(12), this quarter(10)
- **Existing Customer**: contact record(10)
- **Authority Level**: cto/ceo(10), director(8), manager(6)

### Routing Logic:
- **SQL (80+)**: Always transfer to Account Executive
- **SSL (50-79)**: Continue with Quinn; transfer if high urgency or custom pricing needed
- **DQ (<50)**: Still help fully; suggest alternatives only if truly not a fit

### Urgency Detection:
Keywords: urgent, asap, immediately, emergency, down, broken, deadline, launch

## Data Flow Summary

```
Incoming Call → Telnyx → Quinn Prompt
     ↓
Salesforce Lookup → Customer Context: "John, Acme Corp"
     ↓ 
Customer Question → Agent Reasoning → Knowledge Tool → Product Info
     ↓
Qualification → Agent Reasoning → Qualification Tool → Score: 85 (SQL)
     ↓
Transfer Decision → Agent Reasoning → Transfer Tool → Route to AE
     ↓
Transfer Execution → Telnyx Transfer → Account Executive
     ↓
Call Summary → Slack Notification + Google Sheets Logging
```

## Deployment Architecture

### Backend (Replit)
```
https://your-project.replit.app/
├── /tools/salesforce-lookup    (Direct CRM integration)
├── /agent/think-and-act        (LangChain agent orchestration)
├── /tools/slack-notify         (Team notifications)
├── /tools/log-activity         (Analytics logging)
└── /                          (Health check)
```

### Telnyx Configuration
- Phone number routes to Quinn AI agent
- System prompt with conversational logic and tool orchestration rules
- Webhook tools pointing to Replit endpoints
- Transfer targets: Account Executive queue, Human Agent queue

### Required Environment Variables
```bash
# Salesforce Integration
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password  
SALESFORCE_SECURITY_TOKEN=your_token

# AI/Reasoning
OPENAI_API_KEY=sk-your_openai_key

# Notifications
SLACK_BOT_TOKEN=xoxb-your_slack_token

# Analytics
GOOGLE_SHEETS_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account"...}
```

## Why This Architecture Works

### ✅ **Performance**
- Voice calls require <1 second response times
- Direct tools are optimized for speed
- Agent reasoning is used selectively for complex decisions
- Background processes don't block conversation flow

### ✅ **Accuracy** 
- Structured qualification rules prevent inconsistent scoring
- Real Salesforce data enables personalized conversations
- Curated product knowledge base ensures consistent information
- Transfer logic follows proven sales methodology

### ✅ **Scalability**
- Stateless webhook architecture handles concurrent calls
- Easy to modify qualification rules without redeployment
- Modular tool system allows adding new integrations
- Can scale horizontally with multiple Replit instances

### ✅ **Business Value**
- Captures and qualifies every inbound lead automatically
- Routes high-value prospects to sales team immediately
- Provides detailed analytics on call quality and conversion rates
- Maintains team visibility with real-time Slack notifications
- Reduces sales team workload while improving lead quality

## In Essence

Quinn is a **phone-based sales qualification system** that thinks like an experienced sales rep but operates 24/7 with perfect consistency, detailed logging, and intelligent routing. It handles the initial qualification and information gathering so your human sales team can focus on closing qualified opportunities.