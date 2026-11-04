import hashlib
import hmac


def generate_export_signature(
    method: str,
    path: str,
    query: str,
    timestamp: str,
    secret: str
) -> str:
    """
    Generates HMAC-SHA256 signature matching upstream Urja portal signing logic:
    message = [method, path, query, timestamp].join("\n")
    """
    payload = f"{method}\n{path}\n{query}\n{timestamp}"
    signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return signature
