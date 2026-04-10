# Concurrent LSEG Data Platform API Calls with Python Asyncio and HTTPX

- Version: 1.0
- Last update: Apr 2026
- Environment: Python + JupyterLab + Data Platform Account
- Prerequisite: Data Platform access/entitlements

## Overview

The [Requests](https://requests.readthedocs.io/en/latest/) library is widely regarded as *the de facto* standard HTTP client for Python applications. Many Python developers first learn REST API calls through Requests — including through our [Data Platform APIs Tutorials](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/tutorials) (or you can try RDP HTTP operations with the [built-in http.client](https://docs.python.org/3/library/http.client.html) if you enjoy a challenge.).

That said, there are other Python HTTP libraries worth considering — [HTTPX](https://www.python-httpx.org/), [Aiohttp](https://docs.aiohttp.org/en/stable/), [Urllib3](https://urllib3.readthedocs.io/en/stable/), [Grequests](https://pypi.org/project/grequests/), [PycURL](http://pycurl.io/docs/latest/index.html), and more — each offering different trade-offs in performance and features that may better suit your requirements.

I was drawn to HTTPX because it provides a **requests-compatible API** while also supporting **asynchronous operations** out of the box. That combination made migrating from Requests to HTTPX straightforward, with the added benefit of async support when needed.

This project shows how to use [HTTPX](https://www.python-httpx.org/) with [LSEG Data Platform APIs](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis) for authentication and data retrieval, with side-by-side synchronous and asynchronous examples. Its main purpose is to demonstrate the practical benefit of concurrent asynchronous HTTP calls: when many requests are needed, total wall-clock time is typically much lower than sequential execution while still allowing controlled throttling.

**Note**: A basic knowledge of Python [built-in asyncio](https://docs.python.org/3/library/asyncio.html) library is required to understand example codes.

## What is Data Platform APIs?

[LSEG Data Platform](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis) (RDP APIs) provides web-based API access to a broad range of LSEG content — including Historical Pricing, ESG, News, Real-Time, Transaction, Risk, and Research — delivered through a consistent APIs interfaces. It supports four delivery mechanisms: **Request-Response** (REST), **Alert** (async updates), **Bulk** (large payloads), and **Streaming** (real-time). This project focuses on the **Request-Response** method only.

## What is HTTPX?

[HTTPX](https://www.python-httpx.org/) is a modern Python HTTP client that supports both synchronous and asynchronous APIs, plus [HTTP/2](https://httpwg.org/specs/rfc7540.html). It is largely [compatible with the Requests library](https://www.python-httpx.org/compatibility/), so migrating existing code is straightforward.

For synchronous use, [`httpx.Client`](https://www.python-httpx.org/advanced/clients/) is the equivalent of `requests.Session()` — it maintains a shared connection pool across multiple requests:

```python
import httpx

with httpx.Client(base_url='http://httpbin.org') as client:
    r = client.get('/get')
    r.raise_for_status()
    print(r.status_code)
```

For asynchronous use, [`httpx.AsyncClient`](https://www.python-httpx.org/api/#asyncclient) works with [asyncio](https://docs.python.org/3/library/asyncio.html), [Trio](https://trio.readthedocs.io/en/stable/), and [AnyIO](https://anyio.readthedocs.io/en/stable/). This project uses asyncio:

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

**Synchronous** code runs tasks one at a time — each request must complete before the next one starts. The program blocks and waits at every I/O-bound call, so if a request takes 60 seconds, nothing else runs for those 60 seconds. Fine for a single request, but a real bottleneck when fetching data with many calls.

![synchronous](images/02_synchronous_simple.png)

**Asynchronous** code lets multiple tasks run concurrently. While one request is waiting for a network response, the event loop hands control to the next task instead of sitting idle.

![asynchronous](images/04_asynchronous_simple.png)

The real payoff comes when you have **many requests to make**. With `asyncio.gather()`, all requests are fired concurrently so the total time is roughly that of the single slowest response — not the sum of all response times. That is exactly the pattern used in `example_async_gather.py` and `async_call_nb.ipynb`.

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

## Prerequisites

- Python 3.11+
- LSEG Data Platform credentials with Historical Pricing permission:
  - Machine ID
  - Password
  - AppKey

Please your LSEG representative or account manager for the Data Platform Access

## Project Structure

```
├── requirements.txt             # Pinned dependencies
├── README.md                    # Project README file
├── LICENSE.md                   # Project LICENSE file
├── Article.md                   # Project Implementation detail (article) file
src/
├── .env.example                 # Environment variable template
├── sync_call_nb.ipynb           # Jupyter notebook — synchronous, shared httpx.Client
├── async_call_nb.ipynb          # Jupyter notebook — async, asyncio.gather() with Semaphore
├── example_client.py            # Synchronous — shared httpx.Client console app
└── example_async_gather.py      # Async — asyncio.gather() with Semaphore console app
```

## Included Notebooks

| Notebook | Mode | Description |
| --- | --- | --- |
| `src/sync_call_nb.ipynb` | Synchronous | Step-by-step workflow using a shared `httpx.Client` |
| `src/async_call_nb.ipynb` | Asynchronous | Concurrent workflow using `httpx.AsyncClient` and `asyncio.gather()` |

Both notebooks cover the same RDP API workflow — authentication, fetching historical interday summaries for **30 RICs**, and token revocation — and include wall-clock timing for the data-fetch phase.

### `sync_call_nb.ipynb` highlights

- Shared `httpx.Client` inside a `with` block — single connection pool, clean teardown
- RICs fetched **sequentially**, one request at a time

### `async_call_nb.ipynb` highlights

- Shared `httpx.AsyncClient` — same connection-pool benefit, async context manager
- `asyncio.gather(return_exceptions=True)` — all 30 RIC requests dispatched **concurrently**; one failure does not cancel the rest
- `asyncio.Semaphore` — caps in-flight requests (default: 10) to stay within server rate limits
- Jupyter's native top-level `await` support — no `asyncio.run()` wrapper needed

## Security Notes

- All examples use `verify=False` parameter to disable TLS certificate verification. This is intended for local/dev environments only (e.g. where a TLS-inspecting proxy such as ZScaler is in use). Remove `verify=False` parameter or supply a proper CA bundle for production use.
- Do not log or print access tokens in production applications.

## Project Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create your environment file by creating `src/.env` with the following content (see `src/.env.example` file):

```dotenv
RDP_BASE_URL=https://api.refinitiv.com

MACHINEID_RDP=<RDP Machine-ID>
PASSWORD_RDP=<RDP Password>
APPKEY_RDP=<RDP AppKey>
```

## Run

```powershell
# Jupyter notebook (synchronous)
jupyter lab src/simple_call_nb.ipynb

# Jupyter notebook (async — asyncio.gather)
jupyter lab src/async_call_nb.ipynb
```

Each script prints the authenticated request URLs and JSON responses. Timing is printed on exit for the async scripts.

## Security Notes

- All examples use `verify=False` to disable TLS certificate verification. This is intended for local/dev environments only (e.g. where a TLS-inspecting proxy such as ZScaler is in use). Remove `verify=False` or supply a proper CA bundle for production use.
- Do not log or print access tokens in production applications.

## Development Detail

See [Article.md](./Article.md) file.

## License

Apache 2.0. See [LICENSE.md](LICENSE.md).

## References

For further details, please check out the following resources:

- [LSEG Data Platform](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis) on the [LSEG Developers Portal](https://developers.lseg.com/en/) website.
- [Data Platform APIs Quick Start](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/quick-start)
- [Data Platform APIs Tutorials](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/tutorials)
- [Data Platform APIs Documents](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/documents)
- [HTTPX library](https://www.python-httpx.org/) and [GitHub](https://github.com/encode/httpx) pages.
- [Python Asyncio library](https://docs.python.org/3/library/asyncio.html) page.
- [Python's asyncio: A Hands-On Walkthrough](https://realpython.com/async-io-python/)
- [Asynchronous HTTP Requests in Python with HTTPX and asyncio](https://www.twilio.com/en-us/blog/asynchronous-http-requests-in-python-with-httpx-and-asyncio)
- [Asyncio gather function document](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather) page.
- [Asyncio TaskGroup function document](https://docs.python.org/3/library/asyncio-task.html#task-groups) page.

For any questions related to Data Platform APIs, please use the [Developers Community Q&A page](https://community.developers.refinitiv.com/).

