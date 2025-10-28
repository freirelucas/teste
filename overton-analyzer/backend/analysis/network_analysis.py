"""
Network Analysis Module
Co-citation network analysis and visualization
"""

import networkx as nx
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)


class NetworkAnalyzer:
    """Performs network analysis on citation data"""

    def __init__(self, works: List[Dict]):
        """
        Initialize network analyzer

        Args:
            works: List of enriched work metadata
        """
        self.works = works
        self.graph = nx.Graph()

    def build_cocitation_network(self, min_connections: int = 2) -> nx.Graph:
        """
        Build co-citation network

        Works are connected if they are cited together in policy documents

        Args:
            min_connections: Minimum co-citations to include edge

        Returns:
            NetworkX graph
        """
        logger.info("Building co-citation network...")

        # Build co-citation matrix
        cocitations = defaultdict(int)

        # For each work, find other works cited in same contexts
        work_ids = [work.get('id', '') for work in self.works]

        for i, work1 in enumerate(self.works):
            work1_id = work1.get('id', '')
            if not work1_id:
                continue

            # Add node
            self.graph.add_node(work1_id, **{
                'title': work1.get('title', '')[:50],
                'year': work1.get('publication_year'),
                'citations': work1.get('cited_by_count', 0),
                'authors': ', '.join([a.get('name', '') for a in work1.get('authors', [])[:3]])
            })

            # Check co-citations with other works
            refs1 = set(work1.get('referenced_works', []))

            for j, work2 in enumerate(self.works[i+1:], i+1):
                work2_id = work2.get('id', '')
                if not work2_id:
                    continue

                refs2 = set(work2.get('referenced_works', []))

                # Count shared references
                shared_refs = len(refs1.intersection(refs2))

                if shared_refs >= min_connections:
                    cocitations[(work1_id, work2_id)] = shared_refs

        # Add edges
        for (work1_id, work2_id), weight in cocitations.items():
            if weight >= min_connections:
                self.graph.add_edge(work1_id, work2_id, weight=weight)

        logger.info(f"Network created: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

        return self.graph

    def build_citation_network(self) -> nx.DiGraph:
        """
        Build directed citation network

        Returns:
            Directed NetworkX graph
        """
        logger.info("Building citation network...")

        citation_graph = nx.DiGraph()

        # Add all works as nodes
        for work in self.works:
            work_id = work.get('id', '')
            if not work_id:
                continue

            citation_graph.add_node(work_id, **{
                'title': work.get('title', '')[:50],
                'year': work.get('publication_year'),
                'citations': work.get('cited_by_count', 0)
            })

        # Add citation edges
        for work in self.works:
            work_id = work.get('id', '')
            if not work_id:
                continue

            references = work.get('referenced_works', [])

            for ref_id in references:
                # Only add edge if referenced work is in our dataset
                if citation_graph.has_node(ref_id):
                    citation_graph.add_edge(work_id, ref_id)

        logger.info(f"Citation network: {citation_graph.number_of_nodes()} nodes, {citation_graph.number_of_edges()} edges")

        return citation_graph

    def calculate_centrality_metrics(self, graph: nx.Graph = None) -> Dict:
        """
        Calculate various centrality metrics

        Args:
            graph: NetworkX graph (uses self.graph if None)

        Returns:
            Dictionary of centrality metrics
        """
        if graph is None:
            graph = self.graph

        if graph.number_of_nodes() == 0:
            return {}

        logger.info("Calculating centrality metrics...")

        metrics = {}

        # Degree centrality
        degree_cent = nx.degree_centrality(graph)
        metrics['degree_centrality'] = sorted(
            [{'id': k, 'score': v} for k, v in degree_cent.items()],
            key=lambda x: x['score'],
            reverse=True
        )[:20]

        # Betweenness centrality (if graph is connected enough)
        if graph.number_of_edges() > 0:
            try:
                between_cent = nx.betweenness_centrality(graph)
                metrics['betweenness_centrality'] = sorted(
                    [{'id': k, 'score': v} for k, v in between_cent.items()],
                    key=lambda x: x['score'],
                    reverse=True
                )[:20]
            except:
                metrics['betweenness_centrality'] = []

        # Closeness centrality
        if nx.is_connected(graph):
            close_cent = nx.closeness_centrality(graph)
            metrics['closeness_centrality'] = sorted(
                [{'id': k, 'score': v} for k, v in close_cent.items()],
                key=lambda x: x['score'],
                reverse=True
            )[:20]
        else:
            metrics['closeness_centrality'] = []

        # Eigenvector centrality
        try:
            eigen_cent = nx.eigenvector_centrality(graph, max_iter=1000)
            metrics['eigenvector_centrality'] = sorted(
                [{'id': k, 'score': v} for k, v in eigen_cent.items()],
                key=lambda x: x['score'],
                reverse=True
            )[:20]
        except:
            metrics['eigenvector_centrality'] = []

        # PageRank
        try:
            pagerank = nx.pagerank(graph)
            metrics['pagerank'] = sorted(
                [{'id': k, 'score': v} for k, v in pagerank.items()],
                key=lambda x: x['score'],
                reverse=True
            )[:20]
        except:
            metrics['pagerank'] = []

        return metrics

    def detect_communities(self, graph: nx.Graph = None) -> Dict:
        """
        Detect communities in the network

        Args:
            graph: NetworkX graph (uses self.graph if None)

        Returns:
            Dictionary with community information
        """
        if graph is None:
            graph = self.graph

        if graph.number_of_nodes() == 0:
            return {}

        logger.info("Detecting communities...")

        communities_dict = {}

        # Greedy modularity communities
        try:
            from networkx.algorithms import community

            communities = community.greedy_modularity_communities(graph)

            communities_list = []
            for i, comm in enumerate(communities):
                communities_list.append({
                    'id': i,
                    'size': len(comm),
                    'members': list(comm)[:20]  # Limit members shown
                })

            communities_dict['greedy_modularity'] = {
                'num_communities': len(communities),
                'communities': communities_list,
                'modularity': community.modularity(graph, communities)
            }

        except Exception as e:
            logger.warning(f"Could not detect communities: {e}")
            communities_dict['greedy_modularity'] = {}

        return communities_dict

    def network_statistics(self, graph: nx.Graph = None) -> Dict:
        """
        Calculate network-level statistics

        Args:
            graph: NetworkX graph (uses self.graph if None)

        Returns:
            Dictionary of network statistics
        """
        if graph is None:
            graph = self.graph

        if graph.number_of_nodes() == 0:
            return {}

        stats = {
            'num_nodes': graph.number_of_nodes(),
            'num_edges': graph.number_of_edges(),
            'density': nx.density(graph),
            'is_connected': nx.is_connected(graph),
        }

        # Average degree
        degrees = [d for n, d in graph.degree()]
        stats['avg_degree'] = sum(degrees) / len(degrees) if degrees else 0
        stats['max_degree'] = max(degrees) if degrees else 0

        # Connected components
        if not nx.is_connected(graph):
            components = list(nx.connected_components(graph))
            stats['num_components'] = len(components)
            stats['largest_component_size'] = len(max(components, key=len))
        else:
            stats['num_components'] = 1
            stats['largest_component_size'] = graph.number_of_nodes()

        # Clustering
        stats['avg_clustering'] = nx.average_clustering(graph)

        # Diameter (only if connected)
        if nx.is_connected(graph):
            stats['diameter'] = nx.diameter(graph)
            stats['avg_shortest_path'] = nx.average_shortest_path_length(graph)
        else:
            stats['diameter'] = None
            stats['avg_shortest_path'] = None

        return stats

    def get_network_data_for_visualization(self, graph: nx.Graph = None, top_n: int = 100) -> Dict:
        """
        Prepare network data for visualization

        Args:
            graph: NetworkX graph (uses self.graph if None)
            top_n: Limit to top N nodes by degree

        Returns:
            Dictionary with nodes and edges for visualization
        """
        if graph is None:
            graph = self.graph

        if graph.number_of_nodes() == 0:
            return {'nodes': [], 'edges': []}

        # Get top nodes by degree
        degrees = dict(graph.degree())
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:top_n]
        top_node_ids = [node for node, _ in top_nodes]

        # Create subgraph
        subgraph = graph.subgraph(top_node_ids)

        # Prepare nodes
        nodes = []
        for node_id in subgraph.nodes():
            node_data = graph.nodes[node_id]
            nodes.append({
                'id': node_id,
                'label': node_data.get('title', 'Unknown'),
                'year': node_data.get('year'),
                'citations': node_data.get('citations', 0),
                'degree': degrees.get(node_id, 0)
            })

        # Prepare edges
        edges = []
        for source, target in subgraph.edges():
            edge_data = graph.edges[source, target]
            edges.append({
                'source': source,
                'target': target,
                'weight': edge_data.get('weight', 1)
            })

        return {
            'nodes': nodes,
            'edges': edges,
            'stats': self.network_statistics(subgraph)
        }
