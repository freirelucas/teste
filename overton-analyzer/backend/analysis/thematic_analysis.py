"""
Thematic Analysis Module
Analyzes research themes and topics
"""

from typing import Dict, List
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)


class ThematicAnalyzer:
    """Performs thematic analysis on research works"""

    def __init__(self, works: List[Dict]):
        """
        Initialize thematic analyzer

        Args:
            works: List of enriched work metadata
        """
        self.works = works

    def analyze_topics(self, top_n: int = 30) -> Dict:
        """
        Analyze research topics distribution

        Args:
            top_n: Number of top topics to return

        Returns:
            Dictionary with topic analysis
        """
        logger.info("Analyzing research topics...")

        topic_stats = defaultdict(lambda: {
            'count': 0,
            'total_score': 0,
            'works': []
        })

        for work in self.works:
            topics = work.get('topics', [])
            work_id = work.get('id', '')

            for topic in topics:
                name = topic.get('name', '')
                score = topic.get('score', 0)

                if name:
                    topic_stats[name]['count'] += 1
                    topic_stats[name]['total_score'] += score
                    topic_stats[name]['works'].append(work_id)

        # Convert to list
        topic_list = [
            {
                'name': name,
                'count': stats['count'],
                'avg_score': stats['total_score'] / stats['count'] if stats['count'] > 0 else 0,
                'percentage': (stats['count'] / len(self.works) * 100) if len(self.works) > 0 else 0
            }
            for name, stats in topic_stats.items()
        ]

        topic_list.sort(key=lambda x: x['count'], reverse=True)

        return {
            'total_topics': len(topic_list),
            'top_topics': topic_list[:top_n]
        }

    def analyze_concepts_hierarchy(self) -> Dict:
        """
        Analyze concepts by hierarchy level

        Returns:
            Dictionary with hierarchical concept analysis
        """
        logger.info("Analyzing concept hierarchy...")

        levels = defaultdict(list)

        for work in self.works:
            concepts = work.get('concepts', [])

            for concept in concepts:
                name = concept.get('name', '')
                level = concept.get('level', 0)
                score = concept.get('score', 0)

                if name:
                    levels[level].append({
                        'name': name,
                        'score': score
                    })

        # Aggregate by level
        level_analysis = {}

        for level, concepts in levels.items():
            concept_counts = Counter(c['name'] for c in concepts)

            top_concepts = [
                {
                    'name': name,
                    'count': count
                }
                for name, count in concept_counts.most_common(20)
            ]

            level_analysis[f'level_{level}'] = {
                'level': level,
                'total_concepts': len(set(c['name'] for c in concepts)),
                'total_occurrences': len(concepts),
                'top_concepts': top_concepts
            }

        return level_analysis

    def analyze_sdg_coverage(self) -> Dict:
        """
        Analyze Sustainable Development Goals coverage

        Returns:
            Dictionary with SDG analysis
        """
        logger.info("Analyzing SDG coverage...")

        sdg_stats = defaultdict(lambda: {
            'count': 0,
            'total_score': 0,
            'works': []
        })

        for work in self.works:
            sdgs = work.get('sdgs', [])
            work_id = work.get('id', '')

            for sdg in sdgs:
                name = sdg.get('display_name', '')
                score = sdg.get('score', 0)

                if name:
                    sdg_stats[name]['count'] += 1
                    sdg_stats[name]['total_score'] += score
                    sdg_stats[name]['works'].append(work_id)

        sdg_list = [
            {
                'name': name,
                'count': stats['count'],
                'avg_score': stats['total_score'] / stats['count'] if stats['count'] > 0 else 0,
                'percentage': (stats['count'] / len(self.works) * 100) if len(self.works) > 0 else 0
            }
            for name, stats in sdg_stats.items()
        ]

        sdg_list.sort(key=lambda x: x['count'], reverse=True)

        return {
            'total_works_with_sdgs': sum(1 for work in self.works if work.get('sdgs')),
            'sdg_coverage_percentage': (sum(1 for work in self.works if work.get('sdgs')) / len(self.works) * 100) if len(self.works) > 0 else 0,
            'sdg_distribution': sdg_list
        }

    def analyze_multidisciplinary_works(self) -> Dict:
        """
        Identify multidisciplinary works based on concept diversity

        Returns:
            Dictionary with multidisciplinary analysis
        """
        logger.info("Analyzing multidisciplinary works...")

        multidisciplinary = []

        for work in self.works:
            concepts = work.get('concepts', [])

            # Count unique top-level concepts
            top_level_concepts = set(
                c.get('name', '')
                for c in concepts
                if c.get('level', 0) <= 1
            )

            num_disciplines = len(top_level_concepts)

            if num_disciplines >= 3:  # Threshold for multidisciplinary
                multidisciplinary.append({
                    'title': work.get('title', ''),
                    'id': work.get('id', ''),
                    'num_disciplines': num_disciplines,
                    'disciplines': list(top_level_concepts),
                    'year': work.get('publication_year'),
                    'citations': work.get('cited_by_count', 0)
                })

        multidisciplinary.sort(key=lambda x: x['num_disciplines'], reverse=True)

        return {
            'total_multidisciplinary': len(multidisciplinary),
            'percentage': (len(multidisciplinary) / len(self.works) * 100) if len(self.works) > 0 else 0,
            'top_multidisciplinary_works': multidisciplinary[:20]
        }

    def topic_cooccurrence(self, min_cooccurrence: int = 3) -> List[Dict]:
        """
        Analyze which topics frequently appear together

        Args:
            min_cooccurrence: Minimum co-occurrences to include

        Returns:
            List of topic pairs with co-occurrence counts
        """
        logger.info("Analyzing topic co-occurrence...")

        cooccurrence = defaultdict(int)

        for work in self.works:
            topics = [t.get('name', '') for t in work.get('topics', [])[:5]]  # Top 5 topics

            # Count pairs
            for i in range(len(topics)):
                for j in range(i + 1, len(topics)):
                    if topics[i] and topics[j]:
                        pair = tuple(sorted([topics[i], topics[j]]))
                        cooccurrence[pair] += 1

        # Filter and format
        cooccurrence_list = [
            {
                'topic1': pair[0],
                'topic2': pair[1],
                'count': count
            }
            for pair, count in cooccurrence.items()
            if count >= min_cooccurrence
        ]

        cooccurrence_list.sort(key=lambda x: x['count'], reverse=True)

        return cooccurrence_list[:50]

    def generate_thematic_report(self) -> Dict:
        """
        Generate comprehensive thematic analysis report

        Returns:
            Dictionary with all thematic analyses
        """
        logger.info("Generating thematic analysis report...")

        return {
            'topic_analysis': self.analyze_topics(30),
            'concept_hierarchy': self.analyze_concepts_hierarchy(),
            'sdg_coverage': self.analyze_sdg_coverage(),
            'multidisciplinary_analysis': self.analyze_multidisciplinary_works(),
            'topic_cooccurrence': self.topic_cooccurrence(3)
        }
