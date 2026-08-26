import os
import requests


class JobSearch:

    def __init__(
        self,
        preferences,
        log=print
    ):

        self.preferences = preferences
        self.log = log

        self.api_key = os.getenv(
            "TAVILY_API_KEY"
        )

    def build_queries(self):

        queries = []

        roles = self.preferences.get(
            "roles",
            []
        )

        locations = self.preferences.get(
            "locations",
            []
        )

        for role in roles:

            for location in locations:

                queries.append(
                    f'"{role}" jobs {location}'
                )

                queries.append(
                    f'"{role}" careers {location}'
                )

                queries.append(
                    f'"{role}" apply job {location}'
                )

        return queries

    def search(self, query):

        if not self.api_key:

            self.log(
                "TAVILY_API_KEY is missing."
            )

            return []

        self.log(
            f"Searching with Tavily: {query}"
        )

        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 10
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get(
            "results",
            []
        ):

            url = item.get("url")

            if not url:
                continue

            results.append({
                "title": item.get(
                    "title",
                    ""
                ),

                "url": url,

                "snippet": item.get(
                    "content",
                    ""
                ),

                "source": "Tavily"
            })

        return results

    def discover(self):

        all_jobs = []

        max_jobs = self.preferences.get(
            "max_jobs_per_run",
            20
        )

        for query in self.build_queries():

            try:

                results = self.search(
                    query
                )

                all_jobs.extend(
                    results
                )

                if len(all_jobs) >= max_jobs:
                    break

            except Exception as error:

                self.log(
                    f"Search error: {error}"
                )

        unique = {}

        for job in all_jobs:

            unique[job["url"]] = job

        return list(
            unique.values()
        )[:max_jobs]