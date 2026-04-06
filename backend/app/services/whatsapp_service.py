import hmac
import hashlib
import httpx


async def send_whatsapp_message(
    phone_number_id: str,
    access_token: str,
    to_phone: str,
    text: str,
) -> bool:
    """Send a text message via WhatsApp Cloud API."""
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
        if resp.status_code == 200:
            return True
        print(f"WhatsApp API error {resp.status_code}: {resp.text}")
        return False


def verify_webhook_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify the X-Hub-Signature-256 from Meta webhook requests."""
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        app_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
