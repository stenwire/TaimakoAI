import os
import hmac
import hashlib
import json
import httpx
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

SECRET = settings.PAYSTACK_SECRET_KEY
if not SECRET:
    SECRET = "sk_test_fake"
    
payload = {
  "event": "charge.success",
  "data": {
    "reference": "fake_ref_12345",
    "amount": 5000,
    "customer": {
      "email": "test@venco.africa"
    },
    "metadata": {
      "is_upgrade": True,
      "tier": "flux"
    }
  }
}

body = json.dumps(payload).encode('utf-8')
signature = hmac.new(
    key=SECRET.encode('utf-8'),
    msg=body,
    digestmod=hashlib.sha512
).hexdigest()

headers = {
    "x-paystack-signature": signature,
    "Content-Type": "application/json"
}

resp = httpx.post("http://localhost:8000/webhooks/paystack", content=body, headers=headers)
print("Status:", resp.status_code)
print("Response:", resp.text)
