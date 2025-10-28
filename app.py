from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from services.openalex_service import OpenAlexService
from services.overton_service import OvertonService

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize services
openalex_service = OpenAlexService(email=os.getenv('OPENALEX_EMAIL'))
overton_service = OvertonService(api_key=os.getenv('OVERTON_API_KEY'))

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search():
    """
    Search for research about agent-based models across both APIs
    Query params:
    - q: search query (optional, defaults to 'agent based models')
    - source: 'openalex', 'overton', or 'both' (default: 'both')
    - limit: number of results per source (default: 10)
    """
    query = request.args.get('q', 'agent based models')
    source = request.args.get('source', 'both')
    limit = int(request.args.get('limit', 10))

    results = {
        'query': query,
        'openalex': None,
        'overton': None,
        'error': None
    }

    try:
        if source in ['openalex', 'both']:
            results['openalex'] = openalex_service.search_works(query, limit)

        if source in ['overton', 'both']:
            results['overton'] = overton_service.search_documents(query, limit)

    except Exception as e:
        results['error'] = str(e)

    return jsonify(results)

@app.route('/api/openalex/works/<work_id>')
def get_openalex_work(work_id):
    """Get detailed information about a specific OpenAlex work"""
    try:
        work = openalex_service.get_work(work_id)
        return jsonify(work)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about agent-based models research"""
    try:
        query = 'agent based models'

        # Get basic counts from both sources
        openalex_stats = openalex_service.get_stats(query)
        overton_stats = overton_service.get_stats(query) if overton_service.api_key else None

        return jsonify({
            'openalex': openalex_stats,
            'overton': overton_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'openalex': 'configured',
        'overton': 'configured' if os.getenv('OVERTON_API_KEY') else 'not configured'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
