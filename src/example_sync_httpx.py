"""Example code demonstrating how to use httpx to authenticate and call RDP APIs with standalone httpx.get and httpx.post calls."""
import os
import time

import httpx
from dotenv import load_dotenv


AUTH_TOKEN_URL = "/auth/oauth2/v1/token"
AUTH_REVOKE_URL = "/auth/oauth2/v1/revoke"
HISTORICAL_INTERDAY_SUMMARIES_URL = "/data/historical-pricing/v1/views/interday-summaries/"
HISTORICAL_RICS = ["AAPL.O","MSFT.O","META.O","NVDA.O","GOOG.O","ORCL.N","IBM.N","PLTR.O","AMZN.O","AVGO.O","TSLA.O","CRM.N","AMD.O","INTC.O","CSCO.O"]  # Fetched sequentially


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


def post_authentication(machine_id, password, app_key, url):
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
    # `verify=False` skips SSL verification (for local/dev only). Not recommended for production.
    response = httpx.post(url, data=payload, verify=False)
    response.raise_for_status()  # Raise for 4xx/5xx API failures.
    return response.json()

def get_historical_interday_summaries(ric, token, url, interval, start, end, fields):
    """Request historical Interday summaries data for a single RIC."""
    print(f"Fetching historical interday summaries... for RIC: {ric}")

    headers = _bearer_headers(token)

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

    response_history = httpx.get(f"{url}{ric}", params=params, headers=headers, verify=False)

    print(f"Request URL: {response_history.url}")

    # Raise an exception for 4xx/5xx HTTP errors; lets the caller handle
    # status-specific logic (e.g. 429 rate-limit vs. 401 auth failure).
    response_history.raise_for_status()

    # Deserialise and return the JSON payload for further processing by the caller.
    return response_history.json()


def post_auth_revoke(token, app_key, url):
    """Revoke the access token to end the session."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = f"token={token}"
    auth = httpx.BasicAuth(username=app_key, password="")
    response = httpx.post(url, data=payload, headers=headers, auth=auth, verify=False)
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

    try:
        token_data = post_authentication(machine_id, password, app_key, f"{base_url}{AUTH_TOKEN_URL}")
        print("Authentication successful. Access token obtained.")
        access_token = token_data.get("access_token")

        # Fetch historical interday summaries for each RIC sequentially.
        # For better performance with many RICs, consider concurrent requests (e.g. using asyncio or threading).
        fields = ["TRDPRC_1", "BID", "ASK"]
        start_date = "2025-11-01T00:00:00Z"
        end_date = "2026-02-28T23:59:59Z"

        for ric in HISTORICAL_RICS:
            history_data = get_historical_interday_summaries(
                ric, access_token, f"{base_url}{HISTORICAL_INTERDAY_SUMMARIES_URL}", interval="P1D", start=start_date, end=end_date, fields=fields
            )
            print("Historical interday summaries retrieved successfully!")
            print(f"Historical interday summaries for '{ric}': {history_data}\n\n")

        time.sleep(1)  # Sleep briefly to ensure all requests are completed before revoking the token.
        print("Revoking access token...")
        post_auth_revoke(access_token, app_key, f"{base_url}{AUTH_REVOKE_URL}")
        print("Access token revoked successfully.\n")
    except httpx.HTTPStatusError as exc:
        print(f"HTTP error occurred during HTTP Request: {exc.request.url}: {exc.response.status_code} - {exc.response.text}")
    except httpx.RequestError as exc:
        print(f"An error occurred during HTTP Request: {exc.request.url}: {exc}")
    except ValueError as exc:
        print(f"Configuration error: {exc}")
    except KeyError as exc:
        print(f"An error occurred during HTTP Request: {exc}")


if __name__ == "__main__":
    start = time.perf_counter()
    main()
    elapsed = time.perf_counter() - start
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")