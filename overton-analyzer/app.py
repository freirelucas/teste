"""
Overton Analyzer Web Application
Main Flask application
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime
import logging

# Import API clients
from backend.api.overton_client import OvertonClient
from backend.api.openalex_client import OpenAlexClient

# Import analysis modules
from backend.analysis.bibliometric import BibliometricAnalyzer
from backend.analysis.network_analysis import NetworkAnalyzer
from backend.analysis.temporal_analysis import TemporalAnalyzer
from backend.analysis.thematic_analysis import ThematicAnalyzer
from backend.analysis.geographic_analysis import GeographicAnalyzer
from backend.analysis.sector_comparison import SectorComparator

# Import config
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Create directories if they don't exist
os.makedirs(Config.REPORTS_DIR, exist_ok=True)
os.makedirs(Config.DATA_DIR, exist_ok=True)


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search():
    """
    Main search endpoint
    Performs complete analysis pipeline
    """
    try:
        data = request.get_json()
        query = data.get('query', Config.DEFAULT_QUERY)
        max_results = data.get('max_results', Config.MAX_RESULTS)
        api_key = data.get('api_key', Config.OVERTON_API_KEY)

        if not api_key:
            return jsonify({'error': 'Overton API key is required'}), 400

        logger.info(f"Starting analysis for query: {query}")

        # Step 1: Search Overton for policies
        logger.info("Step 1: Searching Overton...")
        overton = OvertonClient(api_key)
        policies = overton.search_policies(query, max_results)

        if not policies:
            return jsonify({'error': 'No policies found'}), 404

        # Step 2: Extract DOIs
        logger.info("Step 2: Extracting DOIs...")
        dois = overton.extract_cited_dois(policies)

        if not dois:
            return jsonify({'error': 'No cited works found'}), 404

        # Step 3: Get metadata from OpenAlex
        logger.info("Step 3: Fetching metadata from OpenAlex...")
        openalex = OpenAlexClient()
        works_raw = openalex.get_works_batch(dois[:200])  # Limit for performance

        if not works_raw:
            return jsonify({'error': 'No works metadata found'}), 404

        # Enrich metadata
        works = openalex.enrich_metadata(works_raw)

        # Save raw data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_file = os.path.join(Config.DATA_DIR, f'data_{timestamp}.json')

        with open(data_file, 'w') as f:
            json.dump({
                'query': query,
                'timestamp': timestamp,
                'policies': policies,
                'works': works
            }, f, indent=2)

        # Return initial data
        return jsonify({
            'status': 'success',
            'message': 'Data collected successfully',
            'data': {
                'num_policies': len(policies),
                'num_works': len(works),
                'data_file': data_file,
                'timestamp': timestamp
            }
        })

    except Exception as e:
        logger.error(f"Error in search: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Perform all analyses on collected data
    """
    try:
        data = request.get_json()
        data_file = data.get('data_file')

        if not data_file or not os.path.exists(data_file):
            return jsonify({'error': 'Data file not found'}), 404

        # Load data
        logger.info(f"Loading data from {data_file}")
        with open(data_file, 'r') as f:
            saved_data = json.load(f)

        works = saved_data['works']
        policies = saved_data['policies']

        # Perform analyses
        logger.info("Performing bibliometric analysis...")
        biblio_analyzer = BibliometricAnalyzer(works)
        biblio_report = biblio_analyzer.generate_full_report()

        logger.info("Performing network analysis...")
        network_analyzer = NetworkAnalyzer(works)
        network_graph = network_analyzer.build_cocitation_network(min_connections=2)
        centrality = network_analyzer.calculate_centrality_metrics(network_graph)
        communities = network_analyzer.detect_communities(network_graph)
        network_stats = network_analyzer.network_statistics(network_graph)
        network_viz_data = network_analyzer.get_network_data_for_visualization(network_graph, top_n=50)

        logger.info("Performing temporal analysis...")
        temporal_analyzer = TemporalAnalyzer(works, policies)
        temporal_report = temporal_analyzer.generate_temporal_report()

        logger.info("Performing thematic analysis...")
        thematic_analyzer = ThematicAnalyzer(works)
        thematic_report = thematic_analyzer.generate_thematic_report()

        logger.info("Performing geographic analysis...")
        geo_analyzer = GeographicAnalyzer(works, policies)
        geo_report = geo_analyzer.generate_geographic_report()

        logger.info("Performing sector comparison...")
        sector_comparator = SectorComparator(policies, works)
        sector_report = sector_comparator.generate_sector_comparison_report()

        # Compile full report
        full_report = {
            'metadata': {
                'query': saved_data['query'],
                'timestamp': saved_data['timestamp'],
                'num_policies': len(policies),
                'num_works': len(works)
            },
            'bibliometric': biblio_report,
            'network': {
                'statistics': network_stats,
                'centrality': centrality,
                'communities': communities,
                'visualization_data': network_viz_data
            },
            'temporal': temporal_report,
            'thematic': thematic_report,
            'geographic': geo_report,
            'sector_comparison': sector_report
        }

        # Save report
        report_file = os.path.join(
            Config.REPORTS_DIR,
            f"report_{saved_data['timestamp']}.json"
        )

        with open(report_file, 'w') as f:
            json.dump(full_report, f, indent=2)

        logger.info(f"Analysis complete. Report saved to {report_file}")

        return jsonify({
            'status': 'success',
            'message': 'Analysis completed successfully',
            'report': full_report,
            'report_file': report_file
        })

    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/<format>', methods=['POST'])
def export_report(format):
    """
    Export report in various formats
    """
    try:
        data = request.get_json()
        report_file = data.get('report_file')

        if not report_file or not os.path.exists(report_file):
            return jsonify({'error': 'Report file not found'}), 404

        with open(report_file, 'r') as f:
            report = json.load(f)

        timestamp = report['metadata']['timestamp']

        if format == 'json':
            return send_file(
                report_file,
                mimetype='application/json',
                as_attachment=True,
                download_name=f'overton_report_{timestamp}.json'
            )

        elif format == 'excel':
            # Create Excel file
            import pandas as pd
            from openpyxl import Workbook

            excel_file = os.path.join(
                Config.REPORTS_DIR,
                f'report_{timestamp}.xlsx'
            )

            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # Overview sheet
                overview_data = {
                    'Metric': ['Query', 'Policies', 'Works', 'Timestamp'],
                    'Value': [
                        report['metadata']['query'],
                        report['metadata']['num_policies'],
                        report['metadata']['num_works'],
                        report['metadata']['timestamp']
                    ]
                }
                pd.DataFrame(overview_data).to_excel(writer, sheet_name='Overview', index=False)

                # Top cited works
                if report['bibliometric'].get('top_cited_works'):
                    df_top = pd.DataFrame(report['bibliometric']['top_cited_works'])
                    df_top.to_excel(writer, sheet_name='Top Cited Works', index=False)

                # Countries
                if report['geographic']['country_analysis'].get('top_countries'):
                    df_countries = pd.DataFrame(report['geographic']['country_analysis']['top_countries'])
                    df_countries.to_excel(writer, sheet_name='Countries', index=False)

                # Topics
                if report['thematic']['topic_analysis'].get('top_topics'):
                    df_topics = pd.DataFrame(report['thematic']['topic_analysis']['top_topics'])
                    df_topics.to_excel(writer, sheet_name='Topics', index=False)

                # Sectors
                if report['sector_comparison']['citation_patterns'].get('sector_comparison'):
                    df_sectors = pd.DataFrame(report['sector_comparison']['citation_patterns']['sector_comparison'])
                    df_sectors.to_excel(writer, sheet_name='Sectors', index=False)

            return send_file(
                excel_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'overton_report_{timestamp}.xlsx'
            )

        else:
            return jsonify({'error': f'Format {format} not supported'}), 400

    except Exception as e:
        logger.error(f"Error in export: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/status')
def status():
    """Check API status"""
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'overton_key_configured': bool(Config.OVERTON_API_KEY)
    })


if __name__ == '__main__':
    logger.info("Starting Overton Analyzer Web Application...")
    logger.info(f"Debug mode: {Config.DEBUG}")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
