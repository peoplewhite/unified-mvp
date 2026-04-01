"""
Application Configuration
"""

import os

class Settings:
    """Application settings"""
    APP_NAME: str = "Global Vendor Scout"
    DEBUG: bool = True
    
    # API Keys (optional - app works in mock mode without them)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")


settings = Settings()