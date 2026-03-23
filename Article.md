# Data Platform APIs HTTP REST Application using Httpx

- Version: 1.0
- Last update: Mar 2026
- Environment: Python + JupyterLab + Data Platform Account
- Prerequisite: Data Platform access/entitlements

## Overview

The [Requests](https://requests.readthedocs.io/en/latest/) library is widely regarded as *the de facto* standard HTTP client for Python applications. Many Python developers first learn REST API calls through Requests — including through our [Data Platform APIs Tutorials](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/tutorials) (or you can try RDP HTTP operations with the [built-in http.client](https://docs.python.org/3/library/http.client.html) if you enjoy a challenge.).

That said, there are other Python HTTP libraries worth considering — [HTTPX](https://www.python-httpx.org/), [Aiohttp](https://docs.aiohttp.org/en/stable/), [Urllib3](https://urllib3.readthedocs.io/en/stable/), [Grequests](https://pypi.org/project/grequests/), [PycURL](http://pycurl.io/docs/latest/index.html), and more — each offering different trade-offs in performance and features that may better suit your requirements.

I was drawn to HTTPX because it provides a **requests-compatible API** while also supporting **asynchronous operations** out of the box. That combination made migrating from Requests to HTTPX straightforward, with the added benefit of async support when needed.

This project demonstrates how to use [`httpx`](https://www.python-httpx.org/) to authenticate and retrieve data from [LSEG Data Platform APIs](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis) via HTTP endpoints — covering both synchronous and asynchronous patterns for comparison.

**Note**: A basic knowledge of Python [built-in asyncio](https://docs.python.org/3/library/asyncio.html) library is required to understand example codes.

## Included Notebook

### `src/sync_call_nb.ipynb` — Synchronous, step-by-step Jupyter notebook

Interactive notebook version of the synchronous workflow. Each logical step is a separate cell with a markdown explanation above it, making it easy to run and inspect results incrementally.

Demonstrates:
- `POST /auth/oauth2/v1/token` — OAuth 2.0 Password Grant authentication
- `GET /data/historical-pricing/v1/views/interday-summaries/{ric}` — daily OHLCV data with corporate-action adjustments for 10 RICs
- `POST /auth/oauth2/v1/revoke` — session token revocation using HTTP Basic Auth
- Shared `httpx.Client` inside a `with` block for clean connection-pool teardown
- Wall-clock timing across the full workflow

Notebook structure:
1. Imports
2. Constants (endpoint paths, RIC list)
3. Credentials loaded from `src/.env`
4. Helper functions (`post_authentication`, `post_auth_revoke`, `get_historical_interday_summaries`)
5. Main execution block — authenticate, fetch data sequentially, revoke token
6. Elapsed time output

### `src/async_call_nb.ipynb` — Async, concurrent Jupyter notebook (`asyncio.gather`)

Interactive notebook version of the async concurrent workflow using `httpx.AsyncClient` and `asyncio.gather()`. Jupyter's native top-level `await` support means no `asyncio.run()` wrapper is needed.

Demonstrates:
- `POST /auth/oauth2/v1/token` — async OAuth 2.0 Password Grant authentication
- `GET /data/historical-pricing/v1/views/interday-summaries/{ric}` — daily OHLCV data fetched concurrently for 10 RICs
- `asyncio.Semaphore` — caps concurrent in-flight requests (default: 3) to respect server rate limits
- `asyncio.gather(return_exceptions=True)` — all RIC coroutines run simultaneously; one failure does not cancel the rest
- Per-result error inspection: `httpx.HTTPStatusError`, `httpx.RequestError`, generic `Exception`
- `async with httpx.AsyncClient` — shared connection pool, closed cleanly on exit
- Wall-clock timing across the full workflow

Notebook structure:
1. Imports
2. Constants (endpoint paths, RIC list)
3. Credentials loaded from `src/.env`
4. Helper functions (`post_authentication`, `post_auth_revoke`, `get_historical_interday_summaries`)
5. Main execution block — authenticate, gather concurrent RIC fetches, per-result error handling
6. Elapsed time output

## Included Scripts

### `src/example_async_gather.py` — Async with `asyncio.gather()` and `Semaphore`

Async script that fires all RIC requests concurrently via `asyncio.gather()`, with an `asyncio.Semaphore` to cap the number of in-flight requests and avoid hitting server rate limits.

Demonstrates:
- `POST /auth/oauth2/v1/token` — async authentication
- `GET /data/historical-pricing/v1/views/interday-summaries/{ric}` — concurrent fetches for 10 RICs
- `asyncio.Semaphore` — limits concurrent requests (default: 3)
- `return_exceptions=True` — prevents one failure from cancelling the rest; each result is inspected individually
- Per-result error handling: `httpx.HTTPStatusError`, `httpx.RequestError`, generic `Exception`

### `src/example_client.py` — Synchronous with shared client

Synchronous (blocking) script using a single shared `httpx.Client` instance for connection pooling and consistent configuration across all requests.

Demonstrates:
- `POST /auth/oauth2/v1/token` — OAuth 2.0 Password Grant authentication
- `GET /data/pricing/chains/v1/` — chain constituent lookup
- `POST /data/historical-pricing/v1/views/events` — historical trade events for multiple RICs (commented out, ready to enable)
- Refresh token flow (`grant_type=refresh_token`) — commented out, ready to enable
- `POST /auth/oauth2/v1/revoke` — session revocation — commented out, ready to enable
- Environment validation with a `_require_env()` helper that fails fast on missing credentials

## Security Notes

- All examples use `verify=False` to disable TLS certificate verification. This is intended for local/dev environments only (e.g. where a TLS-inspecting proxy such as ZScaler is in use). Remove `verify=False` or supply a proper CA bundle for production use.
- Do not log or print access tokens in production applications.