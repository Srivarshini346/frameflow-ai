import json
import httpx
from typing import Dict, Any, Optional
from app.core.security import generate_webhook_signature
from app.core.logger import logger

class WebhookService:
    """
    Sends secure HMAC-SHA256 signed webhooks to external listeners.
    """

    async def send_callback(
        self,
        webhook_url: str,
        secret: str,
        payload: Dict[str, Any]
    ) -> bool:
        if not webhook_url:
            return False

        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature = generate_webhook_signature(payload_bytes, secret)

        headers = {
            "Content-Type": "application/json",
            "X-FrameFlow-Signature": signature,
            "User-Agent": "FrameFlow-AI-Webhook/1.0"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(webhook_url, content=payload_bytes, headers=headers)
                logger.info(f"Dispatched webhook to {webhook_url} (HTTP {res.status_code})")
                return res.status_code < 300
        except Exception as e:
            logger.warning(f"Failed to dispatch webhook to {webhook_url}: {e}")
            return False

webhook_service = WebhookService()
