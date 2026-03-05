import json
import os
import time
from typing import Any, Sequence

import httpx
from dotenv import load_dotenv


AUTH_TOKEN_URL = "/auth/oauth2/v1/token"
AUTH_REVOKE_URL = "/auth/oauth2/v1/revoke"
CHAIN_URL = "/data/pricing/chains/v1/"
HISTORICAL_EVENT_URL = "/data/historical-pricing/v1/views/events"


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
    # `verify=False` skips SSL verification (for local/dev only). This is not recommended for production use. I use it to avoid LSEG beloved ZScaler.
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
    # `verify=False` skips SSL verification (for local/dev only). This is not recommended for production use. I use it to avoid LSEG beloved ZScaler.
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
    # `verify=False` skips SSL verification (for local/dev only). This is not recommended for production use. I use it to avoid LSEG beloved ZScaler.
    response = client.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def post_auth_refresh(app_key, refresh_token, url, client):
    """Refresh the access token using the refresh token."""
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": app_key,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    # `verify=False` skips SSL verification (for local/dev only). This is not recommended for production use. I use it to avoid LSEG beloved ZScaler.
    response = client.post(url, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def post_auth_revoke(token, app_key, url, client):
    """Revoke the access token to end the session."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = f"token={token}"
    auth = httpx.BasicAuth(username=app_key, password="")
    # `verify=False` skips SSL verification (for local/dev only). This is not recommended for production use. I use it to avoid LSEG beloved ZScaler.
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
        if access_token:
            print("Access Token:", json.dumps(access_token, indent=2))

            ric = "EFX="
            print(f"Fetching chain data... for RIC: {ric}")
            chain_data = get_chain(ric, access_token, CHAIN_URL, client)
            print("Chain data retrieved successfully!")
            print(f"Chain data for {ric}:", json.dumps(chain_data, indent=2))

            # Example multi-RIC request for historical events endpoint.
            rics = ["LSEG.L", "VOD.L", "BP.L"]
            print(f"Posting historical event data... for RICs: {rics}")
            historical_event_data = post_historical_event(rics, access_token, HISTORICAL_EVENT_URL, client)
            print("Historical event data retrieved successfully!")
            print(f"Historical event data for {rics}:", json.dumps(historical_event_data))

            refresh_token = token_data.get("refresh_token")
            if refresh_token:
                time.sleep(5)  # Sleep for 5 seconds before refreshing token (for demo purposes)
                print("Refreshing access token...")
                refreshed_token_data = post_auth_refresh(app_key, refresh_token, AUTH_TOKEN_URL, client)
                print("Token refreshed successfully!")
                print("New Access Token:", json.dumps(refreshed_token_data["access_token"], indent=2))
            else:
                print("No refresh token available. Cannot refresh access token.")

            time.sleep(5)  # Sleep for 5 seconds before revoking token (for demo purposes)
            print("Revoking access token...")
            post_auth_revoke(access_token, app_key, AUTH_REVOKE_URL, client)
            print("Access token revoked successfully.")

        else:
            print("Failed to receive access token. Exiting...")
            return
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