"""
Metabase API Client.
Handles all HTTP communication with the Metabase API.
"""

import base64
import httpx
import logging
import re
from typing import Any, Dict, Optional

from metabase_mcp_navi.config import MetabaseConfig, AuthMethod, get_config

logger = logging.getLogger("metabase-mcp.client")


class MetabaseClientError(Exception):
    """Custom exception for Metabase API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class MetabaseClient:
    """
    HTTP client for Metabase API.
    Handles authentication, requests, and error handling.
    """
    
    def __init__(self, config: Optional[MetabaseConfig] = None):
        """Initialize the client with configuration."""
        self.config = config or get_config()
        self._session_token: Optional[str] = None
        self._client: Optional[httpx.Client] = None
    
    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.url,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
        return self._client
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on auth method."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.config.auth_method == AuthMethod.API_KEY:
            headers["X-API-KEY"] = self.config.api_key
        elif self.config.auth_method == AuthMethod.SESSION_ID:
            headers["X-Metabase-Session"] = self.config.session_id
        elif self.config.auth_method == AuthMethod.USERNAME_PASSWORD:
            if not self._session_token:
                self._authenticate()
            headers["X-Metabase-Session"] = self._session_token
        
        return headers
    
    def _authenticate(self) -> None:
        """Authenticate using username/password and get session token."""
        logger.info("Authenticating with username/password...")
        try:
            response = self.client.post(
                "/api/session",
                json={
                    "username": self.config.username,
                    "password": self.config.password
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            self._session_token = data.get("id")
            logger.info("Authentication successful")
        except httpx.HTTPStatusError as e:
            raise MetabaseClientError(
                f"Authentication failed: {e.response.text}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise MetabaseClientError(f"Authentication error: {str(e)}")
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_on_auth_error: bool = True
    ) -> Any:
        """
        Make an authenticated request to the Metabase API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/api/dashboard")
            params: Query parameters
            json_data: JSON body data
            retry_on_auth_error: Retry once if auth fails (for session renewal)
        
        Returns:
            Parsed JSON response
        """
        headers = self._get_auth_headers()
        
        try:
            response = self.client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
                headers=headers
            )
            response.raise_for_status()
            
            # Handle empty responses
            if not response.content:
                return {}
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            # Handle auth errors - retry once with fresh token
            if e.response.status_code == 401 and retry_on_auth_error:
                logger.warning("Auth error, attempting re-authentication...")
                self._session_token = None
                if self.config.auth_method == AuthMethod.USERNAME_PASSWORD:
                    self._authenticate()
                    return self.request(method, endpoint, params, json_data, retry_on_auth_error=False)
            
            error_body = None
            try:
                error_body = e.response.json()
            except:
                error_body = {"raw": e.response.text}
            
            raise MetabaseClientError(
                f"API error on {method} {endpoint}: {e.response.status_code}",
                status_code=e.response.status_code,
                response=error_body
            )
        except httpx.TimeoutException:
            raise MetabaseClientError(f"Request timeout on {method} {endpoint}")
        except Exception as e:
            raise MetabaseClientError(f"Request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a GET request."""
        return self.request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
        """Make a POST request."""
        return self.request("POST", endpoint, json_data=json_data)
    
    def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
        """Make a PUT request."""
        return self.request("PUT", endpoint, json_data=json_data)
    
    def delete(self, endpoint: str) -> Any:
        """Make a DELETE request."""
        return self.request("DELETE", endpoint)
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection and return current user info."""
        try:
            user = self.get("/api/user/current")
            return {
                "success": True,
                "user": user.get("common_name", user.get("email")),
                "email": user.get("email"),
                "is_superuser": user.get("is_superuser", False)
            }
        except MetabaseClientError as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": e.status_code
            }
    
    def request_binary(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_on_auth_error: bool = True
    ) -> bytes:
        """
        Make an authenticated request that returns binary data (e.g., images).
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body data
            retry_on_auth_error: Retry once if auth fails
        
        Returns:
            Raw bytes response
        """
        headers = self._get_auth_headers()
        # For binary requests, we want to accept any content type
        headers["Accept"] = "*/*"
        
        try:
            response = self.client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
                headers=headers
            )
            response.raise_for_status()
            return response.content
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and retry_on_auth_error:
                logger.warning("Auth error, attempting re-authentication...")
                self._session_token = None
                if self.config.auth_method == AuthMethod.USERNAME_PASSWORD:
                    self._authenticate()
                    return self.request_binary(method, endpoint, params, json_data, retry_on_auth_error=False)
            
            raise MetabaseClientError(
                f"API error on {method} {endpoint}: {e.response.status_code}",
                status_code=e.response.status_code
            )
        except httpx.TimeoutException:
            raise MetabaseClientError(f"Request timeout on {method} {endpoint}")
        except Exception as e:
            raise MetabaseClientError(f"Request failed: {str(e)}")
    
    def get_card_image(self, card_id: int) -> bytes:
        """
        Get a card/question as PNG image.
        Uses the pulse preview endpoint which returns HTML with embedded base64 image.
        
        Args:
            card_id: The ID of the card
        
        Returns:
            PNG image bytes
        """
        # Use pulse preview endpoint which works reliably
        html_content = self.request_text("GET", f"/api/pulse/preview_card/{card_id}")
        
        # Extract base64 encoded images from HTML
        img_pattern = r'data:image/png;base64,([A-Za-z0-9+/=]+)'
        matches = re.findall(img_pattern, html_content)
        
        if not matches:
            raise MetabaseClientError(
                f"No image found in preview for card {card_id}",
                status_code=404
            )
        
        # Return the largest image (main chart)
        largest = max(matches, key=len)
        return base64.b64decode(largest)
    
    def request_text(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_on_auth_error: bool = True
    ) -> str:
        """
        Make an authenticated request that returns text/HTML.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body data
            retry_on_auth_error: Retry once if auth fails
        
        Returns:
            Text response content
        """
        headers = self._get_auth_headers()
        headers["Accept"] = "text/html, text/plain, */*"
        
        try:
            response = self.client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
                headers=headers
            )
            response.raise_for_status()
            return response.text
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and retry_on_auth_error:
                logger.warning("Auth error, attempting re-authentication...")
                self._session_token = None
                if self.config.auth_method == AuthMethod.USERNAME_PASSWORD:
                    self._authenticate()
                    return self.request_text(method, endpoint, params, json_data, retry_on_auth_error=False)
            
            raise MetabaseClientError(
                f"API error on {method} {endpoint}: {e.response.status_code}",
                status_code=e.response.status_code
            )
        except httpx.TimeoutException:
            raise MetabaseClientError(f"Request timeout on {method} {endpoint}")
        except Exception as e:
            raise MetabaseClientError(f"Request failed: {str(e)}")
    
    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None


# Global client instance
_client: Optional[MetabaseClient] = None


def get_client() -> MetabaseClient:
    """Get or create the global client instance."""
    global _client
    if _client is None:
        _client = MetabaseClient()
    return _client
