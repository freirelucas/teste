#!/usr/bin/env python3
"""
ABM Policy Citation Network Analysis - Main Pipeline

This script orchestrates the complete workflow:
1. Retrieve policy documents from Overton
2. Extract cited academic DOIs
3. Retrieve metadata from OpenAlex
4. Build co-citation network
5. Perform analysis and generate visualizations
6. Export results and reports
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from api.overton_client import OvertonClient
from api.openalex_client import OpenAlexClient
from utils.helpers import (
    load_config,
    load_api_key,
    save_json,
    save_dataframe,
    extract_dois_from_policy_docs,
    format_time
)
from utils.data_processor import PolicyDataProcessor, AcademicDataProcessor
from analysis.network_analysis import CoCitationNetwork, CitationNetwork
from visualization.plots import PolicyVisualizer, AcademicVisualizer, NetworkVisualizer


def print_header(text: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def main():
    """Main execution pipeline."""

    start_time = time.time()

    print_header("ABM POLICY CITATION NETWORK ANALYSIS")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # ========================================================================
    # STEP 1: Load Configuration
    # ========================================================================
    print_header("STEP 1: Loading Configuration")

    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return 1

    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("❌ Overton API key not found!")
        print("   Set OVERTON_API_KEY environment variable or create .env file")
        return 1

    print(f"✓ API key loaded: {api_key[:8]}...{api_key[-4:]}")

    # ========================================================================
    # STEP 2: Retrieve Policy Documents from Overton
    # ========================================================================
    print_header("STEP 2: Retrieving Policy Documents from Overton")

    # Initialize Overton client
    overton = OvertonClient(
        api_key=api_key,
        base_url=config['overton']['base_url'],
        config=config['overton']
    )

    # Validate API key
    print("\nValidating API key...")
    if not overton.validate_api_key():
        print("❌ Invalid API key!")
        return 1
    print("✓ API key valid")

    # Search for policy documents
    query = config['search']['query']
    max_documents = config['search']['max_documents']
    per_page = config['search']['per_page']

    policy_docs = overton.search_by_query(
        query=query,
        max_documents=max_documents,
        per_page=per_page
    )

    if not policy_docs:
        print("❌ No policy documents found!")
        return 1

    print(f"\n✓ Retrieved {len(policy_docs):,} policy documents")

    # Save raw data
    raw_data_path = f"{config['output']['data_dir']}/raw/policy_documents_raw.json"
    save_json(policy_docs, raw_data_path)
    print(f"✓ Saved raw data: {raw_data_path}")

    # ========================================================================
    # STEP 3: Process Policy Documents
    # ========================================================================
    print_header("STEP 3: Processing Policy Documents")

    # Create DataFrame
    policy_df = PolicyDataProcessor.create_dataframe(policy_docs)
    print(f"✓ Created DataFrame: {policy_df.shape[0]} rows, {policy_df.shape[1]} columns")

    # Calculate statistics
    policy_stats = PolicyDataProcessor.get_summary_statistics(policy_df)
    print("\nPolicy Document Statistics:")
    print(f"  Total documents: {policy_stats['total_documents']:,}")
    print(f"  Documents with citations: {policy_stats['documents_with_citations']:,}")
    print(f"  Total citations: {policy_stats['total_citations']:,}")
    print(f"  Mean citations per doc: {policy_stats['mean_citations_per_doc']:.2f}")

    # Save processed data
    policy_csv_path = f"{config['output']['data_dir']}/processed/policy_documents.csv"
    save_dataframe(policy_df, policy_csv_path)
    print(f"\n✓ Saved processed data: {policy_csv_path}")

    # ========================================================================
    # STEP 4: Extract Cited Academic DOIs
    # ========================================================================
    print_header("STEP 4: Extracting Cited Academic DOIs")

    cited_dois = extract_dois_from_policy_docs(policy_docs)
    print(f"✓ Extracted {len(cited_dois):,} unique DOIs")

    if not cited_dois:
        print("⚠️  No cited DOIs found. Skipping OpenAlex and network analysis.")
        cited_dois = []

    # Save DOI list
    doi_list_path = f"{config['output']['data_dir']}/processed/cited_dois.json"
    save_json(cited_dois, doi_list_path)
    print(f"✓ Saved DOI list: {doi_list_path}")

    # ========================================================================
    # STEP 5: Retrieve Metadata from OpenAlex
    # ========================================================================
    if cited_dois:
        print_header("STEP 5: Retrieving Metadata from OpenAlex")

        # Initialize OpenAlex client
        openalex = OpenAlexClient(
            base_url=config['openalex']['base_url'],
            config=config['openalex']
        )

        # Retrieve works metadata
        works_metadata = openalex.get_works_batch(
            dois=cited_dois,
            batch_size=config['processing']['batch_size']
        )

        # Extract metadata
        print("\nExtracting metadata...")
        extracted_metadata = {
            doi: openalex.extract_metadata(work)
            for doi, work in works_metadata.items()
        }

        # Create DataFrame
        academic_df = AcademicDataProcessor.create_dataframe(extracted_metadata)
        print(f"✓ Created academic DataFrame: {academic_df.shape[0]} rows, {academic_df.shape[1]} columns")

        # Calculate statistics
        academic_stats = AcademicDataProcessor.get_summary_statistics(academic_df)
        print("\nAcademic Work Statistics:")
        print(f"  Total DOIs queried: {academic_stats['total_dois']:,}")
        print(f"  Works found: {academic_stats['works_found']:,}")
        print(f"  Works not found: {academic_stats['works_not_found']:,}")
        if academic_stats['works_found'] > 0:
            print(f"  Mean citations: {academic_stats.get('mean_citations', 0):.1f}")
            print(f"  Open access: {academic_stats.get('open_access_percentage', 0):.1f}%")

        # Save academic data
        academic_csv_path = f"{config['output']['data_dir']}/processed/academic_works.csv"
        save_dataframe(academic_df, academic_csv_path)
        print(f"\n✓ Saved academic data: {academic_csv_path}")

        academic_json_path = f"{config['output']['data_dir']}/processed/academic_metadata.json"
        save_json(extracted_metadata, academic_json_path)
        print(f"✓ Saved metadata: {academic_json_path}")

    # ========================================================================
    # STEP 6: Build and Analyze Co-Citation Network
    # ========================================================================
    if cited_dois and len(cited_dois) > 1:
        print_header("STEP 6: Building and Analyzing Co-Citation Network")

        # Build network
        cocitation = CoCitationNetwork(
            policy_df=policy_df,
            min_co_citations=config['analysis']['min_co_citations']
        )

        G_cocitation = cocitation.build_network()

        if G_cocitation.number_of_nodes() > 0:
            # Calculate metrics
            metrics = cocitation.calculate_metrics()

            # Detect communities
            if G_cocitation.number_of_nodes() > 1:
                communities = cocitation.detect_communities()

                # Get central nodes
                print("\n📊 Most central academic works (by degree):")
                central_nodes = cocitation.get_central_nodes(
                    top_n=config['analysis']['top_n'],
                    centrality_type='degree'
                )
                for i, (doi, centrality) in enumerate(central_nodes, 1):
                    print(f"  {i}. {doi} (centrality: {centrality:.4f})")

            # Print summary
            print(cocitation.get_network_summary())

            # Save network data
            network_path = f"{config['output']['data_dir']}/processed/cocitation_network.gml"
            import networkx as nx
            nx.write_gml(G_cocitation, network_path)
            print(f"\n✓ Saved network: {network_path}")

            # Save metrics
            metrics_path = f"{config['output']['results_dir']}/reports/network_metrics.json"
            save_json(metrics, metrics_path)
            print(f"✓ Saved metrics: {metrics_path}")

        else:
            print("⚠️  No co-citation network could be built")

    # ========================================================================
    # STEP 7: Generate Visualizations
    # ========================================================================
    print_header("STEP 7: Generating Visualizations")

    figures_dir = config['output']['figures_dir']

    # Policy visualizations
    print("\nGenerating policy document visualizations...")
    policy_viz = PolicyVisualizer(output_dir=figures_dir)
    policy_viz.plot_countries(policy_df, top_n=config['analysis']['top_n'])
    policy_viz.plot_source_types(policy_df, top_n=config['analysis']['top_n'])
    policy_viz.plot_publication_timeline(policy_df)
    policy_viz.plot_topics(policy_df, top_n=config['analysis']['top_n'])

    # Academic visualizations
    if cited_dois:
        print("\nGenerating academic work visualizations...")
        academic_viz = AcademicVisualizer(output_dir=figures_dir)
        academic_viz.plot_publication_years(academic_df)
        academic_viz.plot_citation_distribution(academic_df)

    # Network visualizations
    if cited_dois and len(cited_dois) > 1 and G_cocitation.number_of_nodes() > 0:
        print("\nGenerating network visualizations...")
        network_viz = NetworkVisualizer(output_dir=figures_dir)

        if G_cocitation.number_of_nodes() > 1:
            network_viz.plot_network(
                G_cocitation,
                communities=communities if G_cocitation.number_of_nodes() > 1 else None,
                max_nodes=500,
                filename='cocitation_network.png'
            )
            network_viz.plot_degree_distribution(G_cocitation)

    # ========================================================================
    # STEP 8: Generate Report
    # ========================================================================
    print_header("STEP 8: Generating Final Report")

    # Compile all statistics
    report = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'search_query': query,
            'processing_time_seconds': time.time() - start_time,
        },
        'policy_documents': policy_stats,
        'cited_works': academic_stats if cited_dois else {},
        'network_analysis': metrics if (cited_dois and len(cited_dois) > 1 and G_cocitation.number_of_nodes() > 0) else {},
        'api_statistics': {
            'overton': overton.get_stats(),
            'openalex': openalex.get_stats() if cited_dois else {},
        }
    }

    # Save report
    report_path = f"{config['output']['results_dir']}/reports/analysis_report.json"
    save_json(report, report_path)
    print(f"✓ Saved report: {report_path}")

    # ========================================================================
    # COMPLETION
    # ========================================================================
    elapsed = time.time() - start_time

    print_header("ANALYSIS COMPLETE")
    print(f"\n✓ Total processing time: {format_time(elapsed)}")
    print(f"✓ Results saved to: {config['output']['results_dir']}/")
    print(f"✓ Data saved to: {config['output']['data_dir']}/")
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
