import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class SheetsLogger:
    """Tool for logging Quinn activity and conversations to Google Sheets"""
    
    def __init__(self, service_account_json: str, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.executor = ThreadPoolExecutor(max_workers=2)  # For async operations
        
        # Initialize Google Sheets client
        try:
            # Parse service account JSON
            if service_account_json.startswith('{'):
                # JSON string
                service_account_info = json.loads(service_account_json)
            else:
                # File path
                with open(service_account_json, 'r') as f:
                    service_account_info = json.load(f)
            
            # Set up credentials
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_info(
                service_account_info, scopes=scopes
            )
            
            self.gc = gspread.authorize(credentials)
            self.sheet = self.gc.open_by_key(spreadsheet_id)
            
            # Ensure worksheets exist
            self._setup_worksheets()
            
            logger.info("Google Sheets logger initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {str(e)}")
            raise
    
    def _setup_worksheets(self):
        """Set up required worksheets with headers"""
        try:
            # Activity Log worksheet
            try:
                self.activity_sheet = self.sheet.worksheet("Activity_Log")
            except gspread.WorksheetNotFound:
                self.activity_sheet = self.sheet.add_worksheet(
                    title="Activity_Log", rows=1000, cols=10
                )
                # Add headers
                headers = [
                    "Timestamp", "Conversation_ID", "Tool_Used", "Input_Summary",
                    "Output_Summary", "Duration_Ms", "Status", "Error", "Caller_Info", "Notes"
                ]
                self.activity_sheet.append_row(headers)
            
            # Call Summary worksheet  
            try:
                self.summary_sheet = self.sheet.worksheet("Call_Summaries")
            except gspread.WorksheetNotFound:
                self.summary_sheet = self.sheet.add_worksheet(
                    title="Call_Summaries", rows=1000, cols=15
                )
                # Add headers
                headers = [
                    "Timestamp", "Conversation_ID", "Caller_Name", "Caller_Company",
                    "Qualification", "Score", "Urgency", "Duration", "Outcome",
                    "Transfer_Target", "Summary", "Tools_Used", "AE_Name", "Phone_Number", "Notes"
                ]
                self.summary_sheet.append_row(headers)
            
            logger.info("Worksheets setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up worksheets: {str(e)}")
            raise
    
    async def log_activity(
        self,
        conversation_id: str,
        tool_used: str,
        input_summary: str,
        output_summary: str,
        duration_ms: int = 0,
        status: str = "success",
        error: str = None,
        caller_info: Dict[str, Any] = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Log individual tool activity to Google Sheets
        
        Args:
            conversation_id: Unique conversation identifier
            tool_used: Name of the tool that was used
            input_summary: Brief summary of input to the tool
            output_summary: Brief summary of tool output
            duration_ms: Tool execution time in milliseconds
            status: success/error/timeout
            error: Error message if any
            caller_info: Caller information from Salesforce
            notes: Additional notes
            
        Returns:
            Status of the logging operation
        """
        try:
            # Safety check for extremely large content (Google Sheets limit is 50k chars)
            if input_summary and len(input_summary) > 45000:
                logger.warning(f"Large input_summary: {len(input_summary)} chars (Google Sheets limit: 50k)")
            if output_summary and len(output_summary) > 45000:
                logger.warning(f"Large output_summary: {len(output_summary)} chars (Google Sheets limit: 50k)")
            
            # Prepare row data
            row_data = [
                datetime.now().isoformat(),
                conversation_id or "unknown",
                tool_used,
                input_summary if input_summary else "",  # No arbitrary limits - Google Sheets supports 50k chars
                output_summary if output_summary else "",  # No arbitrary limits - capture complete decisions
                duration_ms,
                status,
                error if error else "",  # Complete error messages
                json.dumps(caller_info) if caller_info else "",
                notes if notes else ""
            ]
            
            # Log asynchronously
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.activity_sheet.append_row,
                row_data
            )
            
            logger.info(f"Activity logged: {tool_used} for conversation {conversation_id}")
            
            return {
                "success": True,
                "logged_at": row_data[0],
                "row_data": row_data
            }
            
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def log_call_summary(
        self,
        conversation_id: str,
        caller_name: str = "Unknown",
        caller_company: str = None,
        qualification: str = "DQ", 
        score: int = 0,
        urgency: str = "low",
        duration: str = "Unknown",
        outcome: str = "Completed",
        transfer_target: str = None,
        summary: str = None,
        tools_used: List[str] = None,
        ae_name: str = None,
        phone_number: str = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Log complete call summary to Google Sheets
        
        Args:
            conversation_id: Unique conversation identifier
            caller_name: Name of the caller
            caller_company: Company name
            qualification: SQL/SSL/DQ
            score: Qualification score
            urgency: high/low
            duration: Call duration
            outcome: Final outcome
            transfer_target: AE/BDR if transferred
            summary: Call summary
            tools_used: List of tools used during call
            ae_name: Account Executive name if transferred
            phone_number: Caller phone number
            notes: Additional notes
            
        Returns:
            Status of the logging operation
        """
        try:
            # Prepare row data
            row_data = [
                datetime.now().isoformat(),
                conversation_id or "unknown",
                caller_name,
                caller_company or "",
                qualification,
                score,
                urgency,
                duration,
                outcome,
                transfer_target or "",
                summary if summary else "",  # Complete call summaries
                ", ".join(tools_used) if tools_used else "",
                ae_name or "",
                phone_number or "",
                notes if notes else ""
            ]
            
            # Log asynchronously
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.summary_sheet.append_row,
                row_data
            )
            
            logger.info(f"Call summary logged for conversation {conversation_id}")
            
            return {
                "success": True,
                "logged_at": row_data[0],
                "qualification": qualification,
                "score": score
            }
            
        except Exception as e:
            logger.error(f"Error logging call summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity for monitoring"""
        try:
            # Get recent rows
            rows = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.activity_sheet.get_all_records()[-limit:]
            )
            
            return rows
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}")
            return []
    
    async def get_call_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get call statistics for the specified number of days"""
        try:
            # Get all call summaries
            summaries = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.summary_sheet.get_all_records
            )
            
            # Filter recent calls and calculate stats
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_calls = []
            for summary in summaries:
                try:
                    call_date = datetime.fromisoformat(summary['Timestamp'])
                    if call_date > cutoff_date:
                        recent_calls.append(summary)
                except ValueError:
                    continue
            
            # Calculate statistics
            total_calls = len(recent_calls)
            sql_count = len([c for c in recent_calls if c.get('Qualification') == 'SQL'])
            ssl_count = len([c for c in recent_calls if c.get('Qualification') == 'SSL']) 
            transfers = len([c for c in recent_calls if c.get('Transfer_Target')])
            
            stats = {
                "total_calls": total_calls,
                "sql_leads": sql_count,
                "ssl_leads": ssl_count,
                "transfers": transfers,
                "conversion_rate": round((sql_count / total_calls * 100), 2) if total_calls > 0 else 0,
                "period_days": days
            }
            
            logger.info(f"Generated stats for last {days} days: {total_calls} calls")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting call stats: {str(e)}")
            return {"error": str(e)}