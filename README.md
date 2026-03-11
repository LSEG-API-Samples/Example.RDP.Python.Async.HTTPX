# RDP_HTTPX

Small Python examples that use [`httpx`](https://www.python-httpx.org/) to authenticate with [LSEG Data Platform APIs](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis) (RDP, also known as Delivery Platform)  using OAuth2 Password Grant, then call sample REST endpoints.

## Included Scripts

- `src/example_sync_httpx.py`
  - Synchronous (blocking) requests with direct `httpx` calls.
  - Demonstrates:
    - `POST /auth/oauth2/v1/token`
    - `GET /data/pricing/chains/v1/`
    - `POST /data/historical-pricing/v1/views/events`
    - Refresh token flow (`grant_type=refresh_token`)
    - `POST /auth/oauth2/v1/revoke`

- `src/example_client.py`
  - Synchronous (blocking) script using one shared `httpx.Client` (connection pooling + shared config).
  - Includes simple environment validation and reusable helper methods.
  - Demonstrates the same endpoint flow as above.

## Prerequisites

- Python 3.10+
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

3. Create your environment file.

Copy `src/.env.example` to `src/.env` and fill in values:

```dotenv
RDP_BASE_URL=https://api.refinitiv.com

MACHINEID_RDP=<RDP Machine-ID>
PASSWORD_RDP=<RDP Password>
APPKEY_RDP=<RDP AppKey>
```

## Run

```powershell
python .\src\example_sync_httpx.py
```

```powershell
python .\src\example_client.py
```

For demo purposes, scripts print token/output payloads and endpoint responses.

## Security Notes

- The examples currently use `verify=False`, which disables TLS certificate verification.
- This is not safe for production. Remove `verify=False` (or provide a proper CA bundle) for real usage.
- Avoid printing access tokens in production applications/logs.

## License

Apache 2.0. See [LICENSE.md](LICENSE.md).

## Reference

- https://realpython.com/async-io-python/
- https://www.twilio.com/en-us/blog/asynchronous-http-requests-in-python-with-httpx-and-asyncio

