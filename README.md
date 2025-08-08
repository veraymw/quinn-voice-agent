# Quinn Voice Agent 🎯

An intelligent AI voice assistant that qualifies inbound sales calls and makes smart routing decisions using Telnyx voice platform integration.

## 🚀 Features

- **Real-time Voice AI**: Handles live phone conversations through Telnyx
- **Smart Lead Qualification**: GPT-4 powered scoring and routing recommendations
- **Salesforce Integration**: Instant customer lookup and account executive matching
- **Activity Tracking**: Comprehensive logging to Google Sheets
- **Slack Notifications**: Team alerts for qualified leads
- **Production Ready**: Sub-20s response times optimized for voice calls

## 🏗️ Architecture

```
📞 Inbound Call → Telnyx Platform → Quinn AI Agent → Backend Tools
                                        ↓
                     ┌─────────────────────────────────────┐
                     │  FastAPI Backend (main.py)         │
                     │                                     │
                     │  🤖 LangChain Agent (Quinn)        │
                     │  ├── Qualification Tool            │
                     │  ├── Transfer Tool                  │
                     │  ├── Knowledge Tool                 │
                     │  └── Think Tool                     │
                     │                                     │
                     │  🔧 Direct Tools                    │
                     │  ├── Salesforce Lookup             │
                     │  ├── Slack Notifications           │
                     │  └── Activity Logger               │
                     └─────────────────────────────────────┘
```

## 📊 Performance

- **Salesforce Lookup**: ~1.1s response time
- **AI Qualification**: ~15s end-to-end processing
- **Lead Scoring**: 0-100 scale with SQL/SSL/DQ classification
- **Voice Optimized**: Built for real-time conversation flow

## 🛠️ Technology Stack

- **Backend**: FastAPI + Python 3.13
- **AI Engine**: LangChain + LangGraph + OpenAI GPT-4
- **CRM**: Salesforce API integration
- **Voice Platform**: Telnyx webhook integration
- **Data Storage**: Google Sheets + Slack
- **Deployment**: Replit/Cloud ready

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/quinn-voice-agent.git
cd quinn-voice-agent
python -m venv quinn-voice-agent-env
source quinn-voice-agent-env/bin/activate  # On Windows: quinn-voice-agent-env\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Create `.env` file with your credentials:

```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_key

# Server Configuration  
PORT=8000
WEBHOOK_BASE_URL=https://your-deployment-url.com

# Salesforce Configuration
SALESFORCE_USERNAME=your_salesforce_username
SALESFORCE_PASSWORD=your_salesforce_password
SALESFORCE_SECURITY_TOKEN=your_salesforce_token
SALESFORCE_DOMAIN=login

# Slack Integration
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_CHANNEL_ID=#your-channel

# Google Sheets Integration
GOOGLE_SHEETS_ID=your_sheets_id
GOOGLE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}
```

### 3. Run Locally

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Test health endpoint: `curl http://localhost:8000/`

## 🔗 API Endpoints

### Webhook Tools (for Telnyx)

| Endpoint | Purpose | Response Time |
|----------|---------|---------------|
| `POST /tools/salesforce-lookup` | Customer record lookup | ~1.1s |
| `POST /agent/think-and-act` | AI qualification & routing | ~15s |
| `POST /tools/slack-notify` | Team notifications | ~1s |
| `POST /tools/log-activity` | Activity tracking | ~0.5s |

### Example Usage

```bash
# Salesforce Customer Lookup
curl -X POST http://localhost:8000/tools/salesforce-lookup \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "conversation_id": "test-123"}'

# AI-Powered Lead Qualification  
curl -X POST http://localhost:8000/agent/think-and-act \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_context": "Caller: Hi, I need messaging APIs for my startup", 
    "specific_query": "score and routing recommendation",
    "conversation_id": "test-456"
  }'
```

## 🎯 Telnyx Integration

Configure these webhook URLs in your Telnyx AI Assistant:

1. **Salesforce Lookup**: `https://your-url.com/tools/salesforce-lookup`
2. **Agent Reasoning**: `https://your-url.com/agent/think-and-act` 
3. **Slack Notification**: `https://your-url.com/tools/slack-notify`
4. **Activity Logger**: `https://your-url.com/tools/log-activity`

See `QuinnVoiceAgentNotes/TELNYX_TOOL_CONFIGURATION.md` for detailed setup instructions.

## 📋 Project Structure

```
quinn-voice-agent/
├── agent/                  # LangChain agent and tools
│   ├── quinn_agent.py     # Main agent orchestrator
│   └── tools/             # Individual agent tools
├── core/                  # Data models and utilities
│   └── data.py           # Pydantic models
├── direct_tools/          # Fast external integrations
│   ├── salesforce_lookup.py
│   ├── slack_notification.py
│   └── sheets_logger.py
├── QuinnVoiceAgentNotes/  # Documentation
├── main.py               # FastAPI application
├── config.py            # Environment configuration
└── requirements.txt     # Dependencies
```

## 🧪 Testing

The backend includes comprehensive endpoint testing:

```bash
# Run test suite (see QuinnVoiceAgentNotes/BACKEND_TEST_RESULTS.md)
python -c "from main import app; print('✅ Import test passed')"

# Test individual endpoints
curl http://localhost:8000/                    # Health check
curl -X POST http://localhost:8000/tools/salesforce-lookup  # Salesforce test
# ... additional test commands in test results
```

## 📈 Business Impact

- **Faster Lead Response**: Immediate customer context from Salesforce
- **Smarter Routing**: AI-powered qualification reduces AE time waste  
- **Complete Tracking**: Every interaction logged for sales analytics
- **Team Coordination**: Real-time Slack alerts for hot leads

## 🚀 Deployment

### Replit Deployment
1. Import project to Replit
2. Add environment variables to Secrets
3. Update `WEBHOOK_BASE_URL` with your Replit URL
4. Configure Telnyx webhooks

### Cloud Deployment
- Compatible with AWS Lambda, Google Cloud Run, or any Python hosting
- Requires environment variables configuration
- Update webhook URLs in Telnyx portal

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions or support:
- Create an issue in this repository
- Check documentation in `QuinnVoiceAgentNotes/`
- Review test results in `BACKEND_TEST_RESULTS.md`

---

**Built with ❤️ for intelligent voice-powered sales**