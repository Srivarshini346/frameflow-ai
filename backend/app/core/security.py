import hmac
import hashlib
from typing import Optional

def generate_webhook_signature(payload_bytes: bytes, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload verification.
    """
    mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
    return "sha256=" + mac.hexdigest()

def verify_webhook_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    """
    Constant-time comparison of webhook HMAC-SHA256 signature.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = generate_webhook_signature(payload_bytes, secret)
    return hmac.compare_digest(expected, signature_header)
