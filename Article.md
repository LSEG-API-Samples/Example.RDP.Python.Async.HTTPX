# Data Platform APIs HTTP REST Application using Httpx

- Version: 1.0
- Last update: Mar 2026
- Environment: Python + JupyterLab + Data Platform Account
- Prerequisite: Data Platform access/entitlements

## Overview

The [Requests](https://requests.readthedocs.io/en/latest/) library is widely regarded as *the de facto* standard HTTP client for Python applications. Many Python developers first learn REST API calls through Requests — including through our [Data Platform APIs Tutorials](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/tutorials) (or you can try RDP HTTP operations with the [built-in http.client](https://docs.python.org/3/library/http.client.html) if you enjoy a challenge.).

That said, there are other Python HTTP libraries worth considering — [HTTPX](https://www.python-httpx.org/), [Aiohttp](https://docs.aiohttp.org/en/stable/), [Urllib3](https://urllib3.readthedocs.io/en/stable/), [Grequests](https://pypi.org/project/grequests/), [PycURL](http://pycurl.io/docs/latest/index.html), and more — each offering different trade-offs in performance and features that may better suit your requirements.

I was drawn to HTTPX because it provides a **requests-compatible API** while also supporting **asynchronous operations** out of the box. That combination made migrating from Requests to HTTPX straightforward, with the added benefit of async support when needed.

This project demonstrates how to use [`httpx`](https://www.python-httpx.org/) to authenticate and retrieve data from [LSEG Data Platform APIs](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis) via HTTP endpoints — covering both synchronous and asynchronous patterns for comparison.

**Note**: A basic knowledge of Python [built-in asyncio](https://docs.python.org/3/library/asyncio.html) library is required to understand example codes.

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

[HTTPX](https://www.python-httpx.org/) is a full featured modern HTTP client for Python 3. It provides a set of synchronous and modern asynchronous APIs with [HTTP/2](https://httpwg.org/specs/rfc7540.html) supported. It is largely [compatible with the Requests library](https://www.python-httpx.org/compatibility/), so any Python developers can migrate their existing [Requests](https://requests.readthedocs.io/en/latest/) library code to the HTTPX easily.

```python
import httpx

# Get
params = {'key1': 'value1', 'key2': 'value2'}
r = httpx.get('https://httpbin.org/get', params=params)
r.raise_for_status()
print(r.json())

# HTTP Post
data = {'integer': 123, 'boolean': True, 'list': ['a', 'b', 'c']}
r = httpx.post('https://httpbin.org/post', json=data)
r.raise_for_status()
print(r.json())
```

For synchronous use, HTTPX also provides [`httpx.Client`](https://www.python-httpx.org/advanced/clients/) object which is the equivalent of `requests.Session()` — it maintains a shared connection pool across multiple requests:

Example:

```python
import httpx

with httpx.Client(base_url='http://httpbin.org') as client:
  r = client.get('/get')
  r.raise_for_status()
  print(r.status_code)
```

For asynchronous use, [`httpx.AsyncClient`](https://www.python-httpx.org/api/#asyncclient) works with [asyncio](https://docs.python.org/3/library/asyncio.html), [Trio](https://trio.readthedocs.io/en/stable/), and [AnyIO](https://anyio.readthedocs.io/en/stable/). I am demonstrating with asyncio in this project.:

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

## What are Synchronous and Asynchronous Execution Models?

**Synchronous** code runs tasks one at a time in a strict sequence — each task must finish before the next one starts. The application pauses and waits at every blocking call. For example, the `httpx.get()` function call below (equivalent to `requests.get()`) blocks the entire program until the HTTP response arrives:

```python
import httpx

def fetch(url):
    """Fetch the content of the URL synchronously."""
    r = httpx.get(url, verify=False)
    print("Fetched:", url, "status:", r.status_code)
    return r.text

def main():
    """ Main function."""
    fetch("https://example.org")
    print("This line prints ONLY after the request is done!")

if __name__ == "__main__":
    main()
```

![synchronous code result](images/01_httpx_sync.png)

If the HTTP request takes 60 seconds, the program idles for those 60 seconds before executing the next line. For a single request this is fine, but it becomes a bottleneck when you need to fetch data for many symbols or endpoints.

![synchronous](images/synchronous_simple.png)

On the other hand, **Asynchronous** code allows multiple tasks to run concurrently in a non-blocking manner. While one task is waiting for I/O (such as a network response), the event loop can hand control to another task (execute next line of codes) instead of sitting idle. The example below uses `asyncio.create_task()` to launch a fetch in the background and immediately continues to the next line — without waiting for the response:

```python
import asyncio
import httpx 

async def fetch(url):
    """Fetch the content of the URL asynchronously."""
    async with httpx.AsyncClient(verify=False) as client:
        r = await client.get(url)
        print("Fetched:", url, "status:", r.status_code)
        return r.text

async def main():
    """ Main function."""
    asyncio.create_task(fetch("https://example.org"))
    print("Task launched and not awaited!")
    # Sleep to allow the fetch task to complete before the program exits.
    await asyncio.sleep(2) 
if __name__ == "__main__":
    asyncio.run(main())
```

![asynchronous code result](images/02_httpx_async.png)

![asynchronous](images/asynchronous_simple.png)

The real payoff of async comes when you have **many requests to make**. With `asyncio.gather()`, you can fire all of them concurrently so the total wall-clock time is roughly that of the single slowest response — instead of the sum of all response times. That is exactly the pattern used in `example_async_gather.py` and `async_call_nb.ipynb` examples for fetching multiple RICs.

## Throttling and Rate Limits 

The Data Platform API request limits (throttles) to effectively manage and protect its service and ensure fair usage across the non-streaming content. 

An application would receive an error from the API call if an application reached or exceeds a limit (especially with the Asynchronous HTTP calls). You required to make some necessary adjustments to rectify the interaction with the API and retry the respective API call. 

Two different server errors on API request limits are: 

| **HTTP Status** | **Detail** |
| --- | --- |
| **429** | **Error Message**: too many attempts |
|  | **Description**: A per account limit where the number of requests per second is limited for each account accessing the platform. If this limit is reached, applications will receive a standard HTTP error (HTTP 429 too many requests). |
|  | **Suggestion**: Please reduce the number of requests per second and retry. |

Please find more detail regarding the Data Platform HTTP error status messages from the [RDP API General Guidelines](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/documentation) document page.

The Historical Pricing endpoint rate limits information is available on the **Reference** tab of the [Data Platform API Playground](https://apidocs.refinitiv.com/Apps/ApiDocs) page. The current rate limits (**As of Mar 2026**) is as follows:

![historical rate limit](images/historical-pricing-ratelimits.png)


## Security Notes

- All examples use `verify=False` to disable TLS certificate verification. This is intended for local/dev environments only (e.g. where a TLS-inspecting proxy such as ZScaler is in use). Remove `verify=False` or supply a proper CA bundle for production use.
- Do not log or print access tokens in production applications.

## Code Walkthrough

Now we come to the code walkthrough. This article focuses primarily on the asynchronous code. Synchronous equivalents are shown in select places for comparison.

The examples use the following Python libraries for demonstration in Jupyter Notebook files.

| Library | Purpose |
| --- | --- |
| `asyncio` | Python's built-in async event loop and concurrency primitives |
| `os` | Read environment variables |
| `time` | Wall-clock timing via `time.perf_counter()` |
| `httpx` | Async HTTP client |
| `IPython.display` | Render formatted Markdown output in the notebook |
| `dotenv` | Load credentials from `src/.env` |

### Data Platform Authentication

Let's start with the authentication. The first step of any application workflow is to log in to the RDP Auth Service.

The required credentials are:

- **Username**: The machine ID associated with your account.
- **Password**: The password for the machine ID.
- **Client ID (AppKey)**: A unique identifier for your app, generated via the App Key Generator. Keep it private.
- **Grant Type `password`**: Used for the initial authentication request with a username/password combination.

I strongly suggest reading the [Data Platform: Authorization - All about tokens](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/tutorials#authorization-all-about-tokens) tutorial for a deeper understanding of RDP authentication.

The authentication function uses Python's [`async`](https://docs.python.org/3/reference/compound_stmts.html#async-def)/[`await`](https://docs.python.org/3/reference/expressions.html#await) syntax so the HTTP request can be suspended and resumed when the network response arrives — without blocking other tasks. The `client` parameter is a shared `httpx.AsyncClient` instance passed in from the caller, so the same underlying TCP connection pool is reused across all requests rather than opening a new connection each time.

```python
async def post_authentication_async(machine_id, password, app_key, url, client):
    """Authenticate to RDP and return the token response as JSON."""

    # Build the OAuth 2.0 Password Grant request payload.
    # Sent as application/x-www-form-urlencoded (httpx encodes a dict automatically).
    payload = {
        "username": machine_id,
        "password": password,
        "grant_type": "password",
        "scope": "trapi",
        "takeExclusiveSignOnControl": "true",
        "client_id": app_key
    }

    # Send authentication request to the OAuth token endpoint.
    # `data=payload` sends a form body required by this endpoint.
    response_auth = await client.post(url, data=payload, headers=headers)
    # Raise for 4xx/5xx API failures.
    response_auth.raise_for_status() 
    return response_auth.json()
```

The `raise_for_status()` call handles any non-[HTTP 200 OK](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/200) response — such as 4xx or 5xx errors — by raising an exception that propagates back to the caller.

Moving on to the main code. The `async with` block opens a shared `httpx.AsyncClient` and guarantees its connection pool is closed cleanly when the block exits, whether it completes normally or raises an exception. Inside the block, `post_authentication_async()` *is awaited* to obtain the Bearer token before any data requests are made.

```python
# Main Code
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

    # --- Exception handlers ordered from most-specific to least-specific ---
    except httpx.HTTPStatusError as e:
        # Server returned a 4xx or 5xx status code.
        print(f"HTTP error during request: {e.request.url} {e.response.status_code} - {e.response.text}")
    except httpx.TimeoutException as e:
        # Request exceeded the configured timeout (must precede RequestError
        # because TimeoutException is a subclass of RequestError).
        print(f"Timeout error: {e}")
    except httpx.RequestError as e:
        # Network-level failure: DNS, connection refused, SSL error, etc.
        print(f"Network error: {e}")
    except Exception as e:
        # Catch-all for unexpected errors (e.g. JSON decode, assertion).
        print(f"Unexpected error: {e}")
```

#### Where is asyncio.run(main())?

You might wonder why the main code does not call `asyncio.run(main())` statement. The reason is that Jupyter natively supports top-level `await`, so no `asyncio.run()` wrapper is needed.

If your target platform is non-Jupyter environment, you need call asynchronous code and method in `asyncio.run(main())` statement as follows:

```python
import asyncio

async def man()
    await something()

if __name__ == "__main__":
    
    asyncio.run(main())
```

### Comparing to Synchronous Code

For a single HTTP request, the synchronous equivalent is *almost* identical. The only real differences are the absence of `async`/`await` and the use of `httpx.Client` instead of `httpx.AsyncClient`. The code runs line by line — each statement blocks and waits for the network response before moving on.

```python
def post_authentication(machine_id, password, app_key, url, client):
    """Authenticate to RDP and return the token response as JSON."""

    payload = { ... } # same as the Async Code
    # no await
    response = client.post(url, data=payload)
    response.raise_for_status()  
    return response.json()

...

# Main code, use httpx.Client.
with httpx.Client(
    verify=False,
    base_url=base_url,
    timeout=10.0,
    default_encoding="utf-8",
    follow_redirects=True,
) as client:
    try:
        # Authenticate and get the access token.
        auth_response = post_authentication(machine_id, password, app_key, AUTH_TOKEN_URL, client)
        access_token = auth_response["access_token"]
        print("Authentication successful! Access token obtained.\n")
    except httpx.HTTPStatusError as exc:
        print(f"HTTP error occurred during HTTP Request: {exc.request.url}: {exc.response.status_code} - {exc.response.text}")
    ...
```

The `post_authentication_async` method sends a single HTTP POST request to the RDP authentication endpoint asynchronously and retrieves the access token for use in subsequent data requests. Nothing too exciting here — just a straightforward async HTTP call.

Once authentication succeeds, the function parses the RDP Auth service response and stores the following token fields:

- **access_token**: The token used to invoke REST data API calls as described above. The application must keep this credential for further RDP APIs requests.
- **refresh_token**: Refresh token to be used for obtaining an updated access token before expiration. The application must keep this credential for access token renewal.
- **expires_in**: Access token validity time in seconds.

### Requesting RDP APIs Data

That brings us to requesting the RDP APIs data. All subsequent REST API calls must pass the Access Token via the `Authorization` HTTP request header as shown below. 
- Header: 
    * Authorization = ```Bearer <RDP Access Token>```

Please notice *the space* between the ```Bearer``` and ```RDP Access Token``` values.

The application then builds a request message — either as a JSON body or URL query parameters depending on the service — and sends it to the appropriate API Endpoint. You can find each endpoint's HTTP operations and parameters on Data Platform's [API Playground page](https://apidocs.refinitiv.com/Apps/ApiDocs), an interactive documentation site available to anyone with a valid Data Platform account.

### Getting Multiple Historical Pricing Data Asynchronously 

Moving on to the main benefit of the asynchronous execution model: performing multiple I/O tasks in parallel, like sending multiple HTTP requests at once. I am demonstrating this with the `/data/historical-pricing/v1/views/interday-summaries/{universe}` endpoint, which retrieves time series pricing Interday summaries data (i.e. bar data) for a single RIC code via the following HTTP structure.

```http
GET /data/historical-pricing/v1/views/interday-summaries/{RIC Code}?{params} HTTP/1.1
Authorization: Bearer {access token}
Host: api.refinitiv.com
```

I am using 30 RICs from various exchanges — S&P 500, Nasdaq Composite, and others — as sample RIC codes.

```python
HISTORICAL_RICS = ["NVDA.O","AAPL.O","MSFT.O","AMZN.O","GOOG.O","AVGO.O","META.O","ORCL.N","IBM.N","PLTR.O","NFLX.O","TSLA.O","CRM.N","AMD.O","INTC.O","ARM.O","ASML.AS","CSCO.O","WMT.O","LLY.N","JPM.N","XOM.N","V.N","JNJ.N","MU.O","MA.N","COST.O","CVX.N","BAC.N","CAT.N"] 
```

Please note that my Data Platform account *does not have permission* to retrieve [ASML](https://www.asml.com/en) (`ASML.AS`) data. I included this RIC intentionally to demonstrate how to handle an error with asynchronous execution model.

[TBD]



