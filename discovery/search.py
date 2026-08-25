import os
import requests

from urllib.parse import quote


class JobSearch:

    def __init__(
        self,
        preferences,
        log=print
    ):

        self.preferences = preferences
        self.log = log

        self.api_key = os.getenv(
            "SEARCH_API_KEY"
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
                "SEARCH_API_KEY is missing."
            )

            return []

        self.log(
            f"Searching: {query}"
        )

        # Search provider endpoint.
        # The provider response is normalized below.
        response = requests.get(
            "https://www.searchapi.io/api/v1/search",
            params={
                "engine": "google",
                "q": query,
                "api_key": self.api_key
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get(
            "organic_results",
            []
        ):

            url = item.get("link")

            if not url:
                continue

            results.append({
                "title": item.get(
                    "title",
                    ""
                ),

                "url": url,

                "snippet": item.get(
                    "snippet",
                    ""
                ),

                "source": "Search"
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