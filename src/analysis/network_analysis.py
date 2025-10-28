"""
Network analysis for policy-academic citation networks.
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple, Set
from collections import defaultdict, Counter
import community as community_louvain


class CoCitationNetwork:
    """Build and analyze co-citation networks of academic works."""

    def __init__(self, policy_df: pd.DataFrame, min_co_citations: int = 2):
        """
        Initialize co-citation network builder.

        Args:
            policy_df: DataFrame with policy documents and cited DOIs
            min_co_citations: Minimum co-citations to create an edge
        """
        self.policy_df = policy_df
        self.min_co_citations = min_co_citations
        self.graph = None
        self.metrics = {}

    def build_network(self) -> nx.Graph:
        """
        Build co-citation network from policy documents.

        Two academic works are connected if they are cited together
        in the same policy document. Edge weight represents the number
        of policy documents that cite both works together.

        Returns:
            NetworkX graph
        """
        print("\n🌐 Building co-citation network...")

        # Count co-citations
        co_citation_counts = defaultdict(int)

        for _, row in self.policy_df.iterrows():
            cited_dois = row.get('cited_dois', [])

            if not cited_dois or len(cited_dois) < 2:
                continue

            # Create pairs of co-cited works
            for i in range(len(cited_dois)):
                for j in range(i + 1, len(cited_dois)):
                    doi1, doi2 = sorted([cited_dois[i], cited_dois[j]])
                    co_citation_counts[(doi1, doi2)] += 1

        # Build graph
        G = nx.Graph()

        # Add edges with weight
        edges_added = 0
        for (doi1, doi2), weight in co_citation_counts.items():
            if weight >= self.min_co_citations:
                G.add_edge(doi1, doi2, weight=weight)
                edges_added += 1

        self.graph = G

        print(f"  Nodes: {G.number_of_nodes():,} academic works")
        print(f"  Edges: {G.number_of_edges():,} co-citation relationships")
        print(f"  (min co-citations: {self.min_co_citations})")

        return G

    def calculate_metrics(self) -> Dict:
        """
        Calculate network metrics.

        Returns:
            Dictionary of network metrics
        """
        if self.graph is None:
            raise ValueError("Network not built yet. Call build_network() first.")

        G = self.graph

        print("\n📊 Calculating network metrics...")

        metrics = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'density': nx.density(G),
            'num_components': nx.number_connected_components(G),
        }

        # Get largest component
        if G.number_of_nodes() > 0:
            largest_cc = max(nx.connected_components(G), key=len)
            G_largest = G.subgraph(largest_cc).copy()

            metrics['largest_component_size'] = len(largest_cc)
            metrics['largest_component_edges'] = G_largest.number_of_edges()

            # Metrics for largest component
            if G_largest.number_of_nodes() > 1:
                metrics['largest_component_density'] = nx.density(G_largest)
                metrics['average_clustering'] = nx.average_clustering(G_largest)

                # Average shortest path (can be slow for large graphs)
                if G_largest.number_of_nodes() < 1000:
                    try:
                        metrics['average_shortest_path'] = nx.average_shortest_path_length(G_largest)
                        metrics['diameter'] = nx.diameter(G_largest)
                    except:
                        pass

        self.metrics = metrics
        return metrics

    def detect_communities(self) -> Dict[str, int]:
        """
        Detect communities using Louvain method.

        Returns:
            Dictionary mapping node to community ID
        """
        if self.graph is None:
            raise ValueError("Network not built yet. Call build_network() first.")

        print("\n🔍 Detecting communities...")

        # Use Louvain method
        communities = community_louvain.best_partition(self.graph)

        num_communities = len(set(communities.values()))
        print(f"  Found {num_communities} communities")

        # Add to metrics
        self.metrics['num_communities'] = num_communities

        return communities

    def get_central_nodes(
        self,
        top_n: int = 10,
        centrality_type: str = 'degree'
    ) -> List[Tuple[str, float]]:
        """
        Get most central nodes in the network.

        Args:
            top_n: Number of top nodes to return
            centrality_type: Type of centrality ('degree', 'betweenness', 'closeness', 'eigenvector')

        Returns:
            List of (node, centrality) tuples
        """
        if self.graph is None:
            raise ValueError("Network not built yet. Call build_network() first.")

        G = self.graph

        if G.number_of_nodes() == 0:
            return []

        # Calculate centrality
        if centrality_type == 'degree':
            centrality = nx.degree_centrality(G)
        elif centrality_type == 'betweenness':
            centrality = nx.betweenness_centrality(G)
        elif centrality_type == 'closeness':
            # Use largest component for closeness
            largest_cc = max(nx.connected_components(G), key=len)
            G_sub = G.subgraph(largest_cc)
            centrality = nx.closeness_centrality(G_sub)
        elif centrality_type == 'eigenvector':
            try:
                centrality = nx.eigenvector_centrality(G, max_iter=1000)
            except:
                centrality = nx.degree_centrality(G)  # Fallback
        else:
            centrality = nx.degree_centrality(G)

        # Sort and return top nodes
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]

    def get_network_summary(self) -> str:
        """
        Get a summary of the network analysis.

        Returns:
            Formatted summary string
        """
        if not self.metrics:
            self.calculate_metrics()

        summary = []
        summary.append("\n" + "=" * 80)
        summary.append("CO-CITATION NETWORK SUMMARY")
        summary.append("=" * 80)

        m = self.metrics

        summary.append(f"\nNetwork Structure:")
        summary.append(f"  Nodes (academic works): {m['num_nodes']:,}")
        summary.append(f"  Edges (co-citations): {m['num_edges']:,}")
        summary.append(f"  Density: {m['density']:.4f}")
        summary.append(f"  Connected components: {m['num_components']:,}")

        if 'largest_component_size' in m:
            summary.append(f"\nLargest Component:")
            summary.append(f"  Size: {m['largest_component_size']:,} nodes")
            summary.append(f"  Edges: {m['largest_component_edges']:,}")
            if 'largest_component_density' in m:
                summary.append(f"  Density: {m['largest_component_density']:.4f}")
            if 'average_clustering' in m:
                summary.append(f"  Average clustering: {m['average_clustering']:.4f}")
            if 'average_shortest_path' in m:
                summary.append(f"  Average shortest path: {m['average_shortest_path']:.2f}")
            if 'diameter' in m:
                summary.append(f"  Diameter: {m['diameter']}")

        if 'num_communities' in m:
            summary.append(f"\nCommunities:")
            summary.append(f"  Number of communities detected: {m['num_communities']}")

        return "\n".join(summary)


class CitationNetwork:
    """Build and analyze policy-to-academic citation networks."""

    def __init__(self, policy_df: pd.DataFrame):
        """
        Initialize citation network builder.

        Args:
            policy_df: DataFrame with policy documents and cited DOIs
        """
        self.policy_df = policy_df
        self.graph = None

    def build_network(self) -> nx.DiGraph:
        """
        Build directed citation network.

        Policy documents cite academic works (policy -> academic).

        Returns:
            NetworkX directed graph
        """
        print("\n🌐 Building citation network...")

        G = nx.DiGraph()

        for _, row in self.policy_df.iterrows():
            policy_id = row.get('policy_document_id', '')
            cited_dois = row.get('cited_dois', [])

            if not policy_id or not cited_dois:
                continue

            # Add edges from policy to academic works
            for doi in cited_dois:
                G.add_edge(policy_id, doi, edge_type='policy_to_academic')

        self.graph = G

        # Count node types
        policy_nodes = [n for n in G.nodes() if not n.startswith('10.')]
        academic_nodes = [n for n in G.nodes() if n.startswith('10.')]

        print(f"  Policy nodes: {len(policy_nodes):,}")
        print(f"  Academic nodes: {len(academic_nodes):,}")
        print(f"  Citation edges: {G.number_of_edges():,}")

        return G

    def get_most_cited_works(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Get most cited academic works.

        Args:
            top_n: Number of top works to return

        Returns:
            List of (DOI, citation_count) tuples
        """
        if self.graph is None:
            raise ValueError("Network not built yet. Call build_network() first.")

        # Count in-degree for academic nodes
        academic_citations = {}
        for node in self.graph.nodes():
            if node.startswith('10.'):  # Academic DOI
                academic_citations[node] = self.graph.in_degree(node)

        # Sort and return top
        sorted_works = sorted(academic_citations.items(), key=lambda x: x[1], reverse=True)
        return sorted_works[:top_n]
