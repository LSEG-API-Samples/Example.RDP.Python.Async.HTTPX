# Data Platform APIs HTTP REST Application using HTTPX

- Version: 1.0
- Last update: Mar 2026
- Environment: Python + JupyterLab + Data Platform Account
- Prerequisite: Data Platform access/entitlements

Python examples that use [`httpx`](https://www.python-httpx.org/) to authenticate with [LSEG Data Platform APIs](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis) (RDP, also known as Delivery Platform) using OAuth 2.0 Password Grant, then call sample REST endpoints — covering both synchronous and asynchronous patterns.

## Project Structure

```
├── requirements.txt             # Pinned dependencies
src/
├── .env.example                 # Environment variable template
├── example_sync_httpx.py        # Synchronous — direct httpx module calls (no shared client)
├── example_client.py            # Synchronous — shared httpx.Client
├── example_async_simple.py      # Async — sequential awaits in a loop
├── example_async_gather.py      # Async — asyncio.gather() with Semaphore
└── async_learn.py               # Learning script — ExceptionGroup / except*
```

## Included Scripts

### `src/example_sync_httpx.py` — Synchronous, direct `httpx` calls

Simplest synchronous example. Each function calls `httpx.get()` / `httpx.post()` directly — no shared client or connection pool. Good as a minimal reference or quick script.

Demonstrates:
- `POST /auth/oauth2/v1/token` — OAuth 2.0 Password Grant authentication
- `GET /data/pricing/chains/v1/` — chain constituent lookup for a single RIC
- `POST /data/historical-pricing/v1/views/events` — historical trade events for multiple RICs
- Refresh token flow (`grant_type=refresh_token`)
- `POST /auth/oauth2/v1/revoke` — session revocation using HTTP Basic Auth
- Per-call `verify=False` passed directly to each `httpx` function

### `src/example_client.py` — Synchronous with shared client

Synchronous (blocking) script using a single shared `httpx.Client` instance for connection pooling and consistent configuration across all requests.

Demonstrates:
- `POST /auth/oauth2/v1/token` — OAuth 2.0 Password Grant authentication
- `GET /data/pricing/chains/v1/` — chain constituent lookup
- `POST /data/historical-pricing/v1/views/events` — historical trade events for multiple RICs (commented out, ready to enable)
- Refresh token flow (`grant_type=refresh_token`) — commented out, ready to enable
- `POST /auth/oauth2/v1/revoke` — session revocation — commented out, ready to enable
- Environment validation with a `_require_env()` helper that fails fast on missing credentials

### `src/example_async_simple.py` — Async, sequential loop

Async script using `httpx.AsyncClient`. Fetches interday-summaries for each RIC one after another inside a `for` loop. Simple starting point before introducing concurrency.

Demonstrates:
- `POST /auth/oauth2/v1/token` — async authentication
- `GET /data/historical-pricing/v1/views/interday-summaries/{ric}` — daily OHLCV data with corporate-action adjustments
- Sequential `await` per RIC — no concurrent requests

### `src/example_async_gather.py` — Async with `asyncio.gather()` and `Semaphore`

Async script that fires all RIC requests concurrently via `asyncio.gather()`, with an `asyncio.Semaphore` to cap the number of in-flight requests and avoid hitting server rate limits.

Demonstrates:
- `POST /auth/oauth2/v1/token` — async authentication
- `GET /data/historical-pricing/v1/views/interday-summaries/{ric}` — concurrent fetches for 10 RICs
- `asyncio.Semaphore` — limits concurrent requests (default: 3)
- `return_exceptions=True` — prevents one failure from cancelling the rest; each result is inspected individually
- Per-result error handling: `httpx.HTTPStatusError`, `httpx.RequestError`, generic `Exception`


### `src/async_learn.py` — `ExceptionGroup` and `except*` sandbox

Standalone learning script demonstrating how `asyncio.gather(return_exceptions=True)` results can be re-raised as an `ExceptionGroup`, and how `except*` dispatches individual exception types from the group.

## Prerequisites

- Python 3.11+ (required for `asyncio.TaskGroup` and `except*`)
- LSEG RDP credentials:
  - Machine ID
  - Password
  - AppKey

If you do not have access yet, contact your LSEG representative or account manager.

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create your environment file by creating `src/.env` with the following content:

```dotenv
RDP_BASE_URL=https://api.refinitiv.com

MACHINEID_RDP=<RDP Machine-ID>
PASSWORD_RDP=<RDP Password>
APPKEY_RDP=<RDP AppKey>
```

## Run

```powershell
# Synchronous
python .\src\example_client.py

# Async — sequential loop
python .\src\example_async_simple.py

# Async — concurrent via asyncio.gather()
python .\src\example_async_gather.py

# Async — concurrent via asyncio.TaskGroup
python .\src\example_async_taskgroup.py
```

Each script prints the authenticated request URLs and JSON responses. Timing is printed on exit for the async scripts.

## Security Notes

- All examples use `verify=False` to disable TLS certificate verification. This is intended for local/dev environments only (e.g. where a TLS-inspecting proxy such as ZScaler is in use). Remove `verify=False` or supply a proper CA bundle for production use.
- Do not log or print access tokens in production applications.

## License

Apache 2.0. See [LICENSE.md](LICENSE.md).

## References

- https://realpython.com/async-io-python/
- https://www.twilio.com/en-us/blog/asynchronous-http-requests-in-python-with-httpx-and-asyncio
- https://docs.python.org/3/library/asyncio-task.html#task-groups

