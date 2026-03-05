
import httpx
import asyncio

async def fetch(url):
    async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
        r = await client.get(url)
        return r.text

async def main():
    urls = ["https://example.com", "https://python.org"]
    results = await asyncio.gather(*(fetch(u) for u in urls))
    print(results)

asyncio.run(main())
