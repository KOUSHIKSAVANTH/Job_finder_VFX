import os
import re
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
                    (
                        role,
                        f'"{role}" jobs {location}'
                    )
                )

                queries.append(
                    (
                        role,
                        f'"{role}" careers {location}'
                    )
                )

                queries.append(
                    (
                        role,
                        f'"{role}" hiring {location}'
                    )
                )

        return queries


    def is_valid_job_result(
        self,
        title,
        url,
        snippet,
        role
    ):

        title_lower = title.lower()
        url_lower = url.lower()
        snippet_lower = snippet.lower()
        role_lower = role.lower()

        # Websites that should never be treated
        # as job vacancies
        blocked_domains = [
            "reddit.com",
            "youtube.com",
            "facebook.com",
            "instagram.com",
            "wikipedia.org",
            "wiktionary.org",
            "quora.com",
            "rottentomatoes.com",
            "cgspectrum.com",
        ]

        if any(
            domain in url_lower
            for domain in blocked_domains
        ):
            return False


        # Informational pages, articles,
        # career guides and unrelated content
        blocked_title_patterns = [
            "job description",
            "salary",
            "career options",
            "career pathway",
            "career paths",
            "skills & software",
            "what is a",
            "what are",
            "how to become",
            "free dictionary",
            "wikipedia",
            "wiktionary",
            "rottentomatoes",
            "interview questions",
            "course",
            "training",
            "tutorial",
        ]

        if any(
            pattern in title_lower
            for pattern in blocked_title_patterns
        ):
            return False


        # Reject obvious general search/category pages
        blocked_url_patterns = [
            "/search",
            "job-search",
            "jobs-in-india",
        ]

        if any(
            pattern in url_lower
            for pattern in blocked_url_patterns
        ):
            return False


        # Reject titles advertising a large number
        # of jobs instead of one vacancy
        if re.search(
            r"\b\d+[,+]?\d*\s+.*jobs?\b",
            title_lower
        ):
            return False


        # The result should contain either the role
        # or strong job-related language
        combined_text = (
            title_lower
            + " "
            + snippet_lower
        )

        job_signals = [
            "job",
            "jobs",
            "hiring",
            "career",
            "vacancy",
            "vacancies",
            "position",
            "opening",
            "apply",
            "employment",
        ]

        has_role = (
            role_lower in combined_text
        )

        has_job_signal = any(
            signal in combined_text
            for signal in job_signals
        )

        if not has_role and not has_job_signal:
            return False


        return True


    def search(
        self,
        query,
        role
    ):

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

            url = item.get(
                "url"
            )

            if not url:
                continue


            title = item.get(
                "title",
                ""
            )

            snippet = item.get(
                "content",
                ""
            )


            if not self.is_valid_job_result(
                title,
                url,
                snippet,
                role
            ):

                self.log(
                    f"Rejected irrelevant result: "
                    f"{title}"
                )

                continue


            results.append({
                "title": title,
                "url": url,
                "snippet": snippet,
                "source": "Tavily"
            })


        return results


    def discover(self):

        roles = self.preferences.get(
            "roles",
            []
        )

        max_jobs = self.preferences.get(
            "max_jobs_per_run",
            20
        )


        if not roles:

            self.log(
                "No roles configured."
            )

            return []


        jobs_by_role = {
            role: []
            for role in roles
        }


        seen_urls = set()


        for role, query in self.build_queries():

            try:

                results = self.search(
                    query,
                    role
                )


                for job in results:

                    url = job["url"]


                    if url in seen_urls:
                        continue


                    seen_urls.add(
                        url
                    )


                    job["role"] = role


                    jobs_by_role[
                        role
                    ].append(
                        job
                    )


            except Exception as error:

                self.log(
                    f"Search error: {error}"
                )


        final_jobs = []


        jobs_per_role = (
            max_jobs // len(roles)
        )


        for role in roles:

            role_jobs = jobs_by_role[
                role
            ]


            final_jobs.extend(
                role_jobs[:jobs_per_role]
            )


        remaining_slots = (
            max_jobs - len(final_jobs)
        )


        if remaining_slots > 0:

            for role in roles:

                role_jobs = jobs_by_role[
                    role
                ]


                extra_jobs = role_jobs[
                    jobs_per_role:
                ]


                for job in extra_jobs:

                    if remaining_slots <= 0:
                        break


                    final_jobs.append(
                        job
                    )


                    remaining_slots -= 1


                if remaining_slots <= 0:
                    break


        self.log(
            f"Valid jobs after filtering: "
            f"{len(final_jobs)}"
        )


        return final_jobs[:max_jobs]