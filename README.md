# ABM Policy Citation Network Analysis

A comprehensive Python toolkit for analyzing policy citations of research on Agent-Based Models (ABM) using the Overton and OpenAlex APIs.

## Overview

This project enables researchers to:

1. **Retrieve policy documents** from Overton that mention Agent-Based Models
2. **Extract cited academic works** from these policy documents
3. **Fetch metadata** for cited works from OpenAlex
4. **Build co-citation networks** to identify influential research clusters
5. **Generate visualizations and reports** for policy impact analysis

## Features

- **Automated data collection** from Overton and OpenAlex APIs
- **Robust error handling** with rate limiting and retry logic
- **Comprehensive data processing** and cleaning
- **Network analysis** with community detection
- **Rich visualizations** for publications, citations, and networks
- **Checkpointing** for resumable long-running processes
- **Detailed reporting** with statistics and metrics

## Project Structure

```
.
├── config/
│   └── config.yaml              # Configuration file
├── src/
│   ├── api/
│   │   ├── overton_client.py    # Overton API client
│   │   └── openalex_client.py   # OpenAlex API client
│   ├── analysis/
│   │   └── network_analysis.py  # Network analysis tools
│   ├── utils/
│   │   ├── helpers.py           # Helper functions
│   │   └── data_processor.py    # Data processing utilities
│   └── visualization/
│       └── plots.py             # Visualization functions
├── data/
│   ├── raw/                     # Raw API responses
│   └── processed/               # Processed datasets
├── results/
│   ├── figures/                 # Generated plots
│   └── reports/                 # Analysis reports
├── main.py                      # Main execution script
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Overton API key (request at https://www.overton.io)

### Setup

1. **Clone the repository:**

```bash
git clone <repository-url>
cd teste
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure API key:**

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Overton API key:

```
OVERTON_API_KEY=your_actual_api_key_here
```

### Alternative: Use environment variable

```bash
export OVERTON_API_KEY=your_actual_api_key_here
```

## Configuration

Edit `config/config.yaml` to customize the analysis:

```yaml
# Search query and limits
search:
  query: "agent based models"
  max_documents: 50000
  per_page: 100

# Analysis parameters
analysis:
  top_n: 10
  min_co_citations: 2

# Output directories
output:
  data_dir: "data"
  results_dir: "results"
```

## Usage

### Basic Usage

Run the complete analysis pipeline:

```bash
python main.py
```

This will:
1. Search Overton for policy documents about ABM
2. Extract cited academic DOIs
3. Fetch metadata from OpenAlex
4. Build co-citation network
5. Generate visualizations
6. Create analysis report

### Output

The analysis generates the following outputs:

**Data Files:**
- `data/raw/policy_documents_raw.json` - Raw policy documents
- `data/processed/policy_documents.csv` - Processed policy data
- `data/processed/cited_dois.json` - List of cited DOIs
- `data/processed/academic_works.csv` - Academic work metadata
- `data/processed/cocitation_network.gml` - Network graph

**Visualizations:**
- `results/figures/countries.png` - Top countries
- `results/figures/source_types.png` - Policy source types
- `results/figures/timeline.png` - Publication timeline
- `results/figures/topics.png` - Top topics
- `results/figures/academic_years.png` - Publication years
- `results/figures/citations_dist.png` - Citation distribution
- `results/figures/cocitation_network.png` - Network visualization
- `results/figures/degree_distribution.png` - Network degree distribution

**Reports:**
- `results/reports/analysis_report.json` - Comprehensive statistics
- `results/reports/network_metrics.json` - Network analysis metrics

## API Usage

### Overton API Client

```python
from src.api.overton_client import OvertonClient

# Initialize client
client = OvertonClient(api_key="your_key", base_url="...", config={...})

# Search for documents
documents = client.search_by_query(
    query="agent based models",
    max_documents=1000
)
```

### OpenAlex API Client

```python
from src.api.openalex_client import OpenAlexClient

# Initialize client
client = OpenAlexClient(base_url="...", config={...})

# Get metadata for DOIs
metadata = client.get_works_batch(dois=["10.1234/example", ...])
```

### Network Analysis

```python
from src.analysis.network_analysis import CoCitationNetwork

# Build co-citation network
network = CoCitationNetwork(policy_df, min_co_citations=2)
graph = network.build_network()

# Calculate metrics
metrics = network.calculate_metrics()

# Detect communities
communities = network.detect_communities()

# Get central nodes
central = network.get_central_nodes(top_n=10)
```

## Data Processing

The pipeline processes raw API responses into structured DataFrames:

### Policy Documents DataFrame

Contains:
- `policy_document_id` - Unique identifier
- `title` - Document title
- `url` - Document URL
- `published_date` - Publication date
- `source_name` - Source organization
- `source_country` - Country
- `source_type` - Document type
- `topics` - List of topics
- `sdg_categories` - UN SDG categories
- `cofog_divisions` - COFOG classifications
- `cited_dois` - List of cited DOIs
- `cited_doi_count` - Number of citations

### Academic Works DataFrame

Contains:
- `doi` - Digital Object Identifier
- `title` - Work title
- `publication_year` - Year published
- `type` - Work type
- `cited_by_count` - Citation count
- `is_oa` - Open access status
- `author_count` - Number of authors
- `journal_name` - Journal/venue
- `top_concept` - Primary research area

## Network Analysis

The toolkit builds and analyzes co-citation networks where:

- **Nodes** represent academic works
- **Edges** connect works cited together in policy documents
- **Edge weights** represent the number of co-citations

Metrics calculated:
- Network density
- Connected components
- Average clustering coefficient
- Shortest path length
- Community structure
- Centrality measures (degree, betweenness, closeness, eigenvector)

## Visualization

The toolkit generates publication-quality visualizations:

- Bar charts for distributions (countries, types, topics)
- Time series for publication trends
- Histograms for citation distributions
- Network graphs with community coloring
- Degree distribution plots

## Troubleshooting

### API Rate Limiting

The clients implement automatic rate limiting and retry logic. If you encounter persistent rate limit errors:

1. Reduce `max_documents` in config
2. Increase delays in API configuration
3. Process data in smaller batches

### Memory Issues

For large datasets (>10,000 documents):

1. Process in batches
2. Use checkpointing (implemented in helpers)
3. Limit network visualization to largest component

### Missing Data

Not all policy documents cite academic works, and not all DOIs are in OpenAlex:

- Check `cited_doi_count` to see which documents have citations
- Check `works_found` vs `works_not_found` in statistics
- Consider filtering to documents with citations

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is provided as-is for research purposes.

## Citation

If you use this toolkit in your research, please cite:

```bibtex
@software{abm_policy_analysis,
  title={ABM Policy Citation Network Analysis},
  author={Generated by Claude},
  year={2025},
  url={https://github.com/your-repo/abm-policy-analysis}
}
```

## Acknowledgments

This project uses data from:
- **Overton** (https://www.overton.io) - Policy document database
- **OpenAlex** (https://openalex.org) - Open scholarly metadata

## Support

For issues or questions:
- Open an issue on GitHub
- Check the Overton API documentation: https://docs.overton.io
- Check the OpenAlex API documentation: https://docs.openalex.org

## Version History

- **1.0.0** (2025-01) - Initial release
  - Overton and OpenAlex integration
  - Co-citation network analysis
  - Comprehensive visualizations
  - Automated reporting

## Roadmap

Future enhancements:
- [ ] Interactive network visualizations (Plotly, PyVis)
- [ ] Temporal analysis of policy impact
- [ ] Topic modeling integration
- [ ] Batch processing for very large datasets
- [ ] Dashboard with Streamlit/Dash
- [ ] Export to graph databases (Neo4j)