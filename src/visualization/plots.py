"""
Visualization functions for policy and academic data analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np


# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300


class PolicyVisualizer:
    """Create visualizations for policy document data."""

    def __init__(self, output_dir: str = "results/figures"):
        """
        Initialize visualizer.

        Args:
            output_dir: Directory to save figures
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_countries(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
        save: bool = True
    ) -> None:
        """
        Plot top countries by number of policy documents.

        Args:
            df: Policy documents DataFrame
            top_n: Number of top countries to show
            save: Whether to save the figure
        """
        if 'source_country' not in df.columns:
            print("⚠️  'source_country' column not found")
            return

        country_counts = df['source_country'].value_counts().head(top_n)

        if country_counts.empty:
            print("⚠️  No country data available")
            return

        plt.figure(figsize=(12, 6))
        sns.barplot(x=country_counts.values, y=country_counts.index, palette='viridis')
        plt.title(f'Top {top_n} Countries by Policy Documents', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Documents')
        plt.ylabel('Country')
        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'countries.png', bbox_inches='tight')
            print(f"✓ Saved: {self.output_dir / 'countries.png'}")

        plt.close()

    def plot_source_types(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
        save: bool = True
    ) -> None:
        """
        Plot top source types.

        Args:
            df: Policy documents DataFrame
            top_n: Number of top types to show
            save: Whether to save the figure
        """
        if 'source_type' not in df.columns:
            print("⚠️  'source_type' column not found")
            return

        type_counts = df['source_type'].value_counts().head(top_n)

        if type_counts.empty:
            print("⚠️  No source type data available")
            return

        plt.figure(figsize=(12, 6))
        sns.barplot(x=type_counts.values, y=type_counts.index, palette='coolwarm')
        plt.title(f'Top {top_n} Source Types', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Documents')
        plt.ylabel('Source Type')
        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'source_types.png', bbox_inches='tight')
            print(f"✓ Saved: {self.output_dir / 'source_types.png'}")

        plt.close()

    def plot_publication_timeline(
        self,
        df: pd.DataFrame,
        freq: str = 'M',
        save: bool = True
    ) -> None:
        """
        Plot publication timeline.

        Args:
            df: Policy documents DataFrame
            freq: Frequency for aggregation ('M' for monthly, 'Y' for yearly)
            save: Whether to save the figure
        """
        if 'published_date' not in df.columns:
            print("⚠️  'published_date' column not found")
            return

        valid_dates = df['published_date'].dropna()

        if valid_dates.empty:
            print("⚠️  No valid publication dates")
            return

        # Create time series
        counts = valid_dates.value_counts().sort_index()
        counts = counts.resample(freq).sum()

        plt.figure(figsize=(14, 6))
        plt.plot(counts.index, counts.values, linewidth=2, color='steelblue')
        plt.fill_between(counts.index, counts.values, alpha=0.3, color='steelblue')
        plt.title('Policy Documents Published Over Time', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Number of Documents')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'timeline.png', bbox_inches='tight')
            print(f"✓ Saved: {self.output_dir / 'timeline.png'}")

        plt.close()

    def plot_topics(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
        save: bool = True
    ) -> None:
        """
        Plot top topics.

        Args:
            df: Policy documents DataFrame
            top_n: Number of top topics to show
            save: Whether to save the figure
        """
        if 'topics' not in df.columns:
            print("⚠️  'topics' column not found")
            return

        # Flatten topics
        all_topics = []
        for topics in df['topics'].dropna():
            if isinstance(topics, list):
                all_topics.extend(topics)

        if not all_topics:
            print("⚠️  No topics data available")
            return

        topic_counts = pd.Series(all_topics).value_counts().head(top_n)

        plt.figure(figsize=(12, 6))
        sns.barplot(x=topic_counts.values, y=topic_counts.index, palette='magma')
        plt.title(f'Top {top_n} Topics', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Documents')
        plt.ylabel('Topic')
        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'topics.png', bbox_inches='tight')
            print(f"✓ Saved: {self.output_dir / 'topics.png'}")

        plt.close()


class AcademicVisualizer:
    """Create visualizations for academic work data."""

    def __init__(self, output_dir: str = "results/figures"):
        """
        Initialize visualizer.

        Args:
            output_dir: Directory to save figures
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_publication_years(
        self,
        df: pd.DataFrame,
        save: bool = True
    ) -> None:
        """
        Plot distribution of publication years.

        Args:
            df: Academic works DataFrame
            save: Whether to save the figure
        """
        if 'publication_year' not in df.columns:
            print("⚠️  'publication_year' column not found")
            return

        years = df['publication_year'].dropna()

        if years.empty:
            print("⚠️  No publication year data available")
            return

        plt.figure(figsize=(12, 6))
        year_counts = years.value_counts().sort_index()
        plt.bar(year_counts.index, year_counts.values, color='steelblue', alpha=0.7)
        plt.title('Academic Works by Publication Year', fontsize=14, fontweight='bold')
        plt.xlabel('Publication Year')
        plt.ylabel('Number of Works')
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'academic_years.png', bbox_inches='tight')
            print(f"✓ Saved: {self.output_dir / 'academic_years.png'}")

        plt.close()

    def plot_citation_distribution(
        self,
        df: pd.DataFrame,
        save: bool = True
    ) -> None:
        """
        Plot citation distribution.

        Args:
            df: Academic works DataFrame
            save: Whether to save the figure
        """
        if 'cited_by_count' not in df.columns:
            print("⚠️  'cited_by_count' column not found")
            return

        citations = df['cited_by_count'].dropna()

        if citations.empty:
            print("⚠️  No citation data available")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Histogram
        ax1.hist(citations, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
        ax1.set_title('Citation Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Number of Citations')
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3, axis='y')

        # Log scale histogram
        ax2.hist(np.log10(citations + 1), bins=50, color='coral', alpha=0.7, edgecolor='black')
        ax2.set_title('Citation Distribution (Log Scale)', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Log10(Citations + 1)')
        ax2.set_ylabel('Frequency')
        ax2.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'citations_dist.png', bbox_inches='tight')
            print(f"✓ Saved: {self.output_dir / 'citations_dist.png'}")

        plt.close()


class NetworkVisualizer:
    """Create visualizations for network data."""

    def __init__(self, output_dir: str = "results/figures"):
        """
        Initialize visualizer.

        Args:
            output_dir: Directory to save figures
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_network(
        self,
        G: nx.Graph,
        communities: Optional[Dict] = None,
        node_size_attr: Optional[str] = None,
        max_nodes: int = 500,
        save: bool = True,
        filename: str = 'network.png'
    ) -> None:
        """
        Plot network graph.

        Args:
            G: NetworkX graph
            communities: Optional community assignments
            node_size_attr: Optional node attribute for sizing
            max_nodes: Maximum nodes to display (for large graphs)
            save: Whether to save the figure
            filename: Output filename
        """
        if G.number_of_nodes() == 0:
            print("⚠️  Empty graph")
            return

        # For large graphs, use largest component
        if G.number_of_nodes() > max_nodes:
            print(f"⚠️  Graph has {G.number_of_nodes()} nodes. Using largest component...")
            largest_cc = max(nx.connected_components(G), key=len)
            G = G.subgraph(largest_cc).copy()
            print(f"   Largest component: {G.number_of_nodes()} nodes")

        plt.figure(figsize=(16, 12))

        # Layout
        if G.number_of_nodes() < 100:
            pos = nx.spring_layout(G, k=1, iterations=50, seed=42)
        else:
            pos = nx.spring_layout(G, k=0.5, iterations=30, seed=42)

        # Node colors by community
        if communities:
            community_list = [communities.get(node, 0) for node in G.nodes()]
            node_colors = community_list
            cmap = plt.cm.tab20
        else:
            node_colors = 'steelblue'
            cmap = None

        # Node sizes
        if node_size_attr and nx.get_node_attributes(G, node_size_attr):
            node_sizes = [G.nodes[node].get(node_size_attr, 1) * 10 for node in G.nodes()]
        else:
            degrees = dict(G.degree())
            node_sizes = [degrees[node] * 20 for node in G.nodes()]

        # Draw network
        nx.draw_networkx_nodes(
            G, pos,
            node_color=node_colors,
            node_size=node_sizes,
            cmap=cmap,
            alpha=0.7
        )

        nx.draw_networkx_edges(
            G, pos,
            edge_color='gray',
            alpha=0.3,
            width=0.5
        )

        plt.title(f'Network Graph ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)',
                  fontsize=14, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / filename, bbox_inches='tight')
            print(f"✓ Saved: {self.output_dir / filename}")

        plt.close()

    def plot_degree_distribution(
        self,
        G: nx.Graph,
        save: bool = True
    ) -> None:
        """
        Plot degree distribution.

        Args:
            G: NetworkX graph
            save: Whether to save the figure
        """
        degrees = [d for n, d in G.degree()]

        if not degrees:
            print("⚠️  No degree data")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Linear scale
        ax1.hist(degrees, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
        ax1.set_title('Degree Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Degree')
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3, axis='y')

        # Log-log scale
        degree_counts = pd.Series(degrees).value_counts().sort_index()
        ax2.loglog(degree_counts.index, degree_counts.values, 'o-', color='coral', alpha=0.7)
        ax2.set_title('Degree Distribution (Log-Log)', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Degree (log)')
        ax2.set_ylabel('Frequency (log)')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'degree_distribution.png', bbox_inches='tight')
            print(f"✓ Saved: {self.output_dir / 'degree_distribution.png'}")

        plt.close()
