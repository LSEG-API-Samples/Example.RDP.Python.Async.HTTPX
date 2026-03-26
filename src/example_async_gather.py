import asyncio
import os
import time
import httpx
from dotenv import load_dotenv

AUTH_TOKEN_URL = "/auth/oauth2/v1/token"
AUTH_REVOKE_URL = "/auth/oauth2/v1/revoke"
HISTORICAL_INTERDAY_SUMMARIES_URL = "/data/historical-pricing/v1/views/interday-summaries/"

HISTORICAL_RICS = ["NVDA.O","AAPL.O","MSFT.O","AMZN.O","GOOG.O","AVGO.O","META.O","ORCL.N","IBM.N","PLTR.O","NFLX.O","TSLA.O","CRM.N","AMD.O","INTC.O","ARM.O","ASML.AS","CSCO.O","WMT.O","LLY.N","JPM.N","XOM.N","V.N","JNJ.N","MU.O","MA.N","COST.O","CVX.N","BAC.N","CAT.N"] # Fetched concurrently

MAX_CONCURRENT_TASKS = 10
async def post_authentication_async(machine_id, password, app_key, url, client):
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

    headers = {
        "Content-Type": "application/x-www-form-urlencoded" 
    }

    # Send authentication request to the OAuth token endpoint.
    # `data=payload` sends a form body required by this endpoint.
    response_auth = await client.post(url, data=payload, headers=headers)
    response_auth.raise_for_status()  # Raise for 4xx/5xx API failures.
    return response_auth.json()

async def post_auth_revoke_async(token, app_key, url, client):
    """Revoke the access token to end the session."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = f"token={token}"
    auth = httpx.BasicAuth(username=app_key, password="")
    response = await client.post(url, data=payload, headers=headers, auth=auth)
    response.raise_for_status()


async def get_historical_interday_summaries_async(ric, token, url, client, interval, start, end, fields, semaphore=None):
    """Request historical Interday summaries data for a single RIC.
    """
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

    # Acquire the semaphore slot before sending the request so that at most
    # `semaphore._value` (e.g. 3) requests are in-flight at the same time. Pass None to run without rate-limiting.
    # When no semaphore is provided, send the request immediately without throttling.
    if semaphore:
        async with semaphore:
            response_history = await client.get(f"{url}{ric}", params=params, headers=headers)
    else:
        response_history = await client.get(f"{url}{ric}", params=params, headers=headers)

    print(f"Request URL: {response_history.url}")

    # Raise an exception for 4xx/5xx HTTP errors; lets the caller handle
    # status-specific logic (e.g. 429 rate-limit vs. 401 auth failure).
    response_history.raise_for_status()

    # Deserialise and return the JSON payload for further processing by the caller.
    return response_history.json()



async def main():
    """Main entry point for the async example."""
    load_dotenv()

    # Read credentials and base URL from environment variables.
    machine_id = os.getenv("MACHINEID_RDP")
    password = os.getenv("PASSWORD_RDP")
    app_key = os.getenv("APPKEY_RDP")
    base_url = os.getenv("RDP_BASE_URL")

    # Reuse one connection pool across all requests.
    # `verify=False` skips SSL verification (for local/dev only). This is not recommended for production use. I use it to avoid LSEG beloved ZScaler.
    async with httpx.AsyncClient(
        verify=False,
        base_url=base_url,
        timeout=10.0,
        follow_redirects=True,
    ) as client:
        # --- Authentication (must complete before any data requests) ---
        try:
            token_data = await post_authentication_async(machine_id, password, app_key, AUTH_TOKEN_URL, client)
            print("Authentication successful. Access token obtained.")

            access_token = token_data.get("access_token")
            
            start_time = time.perf_counter()
            print("Start the wall-clock timer...")
            fields_list  = ["TRDPRC_1", "BID", "ASK"]
            start = "2025-11-01T00:00:00Z"
            end = "2026-02-28T23:59:59Z"

            # Limit how many RIC requests run simultaneously to avoid
            # overwhelming the server or hitting rate limits.
            sem = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
            
            # Build one coroutine per RIC; the semaphore inside get_chain
            # ensures at most MAX_CONCURRENT_TASKS run at the same time.
            tasks_history = [get_historical_interday_summaries_async(ric, access_token, HISTORICAL_INTERDAY_SUMMARIES_URL, client, interval="P1D", start=start, end=end, fields=fields_list, semaphore=sem) for ric in HISTORICAL_RICS]

            # gather() runs all tasks concurrently. return_exceptions=True
            # prevents a single failure from cancelling the remaining tasks —
            # each exception is returned as a value instead of being raised.
            results_history = await asyncio.gather(*tasks_history, return_exceptions=True)
            # Pair each RIC with its result (or exception) and handle individually.
            for ric, result in zip(HISTORICAL_RICS, results_history):
                if isinstance(result, httpx.HTTPStatusError):
                    raise result  # 4xx / 5xx HTTP response
                elif isinstance(result, httpx.RequestError):
                    raise result  # network-level failure (includes timeouts)
                elif isinstance(result, Exception):
                    raise result  # any other unexpected error
                print(f"Historical interday summaries for '{ric}': {result}\n\n")

            elapsed = time.perf_counter() - start_time
            print(f"{__file__} executed for {len(HISTORICAL_RICS)} RICs (with throttling {MAX_CONCURRENT_TASKS}) in {elapsed:0.2f} seconds.")

        # --- Exception handlers ordered from most-specific to least-specific ---
        except httpx.HTTPStatusError as e:
            # Server returned a 4xx or 5xx status code.
            print(f"HTTP error during request: {e.request.url} {e.response.status_code} - {e.response.text}")
            return
        except httpx.TimeoutException as e:
            # Request exceeded the configured timeout (must precede RequestError
            # because TimeoutException is a subclass of RequestError).
            print(f"Timeout error: {e}")
            return
        except httpx.RequestError as e:
            # Network-level failure: DNS, connection refused, SSL error, etc.
            print(f"Network error: {e}")
            return
        except Exception as e:
            # Catch-all for unexpected errors (e.g. JSON decode, assertion).
            print(f"Unexpected error: {e}")
            return
        
        await asyncio.sleep(1)  # Just to ensure all output is printed before revoking the token.
        print("Revoking access token...")
        await post_auth_revoke_async(access_token, app_key, AUTH_REVOKE_URL, client)
        print("Access token revoked successfully.\n")

if __name__ == "__main__":
    
    asyncio.run(main())
   