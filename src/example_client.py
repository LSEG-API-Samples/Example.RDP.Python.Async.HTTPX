import json
import os
import time

import httpx
from dotenv import load_dotenv


AUTH_TOKEN_URL = "/auth/oauth2/v1/token"
AUTH_REVOKE_URL = "/auth/oauth2/v1/revoke"
HISTORICAL_INTERDAY_SUMMARIES_URL = "/data/historical-pricing/v1/views/interday-summaries/"
HISTORICAL_RICS = ["NVDA.O","AAPL.O","MSFT.O","AMZN.O","GOOG.O","AVGO.O","META.O","ORCL.N","IBM.N","PLTR.O","NFLX.O","TSLA.O","CRM.N","AMD.O","INTC.O","ARM.O","ASML.AS","CSCO.O","WMT.O","LLY.N","JPM.N","XOM.N","V.N","JNJ.N","MU.O","MA.N","COST.O","CVX.N","BAC.N","CAT.N"] # Fetched sequentially


def _bearer_headers(token) -> dict[str, str]:
    """Build common JSON headers with bearer auth."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _require_env(name) -> str:
    """Read a required environment variable or fail early with a clear message."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def post_authentication(machine_id, password, app_key, url, client):
    """Authenticate to RDP and return the token response as JSON."""

    # Build the OAuth 2.0 Password Grant request payload.
    # Sent as application/x-www-form-urlencoded (httpx encodes a dict automatically).
    payload = {
        "username": machine_id,           # RDP Machine-ID
        "password": password,             # RDP Password
        "grant_type": "password",         # OAuth 2.0 grant type
        "scope": "trapi",                 # Target API scope
        "takeExclusiveSignOnControl": "true",  # Revoke other active sessions
        "client_id": app_key              # RDP AppKey (acts as client_id)
    }

    # Send authentication request to the OAuth token endpoint.
    # `data=payload` sends a form body required by this endpoint.
    response = client.post(url, data=payload)
    response.raise_for_status()  # Raise for 4xx/5xx API failures.
    return response.json()


def get_chain(ric, token, url, client):
    """Fetch chain data for a single RIC symbol using an access token."""
    headers = _bearer_headers(token)
    # Query string parameters sent with the GET request.
    parameters = {
        "universe": ric
    }
    # Request chain data from the pricing chains endpoint.
    response = client.get(url, params=parameters, headers=headers)
    response.raise_for_status()
    return response.json()


def post_historical_event(rics, token, url, client):
    """Request historical event data for multiple RICs."""
    headers = _bearer_headers(token)
    # JSON body for the historical pricing events request.
    payload = {
        "universe": rics,
        "eventTypes": ["trade"]
    }

    # `json=payload` serializes and sends JSON in the request body.

    response = client.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def get_historical_interday_summaries(ric, token, url, client, interval, start, end, fields):
    """Request historical Interday summaries data for a single RIC."""
    print(f"Fetching historical interday summaries... for RIC: {ric}")

    # Bearer token authenticates the caller; Content-Type signals a JSON response is expected.
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Build the query string for the interday-summaries endpoint.
    # adjustments: apply standard corporate-action and price corrections so that
    # the returned series is comparable across the full date range.
    # fields: comma-separated list of data columns to include in the response.
    params = {
        "interval": interval,
        "start": start,
        "end": end,
        "adjustments": "exchangeCorrection,manualCorrection,CCH,CRE,RPO,RTS",
        "fields": ",".join(fields)
    }

    response_history =  client.get(f"{url}{ric}", params=params, headers=headers)

    print(f"Request URL: {response_history.url}")

    # Raise an exception for 4xx/5xx HTTP errors; lets the caller handle
    # status-specific logic (e.g. 429 rate-limit vs. 401 auth failure).
    response_history.raise_for_status()

    # Deserialise and return the JSON payload for further processing by the caller.
    return response_history.json()


def post_auth_revoke(token, app_key, url, client):
    """Revoke the access token to end the session."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = f"token={token}"
    auth = httpx.BasicAuth(username=app_key, password="")
    response = client.post(url, data=payload, headers=headers, auth=auth)
    response.raise_for_status()


def main() -> None:
    """Run the end-to-end demo: auth, chain data, and historical events."""
    # Load key/value pairs from src/.env into process environment.
    load_dotenv()

    # Read credentials and base URL from environment variables.
    machine_id = _require_env("MACHINEID_RDP")
    password = _require_env("PASSWORD_RDP")
    app_key = _require_env("APPKEY_RDP")
    base_url = _require_env("RDP_BASE_URL")

    # Reuse one connection pool across all requests.
    # `verify=False` skips SSL verification (for local/dev only). This is not recommended for production use. I use it to avoid LSEG beloved ZScaler.
    client = httpx.Client(
        verify=False,
        base_url=base_url,
        timeout=10.0,
        default_encoding="utf-8",
        follow_redirects=True,
    )

    try:
        token_data = post_authentication(machine_id, password, app_key, AUTH_TOKEN_URL, client)
        print("Authentication successful. Access token obtained.")
        access_token = token_data.get("access_token")
        
        # Fetch historical interday summaries for each RIC sequentially.
        # For better performance with many RICs, consider concurrent requests (e.g. using asyncio or threading).
        start_time = time.perf_counter()
        print("Start the wall-clock timer...")
        field_list = ["TRDPRC_1", "BID", "ASK"]
        start_date = "2025-11-01T00:00:00Z"
        end_date = "2026-02-28T23:59:59Z"
        
        for ric in HISTORICAL_RICS:
            history_data =  get_historical_interday_summaries(
                ric, access_token, HISTORICAL_INTERDAY_SUMMARIES_URL, client, interval="P1D", start=start_date, end=end_date, fields=field_list
            )
            print("Historical interday summaries retrieved successfully!")
            print(f"Historical interday summaries for '{ric}': {history_data}\n\n")
        
        elapsed = time.perf_counter() - start_time
        print(f"{__file__} executed in {elapsed:0.2f} seconds.")
        print(f"simple_call_nb.ipynb executed for ({len(HISTORICAL_RICS)} RICs) in {elapsed:0.2f} seconds.")

        time.sleep(1)  # Sleep briefly to ensure all requests are completed before revoking the token.
        print("Revoking access token...")
        post_auth_revoke(access_token, app_key, AUTH_REVOKE_URL, client)
        print("Access token revoked successfully.\n")
    except httpx.HTTPStatusError as exc:
        print(f"HTTP error occurred during HTTP Request: {exc.request.url}: {exc.response.status_code} - {exc.response.text}")
    except httpx.RequestError as exc:
        print(f"An error occurred during HTTP Request: {exc.request.url}: {exc}")
    except ValueError as exc:
        print(f"Configuration error: {exc}")
    except KeyError as exc:
        print(f"An error occurred during HTTP Request: {exc}")
    finally:
        client.close()


if __name__ == "__main__":
    main()