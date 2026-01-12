"""
Configuration management for Metabase MCP Server.
Handles environment variables and authentication settings.
"""

import os
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("metabase-mcp")


class AuthMethod(Enum):
    """Authentication methods supported by the server."""
    API_KEY = "api_key"
    SESSION_ID = "session_id"
    USERNAME_PASSWORD = "username_password"


@dataclass
class MetabaseConfig:
    """Configuration for Metabase connection."""
    url: str
    auth_method: AuthMethod
    api_key: Optional[str] = None
    session_id: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 30
    
    def __post_init__(self):
        # Remove trailing slash from URL
        self.url = self.url.rstrip('/')
        
    @classmethod
    def from_env(cls) -> "MetabaseConfig":
        """Create configuration from environment variables."""
        url = os.getenv("METABASE_URL")
        if not url:
            raise ValueError("METABASE_URL environment variable is required")
        
        api_key = os.getenv("METABASE_API_KEY")
        session_id = os.getenv("METABASE_SESSION_ID")
        username = os.getenv("METABASE_USER_EMAIL") or os.getenv("METABASE_USERNAME")
        password = os.getenv("METABASE_PASSWORD")
        verify_ssl = os.getenv("METABASE_VERIFY_SSL", "true").lower() != "false"
        timeout = int(os.getenv("METABASE_TIMEOUT", "30"))
        
        # Determine auth method based on available credentials
        if api_key:
            auth_method = AuthMethod.API_KEY
            logger.info("Using API Key authentication")
        elif session_id:
            auth_method = AuthMethod.SESSION_ID
            logger.info("Using Session ID authentication")
        elif username and password:
            auth_method = AuthMethod.USERNAME_PASSWORD
            logger.info("Using Username/Password authentication")
        else:
            raise ValueError(
                "Authentication required: provide METABASE_API_KEY, "
                "METABASE_SESSION_ID, or both METABASE_USER_EMAIL and METABASE_PASSWORD"
            )
        
        return cls(
            url=url,
            auth_method=auth_method,
            api_key=api_key,
            session_id=session_id,
            username=username,
            password=password,
            verify_ssl=verify_ssl,
            timeout=timeout
        )


def get_config() -> MetabaseConfig:
    """Get the global configuration instance."""
    return MetabaseConfig.from_env()
