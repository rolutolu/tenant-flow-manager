"""Rate Limiting Service — in-memory rate limiting to protect authentication and upload endpoints."""

import time
from collections import defaultdict
from nicegui import context

# In-memory storage for action timestamps
# Structure: { key: [timestamps_of_actions] }
_attempts = defaultdict(list)


def get_client_ip() -> str:
    """Safely retrieve the client's IP address, accounting for reverse proxies."""
    try:
        client = context.get_client()
        if not client or not client.request:
            return "127.0.0.1"

        # Check standard headers set by reverse proxies (Railway, Render, Cloudflare)
        x_forwarded_for = client.request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            # First IP is the actual client
            return x_forwarded_for.split(",")[0].strip()

        real_ip = client.request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        if client.request.client:
            return client.request.client.host
    except Exception:
        pass
    return "127.0.0.1"


def check_rate_limit(key: str, limit: int, period_seconds: int) -> tuple[bool, int]:
    """Check if an action is allowed for the given key.

    Returns (is_allowed, retry_after_seconds).
    """
    now = time.time()
    # Filter out attempts older than the rate limit period
    _attempts[key] = [t for t in _attempts[key] if now - t < period_seconds]

    if len(_attempts[key]) >= limit:
        # Calculate how long before the oldest attempt falls outside the window
        oldest_attempt = _attempts[key][0]
        retry_after = int(period_seconds - (now - oldest_attempt))
        return False, max(1, retry_after)

    return True, 0


def record_attempt(key: str):
    """Record a timestamped attempt for a key."""
    _attempts[key].append(time.time())


def clear_attempts(key: str):
    """Clear all recorded attempts for a key (e.g. after a successful login)."""
    if key in _attempts:
        del _attempts[key]
