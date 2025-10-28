import requests
import time
from typing import Dict, List, Optional

class OpenAlexService:
    """Service to interact with OpenAlex API"""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, email: Optional[str] = None):
        """
        Initialize OpenAlex service

        Args:
            email: Your email for polite pool (better rate limits)
        """
        self.email = email
        self.session = requests.Session()

    def _build_params(self, **kwargs) -> Dict:
        """Build query parameters including email if available"""
        params = kwargs.copy()
        if self.email:
            params['mailto'] = self.email
        return params

    def search_works(self, query: str, limit: int = 10, filters: Optional[Dict] = None) -> Dict:
        """
        Search for works in OpenAlex

        Args:
            query: Search query
            limit: Number of results to return
            filters: Additional filters to apply

        Returns:
            Dictionary with search results
        """
        params = self._build_params(
            search=query,
            per_page=limit
        )

        # Add any additional filters
        if filters:
            for key, value in filters.items():
                params[f'filter[{key}]'] = value

        try:
            response = self.session.get(
                f"{self.BASE_URL}/works",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Extract and format relevant information
            results = {
                'count': data.get('meta', {}).get('count', 0),
                'works': []
            }

            for work in data.get('results', []):
                formatted_work = {
                    'id': work.get('id'),
                    'doi': work.get('doi'),
                    'title': work.get('title'),
                    'display_name': work.get('display_name'),
                    'publication_year': work.get('publication_year'),
                    'publication_date': work.get('publication_date'),
                    'type': work.get('type'),
                    'cited_by_count': work.get('cited_by_count', 0),
                    'is_open_access': work.get('open_access', {}).get('is_oa', False),
                    'oa_status': work.get('open_access', {}).get('oa_status'),
                    'oa_url': work.get('open_access', {}).get('oa_url'),
                    'authors': [
                        {
                            'name': auth.get('author', {}).get('display_name'),
                            'id': auth.get('author', {}).get('id')
                        }
                        for auth in work.get('authorships', [])[:5]  # Limit to first 5 authors
                    ],
                    'concepts': [
                        {
                            'name': concept.get('display_name'),
                            'score': concept.get('score')
                        }
                        for concept in work.get('concepts', [])[:5]  # Top 5 concepts
                    ],
                    'abstract': work.get('abstract_inverted_index'),
                    'source': work.get('primary_location', {}).get('source', {}).get('display_name'),
                    'url': work.get('primary_location', {}).get('landing_page_url')
                }
                results['works'].append(formatted_work)

            return results

        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAlex API error: {str(e)}")

    def get_work(self, work_id: str) -> Dict:
        """
        Get detailed information about a specific work

        Args:
            work_id: OpenAlex work ID (e.g., 'W2741809807' or full URL)

        Returns:
            Dictionary with work details
        """
        # Extract ID if full URL is provided
        if work_id.startswith('http'):
            work_id = work_id.split('/')[-1]

        params = self._build_params()

        try:
            response = self.session.get(
                f"{self.BASE_URL}/works/{work_id}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAlex API error: {str(e)}")

    def get_stats(self, query: str) -> Dict:
        """
        Get statistics about research matching the query

        Args:
            query: Search query

        Returns:
            Dictionary with statistics
        """
        params = self._build_params(
            search=query,
            per_page=1,
            group_by='publication_year'
        )

        try:
            response = self.session.get(
                f"{self.BASE_URL}/works",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'total_works': data.get('meta', {}).get('count', 0),
                'by_year': data.get('group_by', [])
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAlex API error: {str(e)}")
