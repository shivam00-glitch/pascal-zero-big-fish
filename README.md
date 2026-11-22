# PASCAL ZERO — BIG FISH

A standalone, mobile-friendly web research prototype for zero-line oscillator signals.

## Current features
- OHLCV CSV upload and validation
- Smoothed linear-regression-slope oscillator
- Candle-close confirmed zero-line BUY and down-cross markers
- Estimated BUY-to-down-cross duration, rounded to 0.25 candle
- Basic signal counts and duration dashboard
- Broker integration boundary (not connected until a broker is selected)

## Important formula disclosure
The original PASCAL ZERO V1 source formula was not supplied. The current implementation is a new,
transparent prototype inspired by the user's description; it is not claimed to reproduce V1.
The 0.25-candle duration is an interpolation estimate between candle-close oscillator values,
not a measurement of intrabar tick timing.

## CSV format
Required columns: `timestamp,open,high,low,close,volume`

Column aliases accepted: `date`, `datetime`, `time`, `vol`, `qty`.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit. For Android, deploy the app to a supported hosting service
and open its HTTPS URL in Chrome.

## GitHub
1. Create a new empty GitHub repository named `pascal-zero-big-fish`.
2. Upload the contents of this project (not the containing ZIP folder).
3. Do not upload broker credentials or `.env` files.
4. Add a deployment secret only through your hosting provider's secret manager.

## Live broker data
Live data is intentionally not enabled. Choose a broker first, then implement its official API
adapter in `pascal_zero/broker.py`. Broker API access, permissions, fees, market-data entitlements,
and rate limits vary. Do not scrape broker apps or commit tokens.

## Testing
```bash
pytest -q
```

## Risk notice
This is software for research and paper testing, not investment advice. Signals can be false,
delayed or incomplete. Historical performance does not guarantee future results. Validate with
out-of-sample data, realistic brokerage/slippage assumptions and paper trading before considering
any live use.
