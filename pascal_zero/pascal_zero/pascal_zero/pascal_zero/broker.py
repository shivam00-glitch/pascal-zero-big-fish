def get_broker_status():
    return "Disconnected - No credentials configured"

def fetch_live_candles(*args, **kwargs):
    raise NotImplementedError("Live broker adapter not configured yet.")
