# Quinn Voice Agent Enhanced Flow Documentation

## 1. Current System Analysis

### Call Pattern Analysis

Based on analysis of 10+ call transcripts from DialpadCallHistory, several key patterns emerged:

**Support vs Sales Confusion (40% of calls)**
- **8/5 transcript**: Northeast Presbyterian Church calling about billing questions, routed to sales
- **8/7 transcript**: Music Express existing customer with billing address change, routed to sales
- **8/8 transcript**: Customer with credit card payment issues, routed to sales
- **Pattern**: Existing customers with account/billing issues consistently routed to sales line

**Best Practice Sales Pattern (8/1 transcript with Mayra)**
```
Greeting → Problem Discovery → Use Case Understanding → Volume Discussion → Natural Budget Flow → Solution Guidance
```
- Customer: "I was looking for a toll free number... AI to capture leads"
- Mayra: "How are you looking to leverage AI... inbound call handling?"
- Natural flow to volume: "Do you know what roughly your volumes would look like?"
- Customer: "One or two calls a day maybe three"
- Solution recommendation: "Perfect use case... scheduling AI agent template"

**Current System Strengths**
- Sophisticated qualification tools with structured data extraction
- Salesforce lookup integration for customer history
- Intelligent scoring and routing recommendations
- LangGraph-based agent architecture with multiple specialized tools

**Problem Areas Identified**
- Inconsistent qualification approach across calls
- No clear routing mechanism for support vs sales inquiries
- Missing capability validation (can Telnyx support their use case?)
- Missing global coverage checks (are numbers available in their country?)
- Budget questions sometimes awkward or missed entirely

## 2. Dynamic Intent Classification Architecture

### Tool Response Enhancement
Every tool (qualification_tool, knowledge_tool, transfer_tool, etc.) returns intent_classification object:

```json
{
  "intent_classification": {
    "primary_intent": "sales|support|other",
    "confidence": 0.85,
    "intent_reasoning": "Customer asking about pricing for new implementation",
    "context_shift": true/false
  }
}
```

### Real-time Intent Adaptation

**Intent Can Shift Mid-Conversation** (Examples from transcripts):

1. **Support → Sales**: "I have billing questions... actually, we're also evaluating new providers"
2. **Sales → Support**: "We want to buy more numbers... but first, why isn't my current service working?"
3. **Other → Sales**: "I called to ask about your company... we might need SMS for our medical practice"

### Tool-Specific Intent Detection

- **qualification_tool**: Detects sales intent when budget/volume mentioned
- **knowledge_tool**: Detects support intent when asking about existing features/account issues
- **transfer_tool**: Uses accumulated intent history to route correctly
- **think_tool**: Analyzes conversation context for intent patterns

## 3. Enhanced Discovery Phase

For all three categories (sales/support/other), gather:

### Use Case (what are they trying to achieve?)
- Primary business need or problem to solve
- Current pain points with existing solution
- Specific features or capabilities required
- Integration requirements

### Current Situation (existing provider, pain points)  
- Current communications provider (Twilio, RingCentral, etc.)
- Monthly spend and usage patterns
- What's working vs what's not working
- Reasons for considering a change

### Budget/Volume (flexible order - either can come first)
- Monthly budget capacity
- Current usage volumes (messages, calls, numbers, etc.)
- Growth projections
- Procurement process and timeline

## 4. New Tools to Add

### Global Coverage Checker (verify number availability by country)
```python
@tool
def global_coverage_tool(country: str, number_type: str) -> str:
    """Check if Telnyx provides phone numbers in specified country"""
    # Returns availability, pricing, regulations, etc.
```

### Capability Validator (check if their use case is supported)
```python
@tool  
def capability_validator(use_case: str, requirements: str) -> str:
    """Validate if Telnyx can support the customer's specific use case"""
    # Returns capability match, limitations, alternatives
```

### Support Router (direct to appropriate support resources)
```python
@tool
def support_router(issue_type: str, customer_status: str) -> str:
    """Route support issues to appropriate resources"""
    # Returns support channel, contact info, escalation path
```

## 5. Flexible Conversation Flow

Allow Quinn to ask budget OR use case first based on conversation flow, with smart follow-ups:

### If use case first → validate capability → ask budget/volume
```
Customer: "We need SMS for medical practice reminders"
Quinn: "That's a great use case - we have HIPAA-compliant messaging for healthcare. Let me check if we support your specific requirements..."
[Capability Validator runs]
Quinn: "Perfect, we can absolutely support that. What kind of volume are you looking at monthly?"
```

### If budget first → understand use case → validate capability
```
Customer: "We're spending about $5,000/month with our current provider"
Quinn: "That's a significant investment - what are you primarily using those services for?"
Customer: "International calling and SMS for our global operations"
[Capability Validator + Global Coverage Checker run]
Quinn: "We can definitely help optimize those costs. Which countries are most important for your operations?"
```

## 6. Enhanced Response Logic

### Sales: Self-serve recommendation vs AE connection based on qualification
- **High-value/complex**: Connect with Account Executive
- **Standard needs under $1K/month**: Guide to self-service portal
- **Strategic/AI voice interest**: Prioritize for AE even with lower volume

### Support: Route to portal, docs, or support team with specific guidance  
- **Billing issues**: Route to billing@telnyx.com with specific guidance
- **Technical issues**: Route to support portal or support@telnyx.com
- **Account changes**: Determine if sales team involvement needed

### Other: Gentle discovery to reclassify or provide general guidance
- **Unclear intent**: Ask clarifying questions to determine sales vs support
- **General inquiries**: Provide helpful information while discovering intent
- **Mixed intent**: Handle multiple needs with appropriate routing

## 7. Implementation Plan

### Phase 1: Tool Enhancement (Week 1-2)
- Modify existing tools to return intent_classification in responses
- Update qualification_tool.py to include intent detection logic
- Enhance knowledge_tool.py with support vs sales intent classification
- Update transfer_tool.py to use intent history for routing decisions

### Phase 2: New Tool Development (Week 2-3)
- Build global_coverage_tool for country/number availability checking
- Create capability_validator for use case validation  
- Develop support_router for intelligent support routing
- Integration testing with existing Quinn agent architecture

### Phase 3: Flow Enhancement (Week 3-4)
- Update main quinn_agent.py to implement flexible conversation flow
- Enhance conversation state management for intent tracking
- Update response templates for better sales vs support routing
- Implement context_shift detection and handling

### Phase 4: Testing & Optimization (Week 4-5)
- Test with conversation scenarios based on transcript patterns
- A/B testing of flexible budget/use case discovery order
- Optimization of intent confidence thresholds
- Integration with existing Salesforce lookup and qualification scoring

## 8. Technical Architecture

### Enhanced Data Models

```python
class IntentClassification(BaseModel):
    primary_intent: Literal["sales", "support", "other"]
    confidence: float = Field(ge=0.0, le=1.0)
    intent_reasoning: str
    context_shift: bool = False
    supporting_evidence: List[str] = []

class ConversationState(BaseModel):
    intent_history: List[IntentClassification] = []
    current_intent: Optional[IntentClassification] = None
    discovery_data: Dict[str, Any] = {}
    routing_recommendations: List[str] = []
```

### Tool Integration Pattern

```python
def enhanced_tool_response(core_response: Dict, conversation_context: str) -> Dict:
    """Add intent classification to any tool response"""
    intent_classification = analyze_intent(conversation_context, core_response)
    
    return {
        **core_response,
        "intent_classification": intent_classification.dict(),
        "routing_guidance": get_routing_guidance(intent_classification),
        "follow_up_suggestions": get_follow_up_suggestions(intent_classification)
    }
```

### Conversation Flow State Management

```python
class EnhancedQuinnAgent:
    def __init__(self):
        self.conversation_state = ConversationState()
        self.intent_tracker = IntentTracker()
        
    async def process_turn(self, user_input: str, context: str):
        # Analyze current intent
        current_intent = self.intent_tracker.classify_intent(user_input, context)
        
        # Detect intent shifts
        if self.conversation_state.current_intent:
            current_intent.context_shift = self._detect_context_shift(
                self.conversation_state.current_intent, 
                current_intent
            )
        
        # Update conversation state
        self.conversation_state.intent_history.append(current_intent)
        self.conversation_state.current_intent = current_intent
        
        # Route to appropriate handling logic
        return await self._route_by_intent(current_intent, user_input, context)
```

## 9. Success Metrics

### Conversation Quality Metrics
- **Intent Classification Accuracy**: >90% correct intent detection
- **Context Shift Detection**: >85% accuracy in detecting intent changes
- **Routing Accuracy**: >95% correct sales vs support routing

### Business Impact Metrics  
- **Reduced Misrouted Calls**: Target 80% reduction in support calls to sales
- **Improved Qualification Rate**: Target 25% improvement in SQL conversion
- **Faster Resolution**: Target 40% reduction in multi-touch resolution for support issues

### User Experience Metrics
- **Conversation Flow Naturalness**: Qualitative assessment of conversation quality
- **Customer Satisfaction**: Post-call survey scores
- **Agent Efficiency**: Time to resolution, successful transfers

## 10. Engineering Reference

### Key Files to Modify

1. **`/agent/quinn_agent.py`**: Main agent logic with enhanced flow management
2. **`/agent/tools/qualification_tool.py`**: Add intent classification to qualification responses
3. **`/agent/tools/knowledge_tool.py`**: Enhance with support vs sales intent detection
4. **`/agent/tools/transfer_tool.py`**: Update routing logic with intent history
5. **`/agent/models/qualification_models.py`**: Add intent classification data models

### New Files to Create

1. **`/agent/tools/global_coverage_tool.py`**: Country/number availability checking
2. **`/agent/tools/capability_validator.py`**: Use case validation against Telnyx capabilities  
3. **`/agent/tools/support_router.py`**: Intelligent support routing
4. **`/agent/models/intent_models.py`**: Intent classification and conversation state models
5. **`/agent/utils/intent_tracker.py`**: Intent analysis and context shift detection utilities

### Integration Points

- **Salesforce Integration**: Maintain existing customer lookup while adding intent-aware routing
- **Telnyx API Integration**: Leverage for global coverage and capability validation
- **Notification Systems**: Enhance Slack/email notifications with intent context
- **Analytics Pipeline**: Capture intent classification data for continuous improvement

## 11. Conversation Examples

### Example 1: Dynamic Sales → Support → Sales Intent Shift

```
Customer: "Hi, I'm interested in your SMS services for my business."
Quinn: [Intent: Sales] "Great! I'd love to help you with SMS. What type of business use case are you looking to support?"

Customer: "Actually, before we get into that, I'm already a customer and having issues with my current SMS delivery rates."
Quinn: [Intent: Support, Context Shift: True] "I see you're an existing customer with delivery rate concerns. Let me look up your account and connect you with our support team who can investigate those delivery issues. Can you provide your account email?"

Customer: "Sure, it's john@company.com. But after we fix this, I do want to discuss adding international SMS capabilities."
Quinn: [Intent: Mixed Support+Sales] "Perfect! I'll get your delivery issues resolved first, and then I can connect you with our sales team to discuss expanding your international SMS coverage."
```

### Example 2: Flexible Budget/Use Case Discovery

```
Customer: "We're currently spending about $2,000 monthly on communications."
Quinn: [Intent: Sales] "That's a substantial investment - I'd love to understand how we might help optimize that. What are you primarily using those services for?"

Customer: "Mostly outbound calling for our call center, about 50,000 minutes monthly."
Quinn: [Capability Validator triggered] "Excellent, we can definitely support that volume. Are you calling domestically or internationally?"

Customer: "Mostly US, but we're expanding to Canada and Mexico."
Quinn: [Global Coverage Checker triggered] "Perfect timing - we have excellent rates and coverage for North American markets. Based on your volume, you'd likely qualify for our enterprise pricing. Would you like me to connect you with an Account Executive to discuss a custom quote?"
```

This documentation serves as both an engineering specification and a reference for future AI agents working on the Quinn Voice Agent system.