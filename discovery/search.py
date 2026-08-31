import os
import re
import requests

from datetime import datetime, timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from difflib import SequenceMatcher


class JobSearch:

    @staticmethod
    def normalize_url(url):

        parts = urlsplit(str(url).strip())

        ignored_parameters = {
            "fbclid",
            "gclid"
        }

        query = [
            (key, value)
            for key, value in parse_qsl(
                parts.query,
                keep_blank_values=True
            )
            if not key.lower().startswith("utm_")
            and key.lower() not in ignored_parameters
        ]

        path = parts.path.rstrip("/") or "/"

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            urlencode(query),
            ""
        ))

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

                past_31_days = (
                    datetime.now() - timedelta(days=31)
                ).strftime("%Y-%m-%d")

                queries.append(
                    (
                        role,
                        f'site:linkedin.com/posts '
                        f'"{role}" "{location}" '
                        f'(hiring OR "looking for" OR apply) '
                        f'after:{past_31_days}'
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

        title_lower = str(title or "").lower()
        url_lower = str(url or "").lower()
        snippet_lower = str(snippet or "").lower()
        role_lower = str(role or "").lower()

        parsed_url = urlsplit(
            str(url or "").strip()
        )

        if parsed_url.scheme not in [
            "http",
            "https"
        ] or not parsed_url.netloc:
            return False

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
            "bebee.com",
            "upwork.com",
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
            "linkedin.com/jobs",
            "naukri.com/",
            "instahyre.com/",
            "animationandvfxjobs.com/",
            "ziprecruiter.com/jobs",
            "/browse-careers"
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

        role_variants = [
            role_lower,
            role_lower.replace(
                "compositor",
                "compositing artist"
            ),
            role_lower.replace(
                "paint/prep",
                "paint prep"
            ),
            role_lower.replace(
                "paint/prep",
                "paint-prep"
            ),
            role_lower.replace(
                "paint/prep artist",
                "paint artist"
            ),
            role_lower.replace(
                "artist",
                "artists"
            ),
            role_lower.replace(
                "artists",
                "artist"
            )
        ]

        normalized_text = re.sub(
            r"[^a-z0-9]+",
            " ",
            combined_text
        )

        normalized_role = re.sub(
            r"[^a-z0-9]+",
            " ",
            role_lower
        ).strip()

        role_tokens = [
            token
            for token in normalized_role.split()
            if len(token) > 2
        ]

        token_matches = sum(
            token in normalized_text
            for token in role_tokens
        )

        fuzzy_role_match = (
            bool(normalized_role)
            and SequenceMatcher(
                None,
                normalized_role,
                normalized_text
            ).ratio() >= 0.35
        )

        has_role = any(
            variant in combined_text
            for variant in role_variants
            if variant
        ) or (
            bool(role_tokens)
            and token_matches == len(role_tokens)
        ) or fuzzy_role_match

        has_job_signal = any(
            signal in combined_text
            for signal in job_signals
        )

        is_linkedin_post = (
            "linkedin.com/posts/" in url_lower
            or "linkedin.com/feed/update/" in url_lower
        )

        if is_linkedin_post and not has_role:
            return False

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
        skipped_results = 0


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

            is_linkedin_post = (
                "linkedin.com/posts/" in str(url).lower()
                or "linkedin.com/feed/update/"
                in str(url).lower()
            )

            # Filter LinkedIn posts older than 31 days
            if is_linkedin_post:
                published_at = item.get(
                    "published_at"
                ) or item.get(
                    "publish_date"
                ) or item.get(
                    "date"
                )

                if published_at:
                    try:
                        if isinstance(published_at, str):
                            pub_date = datetime.fromisoformat(
                                published_at.replace("Z", "+00:00")
                            )
                        else:
                            pub_date = published_at

                        cutoff_date = datetime.now() - timedelta(days=31)
                        if pub_date.replace(tzinfo=None) < cutoff_date.replace(tzinfo=None):
                            self.log(
                                f"Skipping LinkedIn post older than 31 days: {url}"
                            )
                            skipped_results += 1
                            continue
                    except (ValueError, TypeError, AttributeError):
                        pass

            if not self.is_valid_job_result(
                title,
                url,
                snippet,
                role
            ):

                skipped_results += 1

                continue

            results.append({
                "title": title,
                "url": url,
                "snippet": snippet,
                "source": (
                    "LinkedIn public post"
                    if is_linkedin_post
                    else "Tavily"
                ),
                "is_linkedin_post": is_linkedin_post
            })

        if skipped_results:
            self.log(
                f"Skipped {skipped_results} non-matching "
                f"results for this query."
            )


        return results


    def discover(self):

        roles = self.preferences.get(
            "roles",
            []
        )

        try:
            max_jobs = max(
                0,
                int(self.preferences.get(
                    "max_jobs_per_run",
                    20
                ))
            )
        except (TypeError, ValueError):
            self.log(
                "Invalid max_jobs_per_run; using 20."
            )
            max_jobs = 20


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

                    url = self.normalize_url(
                        job["url"]
                    )


                    if url in seen_urls:
                        continue


                    seen_urls.add(
                        url
                    )


                    job["role"] = role
                    job["url"] = url


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