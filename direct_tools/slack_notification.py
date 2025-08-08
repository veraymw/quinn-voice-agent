from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class SlackNotificationTool:
    """Tool for sending Quinn call summaries to Slack channels"""
    
    def __init__(self, bot_token: str, default_channel: str = "#quinn-voice-calls"):
        self.client = WebClient(token=bot_token)
        self.default_channel = default_channel
        
    async def send_call_summary(
        self,
        caller_name: str = "Unknown Caller",
        caller_company: str = None,
        qualification: str = "DQ",
        score: int = 0,
        urgency: str = "low",
        duration: str = "Unknown",
        outcome: str = "Call completed",
        summary: str = "No summary available",
        transfer_target: str = None,
        conversation_id: str = None,
        channel: str = None
    ) -> Dict[str, Any]:
        """
        Send a formatted call summary to Slack
        
        Args:
            caller_name: Name of the caller
            caller_company: Company name if available
            qualification: SQL, SSL, or DQ
            score: Qualification score (0-100)
            urgency: high or low
            duration: Call duration
            outcome: Final outcome of the call
            summary: Brief summary of the call
            transfer_target: Where the call was transferred (AE/BDR)
            conversation_id: Unique conversation identifier
            channel: Override default channel
            
        Returns:
            Status of the Slack message send
        """
        try:
            target_channel = channel or self.default_channel
            
            # Format caller information
            caller_info = caller_name
            if caller_company:
                caller_info += f" ({caller_company})"
            
            # Choose emoji based on qualification
            emoji = self._get_qualification_emoji(qualification)
            urgency_indicator = " 🚨" if urgency == "high" else ""
            
            # Format transfer information
            transfer_info = ""
            if transfer_target:
                transfer_emoji = "➡️" if transfer_target == "AE" else "🔄"
                transfer_info = f"\n*Transfer:* {transfer_emoji} {transfer_target}"
            
            # Create the message
            message_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📞 Quinn Call Summary{urgency_indicator}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Caller:* {caller_info}"
                        },
                        {
                            "type": "mrkdwn", 
                            "text": f"*Qualification:* {emoji} {qualification} (Score: {score})"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:* {duration}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Outcome:* {outcome}{transfer_info}"
                        }
                    ]
                }
            ]
            
            # Add summary section if available
            if summary and summary != "No summary available":
                message_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Summary:*\n{summary}"
                    }
                })
            
            # Add conversation ID for reference
            if conversation_id:
                message_blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Conversation ID: `{conversation_id}`"
                        }
                    ]
                })
            
            # Send the message
            response = self.client.chat_postMessage(
                channel=target_channel,
                blocks=message_blocks,
                text=f"Quinn Call Summary - {caller_info} ({qualification})"  # Fallback text
            )
            
            logger.info(f"Slack notification sent successfully to {target_channel}")
            
            return {
                "success": True,
                "message_ts": response["ts"],
                "channel": response["channel"],
                "permalink": self._get_permalink(response["channel"], response["ts"])
            }
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {
                "success": False,
                "error": f"Slack API error: {e.response['error']}"
            }
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_urgent_alert(
        self,
        caller_name: str,
        reason: str,
        conversation_id: str = None,
        channel: str = None
    ) -> Dict[str, Any]:
        """Send urgent alert for high-priority situations"""
        try:
            target_channel = channel or self.default_channel
            
            message = f"""🚨 *URGENT: Quinn Call Alert* 🚨

*Caller:* {caller_name}
*Alert:* {reason}
*Time:* {datetime.now().strftime('%I:%M %p')}
{f'*Conversation ID:* `{conversation_id}`' if conversation_id else ''}

@here - Immediate attention needed!"""
            
            response = self.client.chat_postMessage(
                channel=target_channel,
                text=message,
                parse="full"
            )
            
            logger.info(f"Urgent Slack alert sent for {caller_name}")
            
            return {
                "success": True,
                "message_ts": response["ts"]
            }
            
        except Exception as e:
            logger.error(f"Error sending urgent Slack alert: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_qualification_emoji(self, qualification: str) -> str:
        """Get emoji based on qualification level"""
        emoji_map = {
            "SQL": "🟢",  # Green circle for qualified
            "SSL": "🟡",  # Yellow circle for sales qualified
            "DQ": "🔴"    # Red circle for disqualified
        }
        return emoji_map.get(qualification, "⚪")
    
    def _get_permalink(self, channel: str, timestamp: str) -> Optional[str]:
        """Get permalink for the sent message"""
        try:
            response = self.client.chat_getPermalink(
                channel=channel,
                message_ts=timestamp
            )
            return response["permalink"]
        except Exception as e:
            logger.warning(f"Could not get permalink: {str(e)}")
            return None