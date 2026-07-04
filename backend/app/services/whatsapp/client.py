"""Meta WhatsApp Cloud API client.

All functions are stateless and accept the tenant's `access_token` and
relevant IDs explicitly. No module-level state.
"""
from typing import Any

import httpx

GRAPH_BASE = "https://graph.facebook.com/v21.0"


class WhatsAppAPIError(Exception):
    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body
        super().__init__(f"WhatsApp API {status_code}: {body}")


def _auth_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


async def send_template_message(
    phone_number_id: str,
    access_token: str,
    to_phone: str,
    template_name: str,
    language: str,
    components: list | None = None,
) -> dict:
    """Send a template message. Returns the Meta response dict.

    `components` follows Meta's template component schema:
    https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates
    """
    url = f"{GRAPH_BASE}/{phone_number_id}/messages"
    payload: dict = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
        },
    }
    if components:
        payload["template"]["components"] = components

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=_auth_headers(access_token), timeout=15.0)
        data = resp.json()
        if resp.status_code != 200:
            raise WhatsAppAPIError(resp.status_code, data)
        return data


async def create_template(
    waba_id: str,
    access_token: str,
    name: str,
    category: str,
    language: str,
    components: list,
) -> dict:
    """Submit a new template to Meta for approval.

    `components` is Meta's template component schema. Returns the response
    dict containing at minimum `id` (meta_template_id) and `status`.
    """
    url = f"{GRAPH_BASE}/{waba_id}/message_templates"
    payload = {
        "name": name,
        "category": category,
        "language": language,
        "components": components,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=_auth_headers(access_token), timeout=15.0)
        data = resp.json()
        if resp.status_code not in (200, 201):
            raise WhatsAppAPIError(resp.status_code, data)
        return data


async def list_templates(waba_id: str, access_token: str, limit: int = 100) -> list[dict]:
    """List all templates on the WABA. Returns the `data` array from Meta."""
    url = f"{GRAPH_BASE}/{waba_id}/message_templates"
    params = {"limit": limit}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url, params=params, headers=_auth_headers(access_token), timeout=15.0
        )
        data = resp.json()
        if resp.status_code != 200:
            raise WhatsAppAPIError(resp.status_code, data)
        return data.get("data", [])


async def delete_template(waba_id: str, access_token: str, name: str) -> bool:
    url = f"{GRAPH_BASE}/{waba_id}/message_templates"
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            url, params={"name": name}, headers=_auth_headers(access_token), timeout=15.0
        )
        if resp.status_code != 200:
            raise WhatsAppAPIError(resp.status_code, resp.json())
        return True


async def get_template_by_id(meta_template_id: str, access_token: str) -> dict:
    url = f"{GRAPH_BASE}/{meta_template_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=_auth_headers(access_token), timeout=15.0)
        data = resp.json()
        if resp.status_code != 200:
            raise WhatsAppAPIError(resp.status_code, data)
        return data
