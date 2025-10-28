"""
Sector Comparison Module
Compares policy citation patterns across different sectors
"""

from typing import Dict, List
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class SectorComparator:
    """Compares citation patterns across sectors"""

    def __init__(self, policies: List[Dict], works: List[Dict] = None):
        """
        Initialize sector comparator

        Args:
            policies: List of policy documents
            works: Optional list of enriched work metadata
        """
        self.policies = policies
        self.works = works or []

    def classify_policy_sector(self, policy: Dict) -> str:
        """
        Classify a policy document into a sector

        Args:
            policy: Policy document

        Returns:
            Sector classification
        """
        source = policy.get('source', {})
        source_name = source.get('name', '').lower()
        source_type = source.get('type', '').lower()

        # Classification keywords
        sector_keywords = {
            'government': ['government', 'ministry', 'department', 'parliament', 'congress',
                          'senate', 'federal', 'state', 'municipal', 'national'],
            'think_tank': ['institute', 'foundation', 'center', 'centre', 'think tank',
                          'research center', 'policy center'],
            'academia': ['university', 'college', 'academic', 'school', 'faculty'],
            'private': ['company', 'corporation', 'inc', 'ltd', 'llc', 'consulting',
                       'advisory', 'firm'],
            'ngo': ['ngo', 'non-profit', 'nonprofit', 'charity', 'association',
                   'civil society', 'advocacy'],
            'international': ['united nations', 'world bank', 'imf', 'oecd', 'who',
                            'unesco', 'undp', 'wto', 'european commission', 'eu commission']
        }

        # Check each sector
        for sector, keywords in sector_keywords.items():
            if any(keyword in source_name or keyword in source_type for keyword in keywords):
                return sector

        return 'other'

    def analyze_sector_distribution(self) -> Dict:
        """
        Analyze distribution of policies across sectors

        Returns:
            Dictionary with sector distribution
        """
        logger.info("Analyzing sector distribution...")

        sector_counts = Counter()
        sector_policies = defaultdict(list)

        for policy in self.policies:
            sector = self.classify_policy_sector(policy)
            sector_counts[sector] += 1
            sector_policies[sector].append(policy)

        sector_list = [
            {
                'sector': sector,
                'count': count,
                'percentage': (count / len(self.policies) * 100) if len(self.policies) > 0 else 0
            }
            for sector, count in sector_counts.items()
        ]

        sector_list.sort(key=lambda x: x['count'], reverse=True)

        return {
            'sector_distribution': sector_list,
            'sector_policies': {sector: policies for sector, policies in sector_policies.items()}
        }

    def compare_citation_patterns(self) -> Dict:
        """
        Compare how different sectors cite research

        Returns:
            Dictionary with comparative citation analysis
        """
        logger.info("Comparing citation patterns across sectors...")

        sector_stats = defaultdict(lambda: {
            'policy_count': 0,
            'total_citations': 0,
            'cited_works': set(),
            'topics': Counter(),
            'years': []
        })

        for policy in self.policies:
            sector = self.classify_policy_sector(policy)

            sector_stats[sector]['policy_count'] += 1

            # Count citations
            citations = policy.get('citations', [])
            sector_stats[sector]['total_citations'] += len(citations)

            for citation in citations:
                doi = citation.get('doi', '')
                if doi:
                    sector_stats[sector]['cited_works'].add(doi.lower())

            # Policy year
            pub_date = policy.get('publication_date') or policy.get('published_date') or policy.get('date')
            if pub_date:
                try:
                    year = int(pub_date[:4])
                    sector_stats[sector]['years'].append(year)
                except:
                    pass

        # Calculate metrics
        comparison = []

        for sector, stats in sector_stats.items():
            policy_count = stats['policy_count']

            comparison.append({
                'sector': sector,
                'policy_count': policy_count,
                'total_citations': stats['total_citations'],
                'avg_citations_per_policy': stats['total_citations'] / policy_count if policy_count > 0 else 0,
                'unique_works_cited': len(stats['cited_works']),
                'avg_year': sum(stats['years']) / len(stats['years']) if stats['years'] else None
            })

        comparison.sort(key=lambda x: x['policy_count'], reverse=True)

        return {
            'sector_comparison': comparison
        }

    def analyze_sector_topics(self) -> Dict:
        """
        Analyze which topics are cited by which sectors

        Returns:
            Dictionary with sector-topic analysis
        """
        if not self.works:
            return {}

        logger.info("Analyzing topics by sector...")

        # Build DOI to work mapping
        doi_to_work = {}
        for work in self.works:
            doi = work.get('doi', '').lower()
            if doi:
                doi_to_work[doi] = work

        sector_topics = defaultdict(Counter)

        for policy in self.policies:
            sector = self.classify_policy_sector(policy)

            citations = policy.get('citations', [])
            for citation in citations:
                doi = citation.get('doi', '').lower()

                if doi in doi_to_work:
                    work = doi_to_work[doi]

                    # Extract topics
                    topics = work.get('topics', [])
                    for topic in topics[:3]:  # Top 3 topics
                        topic_name = topic.get('name', '')
                        if topic_name:
                            sector_topics[sector][topic_name] += 1

        # Format results
        sector_topic_analysis = {}

        for sector, topics in sector_topics.items():
            sector_topic_analysis[sector] = [
                {'topic': topic, 'count': count}
                for topic, count in topics.most_common(15)
            ]

        return {
            'sector_topics': sector_topic_analysis
        }

    def analyze_sector_geography(self) -> Dict:
        """
        Analyze geographic patterns by sector

        Returns:
            Dictionary with sector-geography analysis
        """
        logger.info("Analyzing sector geography...")

        sector_countries = defaultdict(Counter)

        for policy in self.policies:
            sector = self.classify_policy_sector(policy)

            source = policy.get('source', {})
            country = source.get('country', '')

            if country:
                sector_countries[sector][country] += 1

        # Format results
        sector_geo_analysis = {}

        for sector, countries in sector_countries.items():
            sector_geo_analysis[sector] = [
                {'country': country, 'count': count}
                for country, count in countries.most_common(10)
            ]

        return {
            'sector_geography': sector_geo_analysis
        }

    def identify_sector_specific_works(self) -> Dict:
        """
        Identify works that are cited primarily by specific sectors

        Returns:
            Dictionary with sector-specific works
        """
        if not self.works:
            return {}

        logger.info("Identifying sector-specific works...")

        # Build DOI to work mapping
        doi_to_work = {}
        for work in self.works:
            doi = work.get('doi', '').lower()
            if doi:
                doi_to_work[doi] = work

        # Track which sectors cite each work
        work_sectors = defaultdict(Counter)

        for policy in self.policies:
            sector = self.classify_policy_sector(policy)

            citations = policy.get('citations', [])
            for citation in citations:
                doi = citation.get('doi', '').lower()
                if doi:
                    work_sectors[doi][sector] += 1

        # Identify sector-specific works (>80% citations from one sector)
        sector_specific = defaultdict(list)

        for doi, sectors in work_sectors.items():
            if doi not in doi_to_work:
                continue

            total_cites = sum(sectors.values())
            if total_cites < 2:  # Minimum threshold
                continue

            for sector, count in sectors.items():
                percentage = (count / total_cites * 100)

                if percentage >= 60:  # 60% threshold
                    work = doi_to_work[doi]
                    sector_specific[sector].append({
                        'title': work.get('title', ''),
                        'doi': doi,
                        'citations_from_sector': count,
                        'total_citations': total_cites,
                        'percentage': round(percentage, 2)
                    })

        # Sort by percentage
        for sector in sector_specific:
            sector_specific[sector].sort(key=lambda x: x['percentage'], reverse=True)
            sector_specific[sector] = sector_specific[sector][:10]  # Top 10

        return {
            'sector_specific_works': dict(sector_specific)
        }

    def generate_sector_comparison_report(self) -> Dict:
        """
        Generate comprehensive sector comparison report

        Returns:
            Dictionary with all sector comparisons
        """
        logger.info("Generating sector comparison report...")

        return {
            'sector_distribution': self.analyze_sector_distribution(),
            'citation_patterns': self.compare_citation_patterns(),
            'sector_topics': self.analyze_sector_topics(),
            'sector_geography': self.analyze_sector_geography(),
            'sector_specific_works': self.identify_sector_specific_works()
        }
