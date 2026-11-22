"""
Broker integration boundary.

No broker is connected by default. Implement a broker-specific client in this
module only after choosing a broker and reviewing its official API terms.
Never commit API keys, access tokens or passwords to GitHub.
"""
def get_broker_status():
    return "NOT CONFIGURED — CSV mode is available"

def fetch_live_candles(symbol: str, interval: str, limit: int = 500):
    raise NotImplementedError(
        "Live market data adapter is not configured. Choose a broker and implement "
        "its official authenticated API client."
    )
