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