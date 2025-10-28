"""
Temporal Analysis Module
Analyzes trends over time
"""

import pandas as pd
from typing import Dict, List
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class TemporalAnalyzer:
    """Performs temporal analysis on research works"""

    def __init__(self, works: List[Dict], policies: List[Dict] = None):
        """
        Initialize temporal analyzer

        Args:
            works: List of enriched work metadata
            policies: Optional list of policy documents
        """
        self.works = works
        self.policies = policies or []
        self.df_works = pd.DataFrame(works)

        if self.policies:
            self.df_policies = pd.DataFrame(policies)

    def publications_over_time(self) -> Dict:
        """
        Analyze publication trends over time

        Returns:
            Dictionary with temporal publication data
        """
        if 'publication_year' not in self.df_works.columns:
            return {}

        logger.info("Analyzing publications over time...")

        # Clean data
        df = self.df_works[self.df_works['publication_year'].notna()].copy()
        df['publication_year'] = df['publication_year'].astype(int)

        # Count by year
        yearly_counts = df['publication_year'].value_counts().sort_index()

        # Citations by year
        yearly_citations = df.groupby('publication_year')['cited_by_count'].agg(['sum', 'mean', 'count'])

        timeline = []
        for year in sorted(yearly_counts.index):
            timeline.append({
                'year': int(year),
                'publications': int(yearly_counts[year]),
                'total_citations': int(yearly_citations.loc[year, 'sum']) if year in yearly_citations.index else 0,
                'avg_citations': float(yearly_citations.loc[year, 'mean']) if year in yearly_citations.index else 0
            })

        # Calculate growth rates
        if len(timeline) > 1:
            for i in range(1, len(timeline)):
                prev_pubs = timeline[i-1]['publications']
                curr_pubs = timeline[i]['publications']
                growth = ((curr_pubs - prev_pubs) / prev_pubs * 100) if prev_pubs > 0 else 0
                timeline[i]['growth_rate'] = round(growth, 2)

        return {
            'timeline': timeline,
            'total_years': len(timeline),
            'peak_year': int(yearly_counts.idxmax()) if len(yearly_counts) > 0 else None,
            'peak_publications': int(yearly_counts.max()) if len(yearly_counts) > 0 else 0
        }

    def citations_over_time(self) -> Dict:
        """
        Analyze citation trends over time

        Returns:
            Dictionary with temporal citation data
        """
        if 'publication_year' not in self.df_works.columns or 'cited_by_count' not in self.df_works.columns:
            return {}

        logger.info("Analyzing citations over time...")

        df = self.df_works[self.df_works['publication_year'].notna()].copy()
        df['publication_year'] = df['publication_year'].astype(int)

        citation_timeline = []

        for year in sorted(df['publication_year'].unique()):
            year_data = df[df['publication_year'] == year]

            citation_timeline.append({
                'year': int(year),
                'total_citations': int(year_data['cited_by_count'].sum()),
                'avg_citations': float(year_data['cited_by_count'].mean()),
                'median_citations': float(year_data['cited_by_count'].median()),
                'max_citations': int(year_data['cited_by_count'].max()),
                'num_works': len(year_data)
            })

        return {
            'citation_timeline': citation_timeline
        }

    def analyze_research_trends(self) -> Dict:
        """
        Analyze emerging research trends over time

        Returns:
            Dictionary with trend analysis
        """
        if 'publication_year' not in self.df_works.columns:
            return {}

        logger.info("Analyzing research trends...")

        # Analyze concepts over time
        concept_timeline = defaultdict(lambda: defaultdict(int))

        for work in self.works:
            year = work.get('publication_year')
            if not year:
                continue

            concepts = work.get('concepts', [])
            for concept in concepts[:5]:  # Top 5 concepts per paper
                name = concept.get('name', '')
                if name:
                    concept_timeline[name][year] += 1

        # Find emerging topics (increased frequency in recent years)
        if self.df_works['publication_year'].notna().any():
            median_year = self.df_works['publication_year'].median()

            emerging_topics = []
            for concept, years in concept_timeline.items():
                early_count = sum(count for year, count in years.items() if year < median_year)
                late_count = sum(count for year, count in years.items() if year >= median_year)
                total_count = early_count + late_count

                if total_count >= 5:  # Minimum threshold
                    growth = ((late_count - early_count) / early_count * 100) if early_count > 0 else 100
                    emerging_topics.append({
                        'topic': concept,
                        'early_period_count': early_count,
                        'late_period_count': late_count,
                        'total_count': total_count,
                        'growth_rate': round(growth, 2)
                    })

            emerging_topics.sort(key=lambda x: x['growth_rate'], reverse=True)

            return {
                'emerging_topics': emerging_topics[:20],
                'median_year': int(median_year)
            }

        return {}

    def analyze_policy_citations_over_time(self) -> Dict:
        """
        Analyze when policies cite research (policy document timeline)

        Returns:
            Dictionary with policy citation timeline
        """
        if not self.policies:
            return {}

        logger.info("Analyzing policy citations over time...")

        policy_timeline = defaultdict(int)

        for policy in self.policies:
            # Try different date fields
            pub_date = policy.get('publication_date') or policy.get('published_date') or policy.get('date')

            if pub_date:
                try:
                    # Extract year from date string
                    if isinstance(pub_date, str):
                        year = int(pub_date[:4])
                        policy_timeline[year] += 1
                except:
                    continue

        timeline = [
            {'year': year, 'policy_count': count}
            for year, count in sorted(policy_timeline.items())
        ]

        return {
            'policy_timeline': timeline
        }

    def citation_lag_analysis(self) -> Dict:
        """
        Analyze time lag between publication and policy citation

        Returns:
            Dictionary with citation lag statistics
        """
        if not self.policies:
            return {}

        logger.info("Analyzing citation lag...")

        lags = []

        for policy in self.policies:
            policy_year = None
            pub_date = policy.get('publication_date') or policy.get('published_date') or policy.get('date')

            if pub_date:
                try:
                    policy_year = int(pub_date[:4])
                except:
                    continue

            if not policy_year:
                continue

            # Get cited works
            citations = policy.get('citations', [])
            for citation in citations:
                doi = citation.get('doi', '')

                # Find corresponding work
                for work in self.works:
                    if work.get('doi', '').lower() == doi.lower():
                        work_year = work.get('publication_year')
                        if work_year:
                            lag = policy_year - work_year
                            if 0 <= lag <= 50:  # Reasonable range
                                lags.append(lag)
                        break

        if lags:
            import numpy as np

            return {
                'avg_lag_years': float(np.mean(lags)),
                'median_lag_years': float(np.median(lags)),
                'min_lag_years': int(min(lags)),
                'max_lag_years': int(max(lags)),
                'total_citations_analyzed': len(lags)
            }

        return {}

    def generate_temporal_report(self) -> Dict:
        """
        Generate comprehensive temporal analysis report

        Returns:
            Dictionary with all temporal analyses
        """
        logger.info("Generating temporal analysis report...")

        return {
            'publications_over_time': self.publications_over_time(),
            'citations_over_time': self.citations_over_time(),
            'research_trends': self.analyze_research_trends(),
            'policy_timeline': self.analyze_policy_citations_over_time(),
            'citation_lag': self.citation_lag_analysis()
        }
