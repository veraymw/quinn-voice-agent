# Quinn Voice Agent 🎯

AI-powered sales agent combining LangChain reasoning with fast webhook tools for Telnyx Voice AI Assistant.

## Quick Start

1. **Import to Replit** and set environment variables in Secrets
2. **Run project** to get your webhook URL  
3. **Configure tools in Telnyx Portal** using the URLs below
4. **Test each tool** individually before going live

## Webhook URLs (Replace with your Replit URL)

- **Salesforce Lookup**: `https://your-replit-url.com/tools/salesforce-lookup`
- **Agent Reasoning**: `https://your-replit-url.com/agent/think-and-act`  
- **Slack Notification**: `https://your-replit-url.com/tools/slack-notify`
- **Activity Logger**: `https://your-replit-url.com/tools/log-activity`

## Architecture

**Hybrid System**: Fast direct tools + intelligent LangChain agent decisions

- ✅ **Proven Salesforce integration** (copied from working quinnline)
- ✅ **Smart qualification** (80+ SQL→AE, Urgent→BDR, Others→Continue)  
- ✅ **Complete tracking** (Google Sheets + Slack notifications)
- ✅ **Voice-optimized** (sub-second responses for critical tools)

## Key Features

- **Instant Caller ID**: Salesforce lookup on every call start
- **Intelligent Qualification**: LangChain agent scores leads 0-100
- **Smart Routing**: SQL leads to AE, urgent issues to BDR
- **Complete Logging**: Every tool use tracked in Google Sheets
- **Team Notifications**: Call summaries posted to Slack

## See IMPLEMENTATION_NOTES.md for complete setup and configuration details.