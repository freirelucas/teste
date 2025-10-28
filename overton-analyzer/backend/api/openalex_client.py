"""
OpenAlex API Client
Handles all interactions with the OpenAlex API
"""

import requests
import time
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAlexClient:
    """Client for interacting with OpenAlex API"""

    def __init__(self, base_url: str = 'https://api.openalex.org'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Overton-Analyzer/1.0 (mailto:research@example.com)',
            'Content-Type': 'application/json'
        })

    def get_work_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get work metadata by DOI

        Args:
            doi: Digital Object Identifier

        Returns:
            Work metadata
        """
        try:
            # Clean DOI
            doi = doi.strip().lower()
            if not doi.startswith('https://doi.org/'):
                doi = f'https://doi.org/{doi}'

            response = self.session.get(
                f'{self.base_url}/works/{doi}',
                timeout=30
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching work for DOI {doi}: {e}")
            return None

    def get_works_batch(self, dois: List[str], batch_size: int = 50) -> List[Dict]:
        """
        Get multiple works by DOIs in batches

        Args:
            dois: List of DOIs
            batch_size: Number of DOIs per batch

        Returns:
            List of work metadata
        """
        logger.info(f"Fetching metadata for {len(dois)} works from OpenAlex")

        all_works = []

        for i in range(0, len(dois), batch_size):
            batch = dois[i:i + batch_size]

            for doi in batch:
                work = self.get_work_by_doi(doi)
                if work:
                    all_works.append(work)
                time.sleep(0.1)  # Rate limiting

            logger.info(f"Processed {min(i + batch_size, len(dois))}/{len(dois)} works")

        logger.info(f"Successfully retrieved {len(all_works)} works")
        return all_works

    def search_works(self, query: str, max_results: int = 200) -> List[Dict]:
        """
        Search for works by query

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of works
        """
        logger.info(f"Searching OpenAlex for: {query}")

        all_results = []
        page = 1
        per_page = 50

        while len(all_results) < max_results:
            try:
                params = {
                    'search': query,
                    'page': page,
                    'per_page': per_page
                }

                response = self.session.get(
                    f'{self.base_url}/works',
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
                time.sleep(0.5)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error searching works: {e}")
                break

        return all_results[:max_results]

    def enrich_metadata(self, works: List[Dict]) -> List[Dict]:
        """
        Enrich work metadata with additional information

        Args:
            works: List of works

        Returns:
            Enriched works with extracted metadata
        """
        enriched = []

        for work in works:
            enriched_work = {
                'id': work.get('id', ''),
                'doi': work.get('doi', ''),
                'title': work.get('title', ''),
                'publication_year': work.get('publication_year'),
                'publication_date': work.get('publication_date'),
                'cited_by_count': work.get('cited_by_count', 0),
                'type': work.get('type', ''),
                'open_access': work.get('open_access', {}).get('is_oa', False),

                # Authors
                'authors': [
                    {
                        'name': author.get('author', {}).get('display_name', ''),
                        'id': author.get('author', {}).get('id', ''),
                        'institutions': [
                            inst.get('display_name', '')
                            for inst in author.get('institutions', [])
                        ]
                    }
                    for author in work.get('authorships', [])
                ],

                # Institutions
                'institutions': list(set([
                    inst.get('display_name', '')
                    for authorship in work.get('authorships', [])
                    for inst in authorship.get('institutions', [])
                ])),

                # Countries
                'countries': list(set([
                    inst.get('country_code', '')
                    for authorship in work.get('authorships', [])
                    for inst in authorship.get('institutions', [])
                    if inst.get('country_code')
                ])),

                # Topics/Concepts
                'topics': [
                    {
                        'name': topic.get('display_name', ''),
                        'score': topic.get('score', 0)
                    }
                    for topic in work.get('topics', [])[:5]
                ],

                'concepts': [
                    {
                        'name': concept.get('display_name', ''),
                        'score': concept.get('score', 0),
                        'level': concept.get('level', 0)
                    }
                    for concept in work.get('concepts', [])[:10]
                ],

                # Venue
                'venue': work.get('primary_location', {}).get('source', {}).get('display_name', ''),

                # References
                'referenced_works': work.get('referenced_works', []),
                'references_count': work.get('referenced_works_count', 0),

                # SDGs (Sustainable Development Goals)
                'sdgs': [
                    {
                        'id': sdg.get('id', ''),
                        'display_name': sdg.get('display_name', ''),
                        'score': sdg.get('score', 0)
                    }
                    for sdg in work.get('sustainable_development_goals', [])
                ],

                # Raw data
                'raw': work
            }

            enriched.append(enriched_work)

        return enriched
