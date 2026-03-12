import asyncio
import json
import os
import time
import httpx
from dotenv import load_dotenv

AUTH_TOKEN_URL = "/auth/oauth2/v1/token"
CHAIN_URL = "/data/pricing/chains/v1/"

RICS = ["EFX=", "0#.HSI", "0#.FTSE","0#.SPX"]  # Fetched concurrently

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

async def get_chain(ric, token, url, client, semaphore=None):
    """Fetch chain data for a single RIC symbol using an access token."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    # Query string parameters sent with the GET request.
    parameters = {
        "universe": ric
    }

    # Request chain data from the pricing chains endpoint.
    if semaphore:
        async with semaphore:
            response_chain = await client.get(url, params=parameters, headers=headers)
    else:
        response_chain = await client.get(url, params=parameters, headers=headers)

    response_chain.raise_for_status()
    return response_chain.json()

async def main():
    """Main entry point for the async example."""
    load_dotenv()

    # Read credentials and base URL from environment variables.
    machine_id = os.getenv("MACHINEID_RDP")
    password = os.getenv("PASSWORD_RDP")
    app_key = os.getenv("APPKEY_RDP")
    base_url = os.getenv("RDP_BASE_URL")

    # Reuse one connection pool across all requests.
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
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during authentication: {e.response.status_code} - {e.response.text}")
            return
        except httpx.HTTPError as e:
            print(f"Network error during authentication: {e}")
            return
        except Exception as e:
            print(f"Unexpected error during authentication: {e}")
            return

        access_token = token_data.get("access_token")

        # --- Fetch all RICs concurrently ---
        # tasks = [get_chain(ric, access_token, CHAIN_URL, client) for ric in RICS]
        # results = await asyncio.gather(*tasks, return_exceptions=True)

        # for ric, result in zip(RICS, results):
        #     if isinstance(result, httpx.HTTPStatusError):
        #         print(f"HTTP error fetching '{ric}': {result.response.status_code} - {result.response.text}")
        #     elif isinstance(result, Exception):
        #         print(f"Error fetching '{ric}': {result}")
        #     else:
        #         print(f"Chain data for '{ric}': {result}")

        # --- Fetch all RICs concurrently ---
        # TaskGroup cancels all remaining tasks as soon as one raises.
        # Exceptions are collected into an ExceptionGroup — use `except*` to handle them.
        MAX_CONCURRENT_TASKS = 3
        sem = asyncio.Semaphore(MAX_CONCURRENT_TASKS)  # Limit concurrent tasks
        sem = None  # No concurrency limit
        try:
            async with asyncio.TaskGroup() as tg:
                tasks = {ric: tg.create_task(get_chain(ric, access_token, CHAIN_URL, client, sem)) for ric in RICS}

            # Reached only if ALL tasks succeeded.
            results = {ric: task.result() for ric, task in tasks.items()}
            print("Chain data for all RICs:", json.dumps(results, indent=2))

        except* httpx.HTTPStatusError as eg:
            for exc in eg.exceptions:  
                print(f"HTTP error fetching chain data: {exc.request.url} -> {exc.response.status_code}: {exc.response.text}")
        except* httpx.HTTPError as eg:
            for exc in eg.exceptions:  
                print(f"Network error fetching chain data: {exc}")


        # try:
        #     ric = "EFX="
        #     ric = "0#.FTSE"
        #     print(f"Fetching chain data... for RIC: {ric}")
        #     chain_data = await get_chain(ric, access_token, CHAIN_URL, client)
        #     print("Chain data retrieved successfully!")
        #     print(f"Chain data for {ric}:", json.dumps(chain_data, indent=2))
        # except httpx.HTTPStatusError as e:
        #     print(f"HTTP error fetching chain data:{e.request.url}: {e.response.status_code} - {e.response.text}")      
        # except httpx.HTTPError as e:
        #     print(f"Network error fetching chain data:{e.request.url}: {e}")


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - start
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")