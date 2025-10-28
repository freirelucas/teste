"""
OpenAlex API Client

Client for interacting with the OpenAlex API to retrieve academic publication metadata.
"""

import time
import requests
from typing import Dict, List, Optional
from collections import defaultdict


class OpenAlexClient:
    """Client for the OpenAlex API."""

    def __init__(self, base_url: str, config: Dict):
        """
        Initialize the OpenAlex API client.

        Args:
            base_url: Base URL for the API
            config: Configuration dictionary with rate limits and retry settings
        """
        self.base_url = base_url
        self.config = config

        # Rate limiting
        self.last_request_time = 0
        self.request_delay = 1.0 / config['rate_limit']['requests_per_second']

        # Statistics
        self.stats = {
            'api_calls': 0,
            'rate_limits': 0,
            'errors': 0,
            'works_retrieved': 0
        }

    def _rate_limit(self):
        """Implement rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        wait_time = self.request_delay - elapsed

        if wait_time > 0:
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def get_work_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Retrieve metadata for a single work by DOI.

        Args:
            doi: DOI of the work (without https://doi.org/ prefix)

        Returns:
            Work metadata dictionary or None if not found
        """
        # Clean DOI
        if doi.startswith('https://doi.org/'):
            doi = doi.replace('https://doi.org/', '')

        url = f"{self.base_url}/works/doi:{doi}"

        for attempt in range(self.config['retry']['max_retries']):
            self._rate_limit()
            self.stats['api_calls'] += 1

            try:
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    self.stats['works_retrieved'] += 1
                    return response.json()

                elif response.status_code == 404:
                    return None  # Work not found

                elif response.status_code == 429:
                    self.stats['rate_limits'] += 1
                    wait_time = self.config['retry']['base_delay'] * (2 ** attempt)
                    print(f"⚠️  Rate limited. Retrying in {wait_time}s...")
                    time.sleep(wait_time)

                else:
                    self.stats['errors'] += 1
                    return None

            except requests.exceptions.RequestException:
                if attempt < self.config['retry']['max_retries'] - 1:
                    time.sleep(self.config['retry']['base_delay'])
                else:
                    self.stats['errors'] += 1
                    return None

        return None

    def get_works_batch(
        self,
        dois: List[str],
        batch_size: int = 50
    ) -> Dict[str, Optional[Dict]]:
        """
        Retrieve metadata for multiple works by DOI.

        Args:
            dois: List of DOIs
            batch_size: Number of DOIs to process at once

        Returns:
            Dictionary mapping DOI to work metadata (or None if not found)
        """
        results = {}
        total = len(dois)

        print(f"\n📚 Retrieving metadata from OpenAlex for {total:,} DOIs...")

        for i in range(0, total, batch_size):
            batch = dois[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"  Batch {batch_num}/{total_batches}: processing {len(batch)} DOIs")

            for doi in batch:
                work = self.get_work_by_doi(doi)
                results[doi] = work

        successful = sum(1 for v in results.values() if v is not None)
        print(f"✓ Retrieved {successful:,}/{total:,} works successfully")

        return results

    def extract_metadata(self, work: Dict) -> Dict:
        """
        Extract relevant metadata from a work object.

        Args:
            work: Work metadata from OpenAlex

        Returns:
            Dictionary with extracted metadata
        """
        if not work:
            return {}

        # Extract basic metadata
        metadata = {
            'doi': work.get('doi', '').replace('https://doi.org/', ''),
            'title': work.get('title', ''),
            'publication_year': work.get('publication_year'),
            'publication_date': work.get('publication_date'),
            'type': work.get('type'),
            'cited_by_count': work.get('cited_by_count', 0),
            'is_oa': work.get('open_access', {}).get('is_oa', False),
            'oa_status': work.get('open_access', {}).get('oa_status'),
        }

        # Extract authors
        authorships = work.get('authorships', [])
        metadata['authors'] = [
            {
                'name': auth.get('author', {}).get('display_name', ''),
                'orcid': auth.get('author', {}).get('orcid', ''),
                'position': auth.get('author_position')
            }
            for auth in authorships
        ]
        metadata['author_count'] = len(authorships)

        # Extract institutions
        institutions = []
        for auth in authorships:
            for inst in auth.get('institutions', []):
                inst_name = inst.get('display_name', '')
                if inst_name and inst_name not in institutions:
                    institutions.append(inst_name)
        metadata['institutions'] = institutions

        # Extract concepts/topics
        concepts = work.get('concepts', [])
        metadata['concepts'] = [
            {
                'name': c.get('display_name', ''),
                'level': c.get('level'),
                'score': c.get('score')
            }
            for c in concepts
        ]

        # Extract journal information
        primary_location = work.get('primary_location', {})
        source = primary_location.get('source', {})
        metadata['journal'] = {
            'name': source.get('display_name', ''),
            'issn': source.get('issn', []),
            'type': source.get('type')
        }

        # Extract SDGs
        sdgs = work.get('sustainable_development_goals', [])
        metadata['sdgs'] = [
            {
                'id': sdg.get('id', ''),
                'display_name': sdg.get('display_name', ''),
                'score': sdg.get('score')
            }
            for sdg in sdgs
        ]

        return metadata

    def get_stats(self) -> Dict:
        """
        Get API usage statistics.

        Returns:
            Dictionary of statistics
        """
        return self.stats.copy()
