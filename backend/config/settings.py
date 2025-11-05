"""
Configuration settings for AI Financial Statement Generation System
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration class for the AI Financial Statement System"""
    
    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Database Configuration
    sqlite_db_path: str = "fs_audit.db"
    cache_ttl_hours: int = 1
    
    # Processing Configuration
    max_workers: int = 4
    pdf_dpi: int = 300
    
    # Model Configuration
    gemini_pro_model: str = "gemini-2.5-pro"
    gemini_flash_model: str = "gemini-2.5-flash"
    grok_model: str = "x-ai/grok-4-fast"
    
    # Similarity Thresholds for Account Mapping
    auto_map_threshold: float = 0.85
    review_threshold: float = 0.7
    
    # Monitoring Configuration
    metrics_port: int = 8000
    prometheus_endpoint: str = "/metrics"
    
    # File Monitoring
    input_directory: str = "./input"
    output_directory: str = "./output"
    
    # Email Configuration for Alerts
    smtp_server: Optional[str] = os.getenv("SMTP_SERVER")
    smtp_port: int = 587
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    alert_email: Optional[str] = os.getenv("ALERT_EMAIL")
    
    # Processing Limits
    max_file_size_mb: int = 50
    max_pages_per_pdf: int = 100
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: int = 2
    
    validate_on_init: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.validate_on_init:
            return
            
        missing_vars = []
        if not self.gemini_api_key:
            missing_vars.append("GEMINI_API_KEY")
        if not self.openrouter_api_key:
            missing_vars.append("OPENROUTER_API_KEY")
        if not self.supabase_url:
            missing_vars.append("SUPABASE_URL")
        if not self.supabase_anon_key:
            missing_vars.append("SUPABASE_ANON_KEY")
        if not self.supabase_service_key:
            missing_vars.append("SUPABASE_SERVICE_KEY")
        
        if missing_vars:
            print(f"Warning: Missing required environment variables: {', '.join(missing_vars)}")
            print("Application may not function properly without these variables.")
    
    def validate(self):
        """Explicitly validate configuration and raise errors if required fields are missing"""
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.supabase_anon_key:
            raise ValueError("SUPABASE_ANON_KEY environment variable is required")
        if not self.supabase_service_key:
            raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")


# Global configuration instance
config = Config()
