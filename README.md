# Data Platform APIs HTTP REST Application using HTTPX

- Version: 1.0
- Last update: Mar 2026
- Environment: Python + JupyterLab + Data Platform Account
- Prerequisite: Data Platform access/entitlements

Python examples that use [`httpx`](https://www.python-httpx.org/) to authenticate with [LSEG Data Platform APIs](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis) (RDP, also known as Delivery Platform) using OAuth 2.0 Password Grant, then call sample REST endpoints — covering both synchronous and asynchronous patterns.

## What is Data Platform APIs?

[LSEG Data Platform](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis) (RDP APIs, also known as Delivery Platform in LSEG Real-Time) provides simple web based API access to a broad range of LSEG content.

RDP APIs give developers seamless and holistic access to all of the LSEG content such as Historical Pricing, Environmental Social and Governance (ESG), News, Research, etc, and commingled with their content, enriching, integrating, and distributing the data through a single interface, delivered wherever they need it.  The RDP APIs delivery mechanisms are the following:
* Request - Response: RESTful web service (HTTP GET, POST, PUT or DELETE) 
* Alert: delivery is a mechanism to receive asynchronous updates (alerts) to a subscription. 
* Bulks:  deliver substantial payloads, like the end-of-day pricing data for the whole venue. 
* Streaming: deliver real-time delivery of messages.

This example project is focusing on the Request-Response: RESTful web service delivery method only.  

For more detail regarding the Data Platform, please see the following APIs resources: 
- [Quick Start](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/quick-start) page.
- [Tutorials](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/tutorials) page.
- [RDP APIs: Introduction to the Request-Response API](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/tutorials#introduction-to-the-request-response-api) page.

## What is HTTPX?

[HTTPX](https://www.python-httpx.org/) is a full featured modern HTTP client for Python 3. It provides a set of synchronous and modern asynchronous APIs with [HTTP/2](https://httpwg.org/specs/rfc7540.html) supported. Any Python developers who are using the [Requests](https://requests.readthedocs.io/en/latest/) library can migrate to the HTTPX library easily with their [requests-compatibility API interfaces](https://www.python-httpx.org/compatibility/) like the following examples:

**HTTP GET**

```python
import httpx

params = {'key1': 'value1', 'key2': 'value2'}
r = httpx.get('https://httpbin.org/get', params=params)
r.raise_for_status()
print(r.json())
```

**HTTP POST**

```python
import httpx

data = {'integer': 123, 'boolean': True, 'list': ['a', 'b', 'c']}
r = httpx.post('https://httpbin.org/post', json=data)
r.raise_for_status()
print(r.json())
```

HTTPX also provides [`httpx.Client`](https://www.python-httpx.org/advanced/clients/) object (equivalent to [`requests.Session()`](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects) object in the [Requests library](https://requests.readthedocs.io/en/latest/)) as synchronous HTTP client for developers. 

Example:

```python
import httpx

with httpx.Client(base_url='http://httpbin.org') as client:
  r = client.get('/get')
  r.raise_for_status()
  print(r.status_code)
```

The asynchronous execute model examples, the library offers [`httpx.AsyncClient`](https://www.python-httpx.org/api/#asyncclient) as an asynchronous HTTP client to use with Python asynchronous library such as a [built-in asyncio](https://docs.python.org/3/library/asyncio.html), [Trio](https://trio.readthedocs.io/en/stable/), and [AnyIO](https://anyio.readthedocs.io/en/stable/) libraries. I am demonstrating with asyncio in this project.

Example:

```python
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        response = await client.get('https://www.example.com/')
        print(response)

asyncio.run(main())
```

## Project Structure

```
├── requirements.txt             # Pinned dependencies
src/
├── .env.example                 # Environment variable template
├── sync_call_nb.ipynb         # Jupyter notebook — synchronous, shared httpx.Client
├── async_call_nb.ipynb          # Jupyter notebook — async, asyncio.gather() with Semaphore
├── example_sync_httpx.py        # Synchronous — direct httpx module calls (no shared client)
├── example_client.py            # Synchronous — shared httpx.Client
└── example_async_gather.py      # Async — asyncio.gather() with Semaphore
```

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

### `src/example_sync_httpx.py` — Synchronous, direct `httpx` calls

Simplest synchronous example. Each function calls `httpx.get()` / `httpx.post()` directly — no shared client or connection pool. Good as a minimal reference or quick script.

Demonstrates:
- `POST /auth/oauth2/v1/token` — OAuth 2.0 Password Grant authentication
- `GET /data/pricing/chains/v1/` — chain constituent lookup for a single RIC
- `POST /data/historical-pricing/v1/views/events` — historical trade events for multiple RICs
- Refresh token flow (`grant_type=refresh_token`)
- `POST /auth/oauth2/v1/revoke` — session revocation using HTTP Basic Auth
- Per-call `verify=False` passed directly to each `httpx` function

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
# Jupyter notebook (synchronous)
jupyter lab src/simple_call_nb.ipynb

# Jupyter notebook (async — asyncio.gather)
jupyter lab src/async_call_nb.ipynb

# Synchronous
python .\src\example_client.py

# Async — concurrent via asyncio.gather()
python .\src\example_async_gather.py
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

