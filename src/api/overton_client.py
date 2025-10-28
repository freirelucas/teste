"""
Overton API Client

Client for interacting with the Overton API to retrieve policy documents.
"""

import time
import requests
from typing import Dict, List, Optional
from datetime import datetime


class OvertonClient:
    """Client for the Overton API."""

    def __init__(self, api_key: str, base_url: str, config: Dict):
        """
        Initialize the Overton API client.

        Args:
            api_key: Overton API key
            base_url: Base URL for the API
            config: Configuration dictionary with rate limits and retry settings
        """
        self.api_key = api_key
        self.base_url = base_url
        self.config = config

        # Rate limiting
        self.last_request_time = 0
        self.current_delay = config['rate_limit']['base_delay']

        # Statistics
        self.stats = {
            'api_calls': 0,
            'rate_limits': 0,
            'errors': 0,
            'documents_retrieved': 0
        }

    def _rate_limit(self):
        """Implement rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        wait_time = self.current_delay - elapsed

        if wait_time > 0:
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def _handle_rate_limit(self):
        """Adjust delay when rate limited."""
        self.stats['rate_limits'] += 1
        self.current_delay = min(
            self.current_delay * self.config['rate_limit']['multiplier'],
            self.config['rate_limit']['max_delay']
        )

    def validate_api_key(self) -> bool:
        """
        Validate the API key with a test request.

        Returns:
            True if the API key is valid, False otherwise
        """
        try:
            params = {
                'query': 'test',
                'format': 'json',
                'api_key': self.api_key,
                'page': 1,
                'per_page': 1
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            return response.status_code == 200

        except requests.exceptions.RequestException:
            return False

    def search_by_query(
        self,
        query: str,
        max_documents: int = 50000,
        per_page: int = 100
    ) -> List[Dict]:
        """
        Search for policy documents using a text query.

        Args:
            query: Search query string
            max_documents: Maximum number of documents to retrieve
            per_page: Number of documents per page

        Returns:
            List of policy document dictionaries
        """
        all_results = []
        page = 1
        total_documents_available = None

        print(f"\n🔎 Searching Overton for: '{query}'")

        while len(all_results) < max_documents:
            self._rate_limit()
            self.stats['api_calls'] += 1

            params = {
                'query': query,
                'format': 'json',
                'api_key': self.api_key,
                'page': page,
                'per_page': per_page
            }

            try:
                response = requests.get(self.base_url, params=params, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])

                    # Extract total count on first page
                    if page == 1 and 'meta' in data:
                        total_documents_available = data['meta'].get('count')
                        if total_documents_available:
                            print(f"📊 API reports {total_documents_available:,} total documents available")
                            max_documents = min(max_documents, total_documents_available)

                    if not results:
                        print(f"✓ Reached end of results at page {page}")
                        break

                    all_results.extend(results)
                    self.stats['documents_retrieved'] = len(all_results)

                    print(f"  Page {page}: retrieved {len(results)} documents (total: {len(all_results):,})")

                    # Check for next page
                    if not data.get('query', {}).get('next_page_url'):
                        print("✓ No more pages available")
                        break

                    page += 1

                elif response.status_code == 429:
                    self._handle_rate_limit()
                    print(f"⚠️  Rate limited. Retrying in {self.current_delay:.1f}s...")
                    time.sleep(self.current_delay)

                else:
                    self.stats['errors'] += 1
                    print(f"❌ API error on page {page}: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    break

            except requests.exceptions.RequestException as e:
                self.stats['errors'] += 1
                print(f"❌ Request error on page {page}: {e}")
                break

        print(f"\n✓ Retrieval complete: {len(all_results):,} documents")
        return all_results

    def get_stats(self) -> Dict:
        """
        Get API usage statistics.

        Returns:
            Dictionary of statistics
        """
        return self.stats.copy()
