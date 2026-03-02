import os
import sys
import time
import httpx
from dotenv import load_dotenv

def authenticate_rdp(machine_id, password, app_key, url) -> dict:
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
    # `verify=False` skips SSL verification (for local/dev only).
    response = httpx.post(url, data=payload, verify=False)
    response.raise_for_status()  # Raise an exception for 4xx/5xx HTTP errors
    return response.json()

def get_chain(ric, token, url) -> dict:
    """Fetch chain data for a single RIC symbol using an access token."""
    # Bearer token is required for authorized API requests.
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Query string parameters sent with the GET request.
    parameters = {
        "universe": ric
    }
    # Request chain data from the pricing chains endpoint.
    response = httpx.get(url, params=parameters, headers=headers, verify=False)
    response.raise_for_status()  # Raise an exception for 4xx/5xx HTTP errors
    return response.json()

def post_historical_event(rics, token, url) -> dict:
    """Request historical event data for multiple RICs."""
    # Send the token in Authorization header for API access.
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # JSON body for the historical pricing events request.
    payload = {
        "universe": rics,
        "eventTypes": ["trade"]
    }

    # `json=payload` serializes and sends JSON in the request body.
    response = httpx.post(url, json=payload, headers=headers, verify=False)
    response.raise_for_status()  # Raise an exception for 4xx/5xx HTTP errors
    return response.json()  

def post_authen_refresh(appkey, refresh_token,url) -> dict:
    """Refresh the access token using the refresh token."""
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": appkey,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = httpx.post(url, data=payload, headers=headers, verify=False)
    response.raise_for_status()  # Raise an exception for 4xx/5xx HTTP errors
    return response.json()

def post_authen_revoke(token, appkey, url) -> None:
    """Revoke the access token to end the session."""
    headers = {            
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = f"token={token}"
    auth = httpx.BasicAuth(username=appkey, password="")

    response = httpx.post(url, data=payload, headers=headers, auth=auth, verify=False)
    response.raise_for_status()

def main() -> None:
    """Run the end-to-end demo: auth, chain data, and historical events."""
    # Load key/value pairs from src/.env into process environment.
    load_dotenv()

    # Read credentials and base URL from environment variables.
    machine_id = os.getenv("MACHINEID_RDP")
    password = os.getenv("PASSWORD_RDP")
    app_key = os.getenv("APPKEY_RDP")
    base_url = os.getenv("RDP_BASE_URL")  # Default to Refinitiv API base URL if not set

    # OAuth token endpoint used to obtain access token.
    auth_url = f"{base_url}/auth/oauth2/v1/token"
    
    try:
        token_data = authenticate_rdp(machine_id, password, app_key, auth_url)
        print("Authentication successful! Status code: 200")
        # For demos only: print token to verify auth worked.
        print(token_data["access_token"])
    except httpx.HTTPStatusError as e:
        # HTTP error response received (e.g. 400 Bad Request, 401 Unauthorized)
        print(f"HTTP error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        # Network-level error (e.g. connection refused, DNS failure, timeout)
        print(f"Request error: {e}")

    # Continue only when an access token is available.
    if token_data["access_token"]:
       
        print("Access token received successfully.")
        # Example single RIC lookup for chain endpoint using HTTP GET.
        RIC = "KIBOR="
        chain_url = f"{base_url}/data/pricing/chains/v1/"
        try:
            print(f"Fetching chain data... for RIC: {RIC}")
            chain_data = get_chain(RIC, token_data["access_token"], chain_url)
            print("Chain data retrieved successfully!")
            print(chain_data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP error while fetching chain data: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Request error while fetching chain data: {e}")

        # Example multi-RIC request for historical events endpoint using HTTP POST.
        RICs = ["LSEG.L","VOD.L","BP.L"]
        historical_event_url = f"{base_url}/data/historical-pricing/v1/views/events"
        try:
            print(f"Posting historical event data... for RICs: {RICs}")
            historical_event_data = post_historical_event(RICs, token_data["access_token"], historical_event_url)
            print("Historical event data posted successfully!")
            print(historical_event_data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP error while posting historical event data: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Request error while posting historical event data: {e}")

        time.sleep(5)  # Sleep for 5 seconds before refreshing token (for demo purposes)
        try:
            refresh_token = token_data.get("refresh_token")
            if refresh_token:
                print("Refreshing access token...")
                refreshed_token_data = post_authen_refresh(app_key, refresh_token, auth_url)
                print("Access token refreshed successfully!")
                print(f" New Access Token: {refreshed_token_data['access_token']}")
            else:
                print("No refresh token available. Skipping token refresh.")
        except httpx.HTTPStatusError as e_refresh:
            print(f"HTTP error while refreshing token: {e_refresh.response.status_code} - {e_refresh.response.text}")
        except httpx.RequestError as e_refresh:
            print(f"Request error while refreshing token: {e_refresh}")

        time.sleep(5)  # Sleep for 5 seconds before revoking token (for demo purposes)
        revoke_url = f"{base_url}/auth/oauth2/v1/revoke"
        try:
            print("Revoking access token...")
            post_authen_revoke(token_data["access_token"], app_key, revoke_url)
            print("Access token revoked successfully.")
        except httpx.HTTPStatusError as e_revoke:
            print(f"HTTP error while revoking token: {e_revoke.response.status_code} - {e_revoke.response.text}")
        except httpx.RequestError as e_revoke:
            print(f"Request error while revoking token: {e_revoke}")
    else:
        print("Failed to receive access token. Exiting...")
        sys.exit(1) 


if __name__ == "__main__":
    main()