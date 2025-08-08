from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Salesforce Configuration (from proven quinnline integration)
    salesforce_username: str
    salesforce_password: str
    salesforce_security_token: str
    salesforce_domain: str = "login"  # Default to production
    
    # Slack Integration
    slack_bot_token: str
    slack_channel_id: str = "#quinn-voice-calls"  # Default channel name
    
    # Google Sheets Integration  
    google_sheets_id: str
    google_service_account_json: str
    
    # OpenAI for LangChain Agent
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"  # Fast model for voice calls
    
    # Server Configuration
    webhook_base_url: str = "https://your-replit-url.com"
    port: int = 8000
    debug: bool = False
    
    # Telnyx Integration
    telnyx_api_key: Optional[str] = None  # Optional for webhook-only mode
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env

# Global settings instance
settings = Settings()