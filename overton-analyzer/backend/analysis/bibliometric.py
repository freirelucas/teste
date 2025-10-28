"""
Bibliometric Analysis Module
Performs various bibliometric analyses on research works
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class BibliometricAnalyzer:
    """Performs bibliometric analysis on research works"""

    def __init__(self, works: List[Dict]):
        """
        Initialize analyzer with works data

        Args:
            works: List of enriched work metadata
        """
        self.works = works
        self.df = pd.DataFrame(works)

    def basic_statistics(self) -> Dict:
        """
        Calculate basic bibliometric statistics

        Returns:
            Dictionary of statistics
        """
        if self.df.empty:
            return {}

        stats = {
            'total_works': len(self.works),
            'total_citations': self.df['cited_by_count'].sum() if 'cited_by_count' in self.df else 0,
            'avg_citations': self.df['cited_by_count'].mean() if 'cited_by_count' in self.df else 0,
            'median_citations': self.df['cited_by_count'].median() if 'cited_by_count' in self.df else 0,
            'max_citations': self.df['cited_by_count'].max() if 'cited_by_count' in self.df else 0,
            'min_citations': self.df['cited_by_count'].min() if 'cited_by_count' in self.df else 0,

            # Year statistics
            'earliest_year': self.df['publication_year'].min() if 'publication_year' in self.df else None,
            'latest_year': self.df['publication_year'].max() if 'publication_year' in self.df else None,
            'avg_year': self.df['publication_year'].mean() if 'publication_year' in self.df else None,

            # Open access
            'open_access_count': self.df['open_access'].sum() if 'open_access' in self.df else 0,
            'open_access_percentage': (self.df['open_access'].sum() / len(self.df) * 100) if 'open_access' in self.df and len(self.df) > 0 else 0,
        }

        # H-index calculation
        if 'cited_by_count' in self.df:
            citations = sorted(self.df['cited_by_count'].tolist(), reverse=True)
            h_index = 0
            for i, cites in enumerate(citations, 1):
                if cites >= i:
                    h_index = i
                else:
                    break
            stats['h_index'] = h_index

        return stats

    def top_cited_works(self, n: int = 20) -> List[Dict]:
        """
        Get top cited works

        Args:
            n: Number of top works to return

        Returns:
            List of top cited works
        """
        if 'cited_by_count' not in self.df:
            return []

        top_works = self.df.nlargest(n, 'cited_by_count')

        return top_works[[
            'title', 'publication_year', 'cited_by_count',
            'authors', 'venue', 'doi'
        ]].to_dict('records')

    def analyze_authors(self, top_n: int = 20) -> Dict:
        """
        Analyze author productivity and impact

        Args:
            top_n: Number of top authors to return

        Returns:
            Dictionary with author analysis
        """
        author_stats = {}

        for work in self.works:
            for author in work.get('authors', []):
                author_name = author.get('name', 'Unknown')

                if author_name not in author_stats:
                    author_stats[author_name] = {
                        'name': author_name,
                        'works_count': 0,
                        'total_citations': 0,
                        'institutions': set()
                    }

                author_stats[author_name]['works_count'] += 1
                author_stats[author_name]['total_citations'] += work.get('cited_by_count', 0)

                for inst in author.get('institutions', []):
                    if inst:
                        author_stats[author_name]['institutions'].add(inst)

        # Convert to list and sort
        author_list = [
            {
                'name': stats['name'],
                'works_count': stats['works_count'],
                'total_citations': stats['total_citations'],
                'avg_citations': stats['total_citations'] / stats['works_count'] if stats['works_count'] > 0 else 0,
                'institutions': list(stats['institutions'])
            }
            for stats in author_stats.values()
        ]

        author_list.sort(key=lambda x: x['total_citations'], reverse=True)

        return {
            'total_authors': len(author_list),
            'top_authors': author_list[:top_n]
        }

    def analyze_institutions(self, top_n: int = 20) -> Dict:
        """
        Analyze institutional productivity

        Args:
            top_n: Number of top institutions to return

        Returns:
            Dictionary with institution analysis
        """
        inst_stats = Counter()

        for work in self.works:
            institutions = work.get('institutions', [])
            for inst in institutions:
                if inst:
                    inst_stats[inst] += 1

        top_institutions = [
            {'name': inst, 'count': count}
            for inst, count in inst_stats.most_common(top_n)
        ]

        return {
            'total_institutions': len(inst_stats),
            'top_institutions': top_institutions
        }

    def analyze_venues(self, top_n: int = 20) -> Dict:
        """
        Analyze publication venues

        Args:
            top_n: Number of top venues to return

        Returns:
            Dictionary with venue analysis
        """
        venue_stats = Counter()

        for work in self.works:
            venue = work.get('venue', '')
            if venue:
                venue_stats[venue] += 1

        top_venues = [
            {'name': venue, 'count': count}
            for venue, count in venue_stats.most_common(top_n)
        ]

        return {
            'total_venues': len(venue_stats),
            'top_venues': top_venues
        }

    def analyze_concepts(self, top_n: int = 30) -> Dict:
        """
        Analyze research concepts/topics

        Args:
            top_n: Number of top concepts to return

        Returns:
            Dictionary with concept analysis
        """
        concept_stats = {}

        for work in self.works:
            concepts = work.get('concepts', [])
            for concept in concepts:
                name = concept.get('name', '')
                score = concept.get('score', 0)
                level = concept.get('level', 0)

                if name not in concept_stats:
                    concept_stats[name] = {
                        'name': name,
                        'count': 0,
                        'total_score': 0,
                        'max_level': 0
                    }

                concept_stats[name]['count'] += 1
                concept_stats[name]['total_score'] += score
                concept_stats[name]['max_level'] = max(concept_stats[name]['max_level'], level)

        # Convert to list and calculate averages
        concept_list = [
            {
                'name': stats['name'],
                'count': stats['count'],
                'avg_score': stats['total_score'] / stats['count'],
                'max_level': stats['max_level']
            }
            for stats in concept_stats.values()
        ]

        concept_list.sort(key=lambda x: x['count'], reverse=True)

        return {
            'total_concepts': len(concept_list),
            'top_concepts': concept_list[:top_n]
        }

    def analyze_sdgs(self) -> Dict:
        """
        Analyze Sustainable Development Goals coverage

        Returns:
            Dictionary with SDG analysis
        """
        sdg_stats = Counter()

        for work in self.works:
            sdgs = work.get('sdgs', [])
            for sdg in sdgs:
                name = sdg.get('display_name', '')
                if name:
                    sdg_stats[name] += 1

        sdg_list = [
            {'name': sdg, 'count': count}
            for sdg, count in sdg_stats.most_common()
        ]

        return {
            'total_works_with_sdgs': sum(1 for work in self.works if work.get('sdgs')),
            'sdg_distribution': sdg_list
        }

    def collaboration_analysis(self) -> Dict:
        """
        Analyze collaboration patterns

        Returns:
            Dictionary with collaboration metrics
        """
        single_author = 0
        multi_author = 0
        international_collab = 0
        total_authors_per_paper = []
        total_countries_per_paper = []

        for work in self.works:
            num_authors = len(work.get('authors', []))
            num_countries = len(work.get('countries', []))

            total_authors_per_paper.append(num_authors)
            total_countries_per_paper.append(num_countries)

            if num_authors == 1:
                single_author += 1
            else:
                multi_author += 1

            if num_countries > 1:
                international_collab += 1

        return {
            'single_author_papers': single_author,
            'multi_author_papers': multi_author,
            'international_collaborations': international_collab,
            'avg_authors_per_paper': np.mean(total_authors_per_paper) if total_authors_per_paper else 0,
            'avg_countries_per_paper': np.mean(total_countries_per_paper) if total_countries_per_paper else 0,
            'collaboration_rate': (multi_author / len(self.works) * 100) if len(self.works) > 0 else 0,
            'international_collab_rate': (international_collab / len(self.works) * 100) if len(self.works) > 0 else 0
        }

    def generate_full_report(self) -> Dict:
        """
        Generate comprehensive bibliometric report

        Returns:
            Dictionary with all analyses
        """
        logger.info("Generating bibliometric report...")

        return {
            'basic_statistics': self.basic_statistics(),
            'top_cited_works': self.top_cited_works(20),
            'author_analysis': self.analyze_authors(20),
            'institution_analysis': self.analyze_institutions(20),
            'venue_analysis': self.analyze_venues(20),
            'concept_analysis': self.analyze_concepts(30),
            'sdg_analysis': self.analyze_sdgs(),
            'collaboration_analysis': self.collaboration_analysis()
        }
