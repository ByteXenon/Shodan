import requests
import json
import time

class RateLimiter:
    def __init__(self, rate_limit):
        self.last_call = 0
        self.rate_limit = rate_limit

    def wait(self):
        while (self.last_call + self.rate_limit) >= time.time():
            time.sleep(self.rate_limit / 10)

        self.last_call = time.time()

class Shodan:
    class ShodanAPI:
        def __init__(self, api_key, proxy=None):
            self.api_key = api_key
            self.proxy = None
            if proxy:
                self.proxy = {"http": proxy, "https": proxy}

            self.proxy_counter = 0

        def request(self, function, params={}):
            params["key"] = self.api_key
            return requests.get(
                url=f"https://api.shodan.io/shodan/host/{function}",
                params=params,
                headers={'Cache-Control': 'no-cache'},
                proxies=self.proxy,
            )

    def __init__(self, api_keys, proxies=[], rate_limit=1):
        self.APIs = []
        self.rate_limiter = RateLimiter(rate_limit)
        for i, api_key in enumerate(api_keys):
            proxy = proxies[i] if len(proxies) > i else None
            self.APIs.append(self.ShodanAPI(api_key, proxy=proxy))

    def request(self, function, params):
        self.rate_limiter.wait()
        api = self.APIs.pop(0)
        self.APIs.append(api)
        response = None
        try:
            response = api.request(function, params)
        except Exception as e:
            return self.request(function, params)

        if response.status_code == 200:
            try:
                json_data = json.loads(response.text)
                return json_data
            except Exception as e:
                print(response.text, "ERROR")
                return self.request(function, params)
        elif response.status_code in (503, 500, 429):
            return self.request(function, params)
        else:
            print(response.status_code, "ERROR")
            return self.request(function, params)

    def search(self, query, page=1, minify=None):
        return self.request("search", {"query": query, "page": page, "minify": minify})

    def count(self, query, facets=None):
        return self.request("count", {"query": query, "facets": facets})
