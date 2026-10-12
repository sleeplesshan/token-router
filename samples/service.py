"""Public, synthetic retry example; never executed by the router."""
def retry_delay(attempt):
    """Return capped exponential backoff in seconds."""
    return min(2 ** attempt, 30)
