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