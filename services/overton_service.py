import requests
import time
from typing import Dict, List, Optional
from threading import Lock

class OvertonService:
    """Service to interact with Overton API"""

    BASE_URL = "https://api.overton.io"
    RATE_LIMIT_DELAY = 1.0  # 1 second between requests

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Overton service

        Args:
            api_key: Overton API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.last_request_time = 0
        self.lock = Lock()

        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })

    def _rate_limit(self):
        """Ensure we don't exceed 1 request per second"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time

            if time_since_last < self.RATE_LIMIT_DELAY:
                sleep_time = self.RATE_LIMIT_DELAY - time_since_last
                time.sleep(sleep_time)

            self.last_request_time = time.time()

    def search_documents(self, query: str, limit: int = 10) -> Dict:
        """
        Search for policy documents and research in Overton

        Args:
            query: Search query
            limit: Number of results to return

        Returns:
            Dictionary with search results
        """
        if not self.api_key:
            return {
                'error': 'Overton API key not configured',
                'message': 'Please add OVERTON_API_KEY to your .env file'
            }

        self._rate_limit()

        params = {
            'q': query,
            'limit': limit
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Format results based on Overton's response structure
            results = {
                'count': data.get('total', 0),
                'documents': []
            }

            for doc in data.get('results', []):
                formatted_doc = {
                    'id': doc.get('id'),
                    'title': doc.get('title'),
                    'abstract': doc.get('abstract'),
                    'year': doc.get('year'),
                    'url': doc.get('url'),
                    'doi': doc.get('doi'),
                    'type': doc.get('type'),
                    'source': doc.get('source'),
                    'authors': doc.get('authors', []),
                    'policy_mentions': doc.get('policy_mentions', 0),
                    'countries': doc.get('countries', []),
                    'organizations': doc.get('organizations', [])
                }
                results['documents'].append(formatted_doc)

            return results

        except requests.exceptions.RequestException as e:
            return {
                'error': f"Overton API error: {str(e)}",
                'message': 'Could not fetch data from Overton'
            }

    def get_stats(self, query: str) -> Dict:
        """
        Get statistics about documents matching the query

        Args:
            query: Search query

        Returns:
            Dictionary with statistics
        """
        if not self.api_key:
            return None

        self._rate_limit()

        params = {
            'q': query,
            'limit': 1
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'total_documents': data.get('total', 0),
                'total_policy_mentions': data.get('total_policy_mentions', 0)
            }

        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
