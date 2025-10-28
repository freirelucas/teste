"""
Overton API Client
Handles all interactions with the Overton API
"""

import requests
import time
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OvertonClient:
    """Client for interacting with Overton API"""

    def __init__(self, api_key: str, base_url: str = 'https://api.overton.io'):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def search_policies(self, query: str, max_results: int = 500) -> List[Dict]:
        """
        Search for policy documents citing research on a topic

        Args:
            query: Search query string
            max_results: Maximum number of results to retrieve

        Returns:
            List of policy documents with metadata
        """
        logger.info(f"Searching Overton for: {query}")

        all_results = []
        page = 0
        per_page = 100

        while len(all_results) < max_results:
            try:
                params = {
                    'q': query,
                    'page': page,
                    'per_page': per_page
                }

                response = self.session.get(
                    f'{self.base_url}/search/policies',
                    params=params,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                results = data.get('results', [])

                if not results:
                    break

                all_results.extend(results)
                logger.info(f"Retrieved {len(all_results)} results...")

                page += 1
                time.sleep(0.5)  # Rate limiting

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching data: {e}")
                break

        logger.info(f"Total results retrieved: {len(all_results)}")
        return all_results[:max_results]

    def get_policy_details(self, policy_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific policy document

        Args:
            policy_id: Overton policy ID

        Returns:
            Policy document details
        """
        try:
            response = self.session.get(
                f'{self.base_url}/policies/{policy_id}',
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching policy details: {e}")
            return None

    def get_cited_works(self, policy_id: str) -> List[Dict]:
        """
        Get research works cited in a policy document

        Args:
            policy_id: Overton policy ID

        Returns:
            List of cited works
        """
        try:
            response = self.session.get(
                f'{self.base_url}/policies/{policy_id}/citations',
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('citations', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching citations: {e}")
            return []

    def extract_cited_dois(self, policies: List[Dict]) -> List[str]:
        """
        Extract all DOIs from policy documents

        Args:
            policies: List of policy documents

        Returns:
            List of unique DOIs
        """
        dois = set()

        for policy in policies:
            # Extract from citations field
            citations = policy.get('citations', [])
            for citation in citations:
                doi = citation.get('doi')
                if doi:
                    dois.add(doi.lower().strip())

            # Extract from references field if available
            references = policy.get('references', [])
            for ref in references:
                doi = ref.get('doi')
                if doi:
                    dois.add(doi.lower().strip())

        logger.info(f"Extracted {len(dois)} unique DOIs")
        return list(dois)

    def analyze_policy_sources(self, policies: List[Dict]) -> Dict:
        """
        Analyze the sources of policy documents by sector

        Args:
            policies: List of policy documents

        Returns:
            Dictionary with sector analysis
        """
        sectors = {
            'think_tank': 0,
            'government': 0,
            'academia': 0,
            'private': 0,
            'ngo': 0,
            'international': 0,
            'unknown': 0
        }

        sector_keywords = {
            'think_tank': ['institute', 'foundation', 'center', 'centre', 'think tank'],
            'government': ['government', 'ministry', 'department', 'parliament', 'congress', 'senate'],
            'academia': ['university', 'college', 'academic', 'school'],
            'private': ['company', 'corporation', 'inc', 'ltd', 'llc'],
            'ngo': ['ngo', 'non-profit', 'nonprofit', 'charity', 'association'],
            'international': ['united nations', 'world bank', 'imf', 'oecd', 'who', 'unesco']
        }

        for policy in policies:
            source = policy.get('source', {})
            source_name = source.get('name', '').lower()
            source_type = source.get('type', '').lower()

            classified = False
            for sector, keywords in sector_keywords.items():
                if any(keyword in source_name or keyword in source_type for keyword in keywords):
                    sectors[sector] += 1
                    classified = True
                    break

            if not classified:
                sectors['unknown'] += 1

        return sectors
