"""
Data processing utilities for policy documents and academic works.
"""

import pandas as pd
from typing import Dict, List, Any
from collections import defaultdict, Counter


class PolicyDataProcessor:
    """Process policy document data from Overton."""

    @staticmethod
    def extract_source_info(doc: Dict) -> Dict:
        """
        Extract source information from policy document.

        Args:
            doc: Policy document dictionary

        Returns:
            Dictionary with source information
        """
        source = doc.get('source', {})
        if not isinstance(source, dict):
            return {}

        return {
            'source_name': source.get('title', source.get('name', '')),
            'source_country': source.get('country', ''),
            'source_type': source.get('type', ''),
        }

    @staticmethod
    def extract_metadata(doc: Dict) -> Dict:
        """
        Extract comprehensive metadata from policy document.

        Args:
            doc: Policy document dictionary

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'policy_document_id': doc.get('policy_document_id', ''),
            'title': doc.get('title', ''),
            'url': doc.get('url', ''),
            'published_on': doc.get('published_on', ''),
            'published_date': pd.to_datetime(doc.get('published_on', ''), errors='coerce'),
        }

        # Add source information
        metadata.update(PolicyDataProcessor.extract_source_info(doc))

        # Extract topics
        topics = doc.get('topics', [])
        metadata['topics'] = topics if isinstance(topics, list) else []

        # Extract SDG categories
        sdgs = doc.get('sdgcategories', [])
        metadata['sdg_categories'] = sdgs if isinstance(sdgs, list) else []

        # Extract COFOG divisions
        cofog = doc.get('cofog_divisions', [])
        metadata['cofog_divisions'] = cofog if isinstance(cofog, list) else []

        # Extract policy document series
        metadata['document_series'] = doc.get('overton_policy_document_series', '')

        # Extract cited scholarly works
        cites = doc.get('cites', {})
        cited_dois = []
        if isinstance(cites, dict):
            scholarly = cites.get('scholarly', [])
            if isinstance(scholarly, list):
                for cite in scholarly:
                    if isinstance(cite, dict) and cite.get('doi'):
                        doi = cite['doi'].replace('https://doi.org/', '')
                        cited_dois.append(doi)

        metadata['cited_dois'] = cited_dois
        metadata['cited_doi_count'] = len(cited_dois)

        return metadata

    @staticmethod
    def create_dataframe(policy_docs: List[Dict]) -> pd.DataFrame:
        """
        Create DataFrame from policy documents.

        Args:
            policy_docs: List of policy document dictionaries

        Returns:
            Pandas DataFrame
        """
        records = [PolicyDataProcessor.extract_metadata(doc) for doc in policy_docs]
        df = pd.DataFrame(records)

        # Ensure published_date is datetime
        if 'published_date' in df.columns:
            df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')

        return df

    @staticmethod
    def get_summary_statistics(df: pd.DataFrame) -> Dict:
        """
        Calculate summary statistics for policy documents.

        Args:
            df: Policy documents DataFrame

        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_documents': len(df),
            'documents_with_citations': (df['cited_doi_count'] > 0).sum(),
            'total_citations': df['cited_doi_count'].sum(),
            'mean_citations_per_doc': df['cited_doi_count'].mean(),
            'median_citations_per_doc': df['cited_doi_count'].median(),
        }

        # Country statistics
        if 'source_country' in df.columns:
            country_counts = df['source_country'].value_counts()
            stats['countries'] = {
                'total_countries': len(country_counts),
                'top_country': country_counts.index[0] if len(country_counts) > 0 else None,
                'top_country_count': int(country_counts.iloc[0]) if len(country_counts) > 0 else 0,
            }

        # Type statistics
        if 'source_type' in df.columns:
            type_counts = df['source_type'].value_counts()
            stats['types'] = {
                'total_types': len(type_counts),
                'top_type': type_counts.index[0] if len(type_counts) > 0 else None,
                'top_type_count': int(type_counts.iloc[0]) if len(type_counts) > 0 else 0,
            }

        # Date range
        if 'published_date' in df.columns:
            valid_dates = df['published_date'].dropna()
            if len(valid_dates) > 0:
                stats['date_range'] = {
                    'earliest': str(valid_dates.min().date()),
                    'latest': str(valid_dates.max().date()),
                }

        return stats


class AcademicDataProcessor:
    """Process academic work data from OpenAlex."""

    @staticmethod
    def create_dataframe(works_dict: Dict[str, Dict]) -> pd.DataFrame:
        """
        Create DataFrame from OpenAlex works metadata.

        Args:
            works_dict: Dictionary mapping DOI to work metadata

        Returns:
            Pandas DataFrame
        """
        records = []

        for doi, work in works_dict.items():
            if work:
                record = {
                    'doi': doi,
                    'title': work.get('title', ''),
                    'publication_year': work.get('publication_year'),
                    'publication_date': work.get('publication_date'),
                    'type': work.get('type'),
                    'cited_by_count': work.get('cited_by_count', 0),
                    'is_oa': work.get('is_oa', False),
                    'oa_status': work.get('oa_status'),
                    'author_count': work.get('author_count', 0),
                }

                # Extract journal name
                journal_info = work.get('journal', {})
                record['journal_name'] = journal_info.get('name', '')

                # Extract concepts
                concepts = work.get('concepts', [])
                if concepts:
                    record['top_concept'] = concepts[0].get('name', '')
                    record['concept_score'] = concepts[0].get('score', 0)

                # Count institutions
                institutions = work.get('institutions', [])
                record['institution_count'] = len(institutions) if institutions else 0

                # Count SDGs
                sdgs = work.get('sdgs', [])
                record['sdg_count'] = len(sdgs) if sdgs else 0

                records.append(record)
            else:
                # Work not found
                records.append({'doi': doi, 'title': None})

        df = pd.DataFrame(records)

        # Convert dates
        if 'publication_date' in df.columns:
            df['publication_date'] = pd.to_datetime(df['publication_date'], errors='coerce')

        return df

    @staticmethod
    def get_summary_statistics(df: pd.DataFrame) -> Dict:
        """
        Calculate summary statistics for academic works.

        Args:
            df: Academic works DataFrame

        Returns:
            Dictionary of statistics
        """
        # Filter to works that were found
        valid_df = df[df['title'].notna()]

        stats = {
            'total_dois': len(df),
            'works_found': len(valid_df),
            'works_not_found': len(df) - len(valid_df),
        }

        if len(valid_df) > 0:
            stats.update({
                'mean_citations': valid_df['cited_by_count'].mean(),
                'median_citations': valid_df['cited_by_count'].median(),
                'total_citations': valid_df['cited_by_count'].sum(),
                'open_access_percentage': (valid_df['is_oa'].sum() / len(valid_df) * 100),
            })

            # Year statistics
            if 'publication_year' in valid_df.columns:
                years = valid_df['publication_year'].dropna()
                if len(years) > 0:
                    stats['year_range'] = {
                        'earliest': int(years.min()),
                        'latest': int(years.max()),
                    }

        return stats
