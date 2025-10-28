"""
Geographic Analysis Module
Analyzes geographic distribution of research
"""

from typing import Dict, List
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)


class GeographicAnalyzer:
    """Performs geographic analysis on research works"""

    def __init__(self, works: List[Dict], policies: List[Dict] = None):
        """
        Initialize geographic analyzer

        Args:
            works: List of enriched work metadata
            policies: Optional list of policy documents
        """
        self.works = works
        self.policies = policies or []

    def analyze_countries(self, top_n: int = 30) -> Dict:
        """
        Analyze research output by country

        Args:
            top_n: Number of top countries to return

        Returns:
            Dictionary with country analysis
        """
        logger.info("Analyzing geographic distribution...")

        country_stats = defaultdict(lambda: {
            'publications': 0,
            'total_citations': 0,
            'works': []
        })

        for work in self.works:
            countries = work.get('countries', [])
            citations = work.get('cited_by_count', 0)
            work_id = work.get('id', '')

            for country in countries:
                if country:
                    country_stats[country]['publications'] += 1
                    country_stats[country]['total_citations'] += citations
                    country_stats[country]['works'].append(work_id)

        # Convert to list
        country_list = [
            {
                'country': country,
                'publications': stats['publications'],
                'total_citations': stats['total_citations'],
                'avg_citations': stats['total_citations'] / stats['publications'] if stats['publications'] > 0 else 0,
                'percentage': (stats['publications'] / len(self.works) * 100) if len(self.works) > 0 else 0
            }
            for country, stats in country_stats.items()
        ]

        country_list.sort(key=lambda x: x['publications'], reverse=True)

        return {
            'total_countries': len(country_list),
            'top_countries': country_list[:top_n],
            'country_distribution': country_list
        }

    def analyze_international_collaboration(self) -> Dict:
        """
        Analyze international collaboration patterns

        Returns:
            Dictionary with collaboration analysis
        """
        logger.info("Analyzing international collaboration...")

        single_country = 0
        multi_country = 0
        country_combinations = Counter()

        for work in self.works:
            countries = work.get('countries', [])
            num_countries = len(countries)

            if num_countries == 1:
                single_country += 1
            elif num_countries > 1:
                multi_country += 1

                # Count country pairs
                for i in range(len(countries)):
                    for j in range(i + 1, len(countries)):
                        pair = tuple(sorted([countries[i], countries[j]]))
                        country_combinations[pair] += 1

        # Top collaborations
        top_collaborations = [
            {
                'country1': pair[0],
                'country2': pair[1],
                'count': count
            }
            for pair, count in country_combinations.most_common(20)
        ]

        return {
            'single_country_works': single_country,
            'multi_country_works': multi_country,
            'international_collab_rate': (multi_country / len(self.works) * 100) if len(self.works) > 0 else 0,
            'top_collaborations': top_collaborations
        }

    def analyze_institutions_by_country(self, top_n: int = 20) -> Dict:
        """
        Analyze top institutions grouped by country

        Args:
            top_n: Number of top institutions per country

        Returns:
            Dictionary with institution analysis by country
        """
        logger.info("Analyzing institutions by country...")

        country_institutions = defaultdict(Counter)

        for work in self.works:
            for author in work.get('authors', []):
                institutions = author.get('institutions', [])

                for inst in institutions:
                    # Try to determine country (simplified, would need better mapping)
                    countries = work.get('countries', [])
                    for country in countries:
                        if country:
                            country_institutions[country][inst] += 1

        # Format results
        results = {}
        for country, institutions in country_institutions.items():
            results[country] = [
                {'institution': inst, 'count': count}
                for inst, count in institutions.most_common(top_n)
            ]

        return results

    def analyze_regional_distribution(self) -> Dict:
        """
        Analyze distribution by world regions

        Returns:
            Dictionary with regional analysis
        """
        logger.info("Analyzing regional distribution...")

        # Simple region mapping (expand as needed)
        region_mapping = {
            'US': 'North America',
            'CA': 'North America',
            'MX': 'North America',

            'GB': 'Europe',
            'DE': 'Europe',
            'FR': 'Europe',
            'IT': 'Europe',
            'ES': 'Europe',
            'NL': 'Europe',
            'CH': 'Europe',
            'SE': 'Europe',
            'NO': 'Europe',
            'DK': 'Europe',
            'BE': 'Europe',
            'AT': 'Europe',
            'PL': 'Europe',

            'CN': 'Asia',
            'JP': 'Asia',
            'IN': 'Asia',
            'KR': 'Asia',
            'SG': 'Asia',
            'TW': 'Asia',
            'HK': 'Asia',

            'AU': 'Oceania',
            'NZ': 'Oceania',

            'BR': 'South America',
            'AR': 'South America',
            'CL': 'South America',
            'CO': 'South America',

            'ZA': 'Africa',
            'KE': 'Africa',
            'NG': 'Africa',
            'EG': 'Africa',
        }

        region_stats = defaultdict(lambda: {
            'publications': 0,
            'countries': set()
        })

        for work in self.works:
            countries = work.get('countries', [])

            for country in countries:
                region = region_mapping.get(country, 'Other')
                region_stats[region]['publications'] += 1
                region_stats[region]['countries'].add(country)

        # Convert to list
        region_list = [
            {
                'region': region,
                'publications': stats['publications'],
                'num_countries': len(stats['countries']),
                'percentage': (stats['publications'] / len(self.works) * 100) if len(self.works) > 0 else 0
            }
            for region, stats in region_stats.items()
        ]

        region_list.sort(key=lambda x: x['publications'], reverse=True)

        return {
            'regional_distribution': region_list
        }

    def analyze_policy_geography(self) -> Dict:
        """
        Analyze geographic distribution of policy documents

        Returns:
            Dictionary with policy geography analysis
        """
        if not self.policies:
            return {}

        logger.info("Analyzing policy document geography...")

        policy_countries = Counter()

        for policy in self.policies:
            # Try to extract country from source
            source = policy.get('source', {})
            country = source.get('country', '')

            if country:
                policy_countries[country] += 1

        policy_list = [
            {'country': country, 'policy_count': count}
            for country, count in policy_countries.most_common(30)
        ]

        return {
            'total_policy_countries': len(policy_countries),
            'policy_by_country': policy_list
        }

    def generate_geographic_report(self) -> Dict:
        """
        Generate comprehensive geographic analysis report

        Returns:
            Dictionary with all geographic analyses
        """
        logger.info("Generating geographic analysis report...")

        return {
            'country_analysis': self.analyze_countries(30),
            'international_collaboration': self.analyze_international_collaboration(),
            'regional_distribution': self.analyze_regional_distribution(),
            'policy_geography': self.analyze_policy_geography()
        }
