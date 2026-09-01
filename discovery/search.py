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

        keywords = self.preferences.get(
            "keywords",
            []
        )

        for role in roles:

            for location in locations:

                # Standard role-based queries
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

                # Fresher/Junior variations
                queries.append(
                    (
                        role,
                        f'fresher "{role}" {location} jobs'
                    )
                )

                queries.append(
                    (
                        role,
                        f'junior "{role}" {location} hiring'
                    )
                )

                queries.append(
                    (
                        role,
                        f'"{role}" entry-level {location}'
                    )
                )

                # LinkedIn searches
                queries.append(
                    (
                        role,
                        f'site:linkedin.com/posts '
                        f'"{role}" "{location}" '
                        f'(hiring OR "looking for" OR apply OR fresher OR junior)'
                    )
                )

        # Add keyword-based searches for broader coverage
        for keyword in keywords[:5]:  # Limit to first 5 keywords to avoid too many queries
            for location in locations:
                queries.append(
                    (
                        keyword,
                        f'{keyword} jobs {location}'
                    )
                )

                queries.append(
                    (
                        keyword,
                        f'{keyword} hiring {location} fresher'
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
            "/browse-careers",
            "job-search",
            "jobs-in-india",
            "linkedin.com/jobs",
            "linkedin.com/in/",
            "linkedin.com/pub/",
            "/jobs?",
            "/career/",
            "/careers/",
            "?page="
        ]

        if any(
            pattern in url_lower
            for pattern in blocked_url_patterns
        ):
            return False

        # Reject senior-level experience requirements for fresher searches
        years_pattern = re.search(
            r"(\d+\s*[-–+to]+\s*\d+|\d+\+?)\s*(years?|yrs?)\s*(?:of\s*)?experience",
            snippet_lower + " " + title_lower,
            flags=re.IGNORECASE,
        )

        if years_pattern:
            years_match = years_pattern.group(0)
            if re.search(r"\b(3|4|5|6|7|8|9|10)\b", years_match):
                return False


        # Reject titles advertising a large number
        # of jobs instead of one vacancy
        if re.search(
            r"\b\d+[,+]?\d*\s+.*jobs?\b",
            title_lower
        ):
            return False

        combined_text = (
            title_lower
            + " "
            + snippet_lower
        )

        seniority_blockers = [
            "senior",
            "lead",
            "staff",
            "manager",
            "principal",
            "expert",
            "architect",
            "team lead",
            "3 years",
            "4 years",
            "5 years",
            "6 years",
            "7 years",
            "8 years",
            "9 years",
            "10 years",
            "3+ years",
            "4+ years",
            "5+ years",
            "3-5 years",
            "5-10 years",
            "8-10 years",
        ]

        if any(
            keyword in combined_text for keyword in seniority_blockers
        ):
            return False


        # The result should contain either the role
        # or strong job-related language

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


    def is_linkedin_post_recent(self, url, snippet):
        """Filter out old LinkedIn posts while being reasonable for niche VFX market."""
        if "linkedin.com/posts/" not in str(url).lower() and \
           "linkedin.com/feed/update/" not in str(url).lower():
            return True

        snippet_lower = str(snippet or "").lower()
        url_lower = str(url or "").lower()

        # Extract any 4-digit numbers that look like years from snippet and URL
        import re
        years_found = re.findall(r'\b(20\d{2}|2\d{2})\b', snippet_lower + " " + url_lower)
        
        # If we find any year before 2025, reject it (old posts)
        if years_found:
            for year_str in years_found:
                try:
                    year = int(year_str)
                    if year < 2025:  # Reject posts from 2024 and earlier
                        self.log(f"Rejecting LinkedIn post from year {year}: {url}")
                        return False
                except ValueError:
                    pass

        # Reject posts with clear "very old" date indicators
        old_indicators = [
            "year ago",
            "years ago",
            "6 months ago",
            "5 months ago",
            "4 months ago",
            "3 months ago",
        ]

        if any(indicator in snippet_lower for indicator in old_indicators):
            self.log(f"Rejecting old LinkedIn post (3+ months old): {url}")
            return False

        # Block specific old months/years
        very_old = ["january", "february", "march", "april", "may", "june", "q1 ", "q2 "]
        if any(old in snippet_lower for old in very_old):
            # Check if it's 2025 or 2026 - if so, might be OK
            if "2025" in snippet_lower or "2026" in snippet_lower:
                return True  # Could be recent
            else:
                return False  # Likely old

        # Accept posts that don't show clear old date indicators
        # (For niche markets, newer posts might not have explicit timestamps)
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

            # Filter LinkedIn posts that appear to be older than 31 days
            if is_linkedin_post and not self.is_linkedin_post_recent(url, snippet):
                self.log(
                    f"Skipping old LinkedIn post (not recent): {url}"
                )
                skipped_results += 1
                continue

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