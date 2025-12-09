import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

async def get_google_auth_url(state: str = "") -> str:
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile openid",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    return f"{base_url}?{query_string}"

async def exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            return None
        return response.json()

async def get_google_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)
        if response.status_code != 200:
            return None
        return response.json()
