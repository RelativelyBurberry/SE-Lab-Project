from pydantic_settings import BaseSettings
from typing import List
import json
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "AlphaForge AI"
    environment: str = "development"
    
    # API Keys
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    newsdata_api_key: str = ""
    twelvedata_api_key: str = ""
    fmp_api_key: str = ""
    
    # Database
    database_url: str = ""

    # Authentication (also consumed by backend/auth.py)
    jwt_secret_key: str = ""
    
    # CORS
    # Keep this as a string so comma-separated .env values can be parsed safely.
    cors_origins: str = '["http://localhost:3000","http://localhost:5173"]'
    
    class Config:
        # Resolve .env relative to this file, not the shell's current directory.
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        case_sensitive = False
        
    @property
    def cors_origin_list(self) -> List[str]:
        """Accept either a JSON array or comma-separated origins in .env."""
        raw = (self.cors_origins or "").strip()
        if not raw:
            return ["http://localhost:3000", "http://localhost:5173"]
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
        except (json.JSONDecodeError, TypeError):
            pass
        return [origin.strip().strip('"').strip("'") for origin in raw.split(",") if origin.strip()]

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)
    
    @property
    def has_database(self) -> bool:
        return bool(self.database_url)
    
    @property
    def has_news_api(self) -> bool:
        return bool(self.newsdata_api_key)

    @property
    def has_twelvedata(self) -> bool:
        return bool(self.twelvedata_api_key)

    @property
    def has_fmp(self) -> bool:
        return bool(self.fmp_api_key)

settings = Settings()
