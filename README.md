# RDP_HTTPX

Small Python example that uses [`httpx`](https://www.python-httpx.org/) to authenticate with the Refinitiv Data Platform (RDP) OAuth2 **Password Grant** flow and call a couple of RDP REST endpoints.

## What’s included

- `src/example_sync_httpx.py` – synchronous (blocking) demo script that:
  - Authenticates: `POST /auth/oauth2/v1/token`
  - Calls Pricing Chains: `GET /data/pricing/chains/v1/`
  - Calls Historical Pricing Events: `POST /data/historical-pricing/v1/views/events`
  - Refreshes token (refresh_token grant)
  - Revokes token: `POST /auth/oauth2/v1/revoke`

## Prerequisites

- Python 3.10+ recommended
- RDP credentials:
  - **Machine ID**
  - **Password**
  - **AppKey**

## Setup

1) Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies.

```powershell
pip install -r requirements.txt
```

3) Create your environment file.

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

The script prints the access token (demo only), then prints the JSON responses from the sample endpoints.

## Security notes

The example uses `verify=False` in `httpx` calls, which **disables TLS certificate verification**. This is unsafe for production—remove `verify=False` (or provide a proper CA bundle) for real usage. I use it in this project to avoid LSEG beloved ZScaler.

Also avoid printing access tokens in real applications.

## License

Apache 2.0 — see [LICENSE.md](LICENSE.md).
