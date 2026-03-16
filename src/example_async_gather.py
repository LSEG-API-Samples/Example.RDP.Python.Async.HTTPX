import asyncio
import os
import time
import httpx
from dotenv import load_dotenv

AUTH_TOKEN_URL = "/auth/oauth2/v1/token"
#HISTORICAL_INTRADAY_SUMMARIES_URL = "/data/historical-pricing/v1/views/intraday-summaries/"
HISTORICAL_INTERDAY_SUMMARIES_URL = "/data/historical-pricing/v1/views/interday-summaries/"

HISTORICAL_RICS = ["AAPL.O","MSFT.O","META.O","NVDA.O","GOOG.O","ORCL.N","IBM.N","PLTR.O","AMZN.O","AVGO.O"]  # Fetched concurrently

async def post_authentication(machine_id, password, app_key, url, client):
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


async def get_historical_interday_summaries(ric, token, url, client, interval, start, end, fields, semaphore=None):
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


# async def get_historical_intraday_summaries(ric, token, url, client, interval, start, end):
#     """Request historical Intraday summaries data"""
#     print(f"Fetching historical intraday summaries... for RIC: {ric}")
#     # Send the token in Authorization header for API access.
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }

#     # Parse incoming date strings and reformat to ISO 8601 nanosecond precision
#     # required by the RDP API (e.g. "2026-01-01T00:00:00.000000000Z").
#     # %f covers microseconds (6 digits); "000" pads to 9 digits (nanoseconds).
#     def to_nanosecond_str(dt_str: str) -> str:
#         dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
#         return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "000Z"

#     # parameters for intraday-summaries request.
#     params = {
#         "interval": interval,
#         "start": to_nanosecond_str(start),
#         "end": to_nanosecond_str(end),
#         "session": "normal"
#     }

#     response_history = await client.get(f"{url}{ric}", params=params, headers=headers)
#     print(f"Request URL: {response_history.url}")
#     # Raise an exception for 4xx/5xx HTTP errors, automatic handles of non-200 responses
#     response_history.raise_for_status()  
#     return response_history.json()


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
            token_data = await post_authentication(machine_id, password, app_key, AUTH_TOKEN_URL, client)
            print("Authentication successful. Access token obtained.")

            access_token = token_data.get("access_token")

            fields = ["TRDPRC_1", "BID", "ASK"]
            start = "2025-11-01T00:00:00Z"
            end = "2026-02-28T23:59:59Z"

            # Limit how many RIC requests run simultaneously to avoid
            # overwhelming the server or hitting rate limits.
            max_concurrent_tasks = 3
            sem = asyncio.Semaphore(max_concurrent_tasks)
            
            # Build one coroutine per RIC; the semaphore inside get_chain
            # ensures at most max_concurrent_tasks run at the same time.
            tasks_history = [get_historical_interday_summaries(ric, access_token, HISTORICAL_INTERDAY_SUMMARIES_URL, client, interval="P1D", start=start, end=end, fields=fields, semaphore=sem) for ric in HISTORICAL_RICS]

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

if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - start
    print(f"{__file__} executed for {HISTORICAL_RICS} in {elapsed:0.2f} seconds.")