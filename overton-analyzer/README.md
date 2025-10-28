# 🔬 Overton Policy Citation Analyzer - Web Application

A comprehensive web application for analyzing citations of academic research in policy documents, connecting data from **Overton** (policy database) and **OpenAlex** (academic database).

## ✨ Features

### 📊 Comprehensive Analysis
- **Bibliometric Analysis** - Citation statistics, H-index, top works, authors, institutions
- **Co-Citation Network** - Network analysis with centrality metrics and community detection
- **Temporal Analysis** - Publication trends, emerging topics, citation lag analysis
- **Thematic Analysis** - Topic distribution, SDG coverage, multidisciplinary works
- **Geographic Analysis** - Country distribution, international collaboration patterns
- **Sector Comparison** - Compare citation patterns across government, think tanks, academia, and private sector

### 🎯 Interactive Web Interface
- Modern, responsive design
- Real-time progress tracking
- Interactive visualizations (Chart.js + D3.js)
- Tabbed interface for easy navigation
- Export results to JSON and Excel

---

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Overton API key ([Get one here](https://overton.io/))
- Modern web browser

### Installation

1. **Clone or download this repository**

2. **Install dependencies**
```bash
cd overton-analyzer
pip install -r requirements.txt
```

3. **Set your API key** (Optional - can also enter in web interface)
```bash
export OVERTON_API_KEY='your-api-key-here'
```

Or create a `.env` file:
```
OVERTON_API_KEY=your-api-key-here
```

4. **Run the application**
```bash
python app.py
```

5. **Open your browser**
Navigate to: `http://localhost:5000`

---

## 📖 Usage Guide

### Step 1: Configure Search
1. Enter your Overton API key
2. Enter your search query (e.g., "agent based models", "climate change")
3. Set maximum results (10-500)
4. Click "Start Analysis"

### Step 2: Wait for Analysis
The application will:
1. Search Overton for policy documents (20%)
2. Extract cited research DOIs (40%)
3. Fetch metadata from OpenAlex (60%)
4. Perform comprehensive analysis (80%)
5. Generate visualizations (100%)

### Step 3: Explore Results
Navigate through different tabs:
- **📚 Bibliometric** - Citation metrics and statistics
- **🔗 Network** - Co-citation network visualization
- **📈 Temporal** - Trends over time
- **🎯 Thematic** - Topics and themes
- **🌍 Geographic** - Geographic distribution
- **🏛️ Sectors** - Sector comparisons

### Step 4: Export Results
Export your analysis in:
- **JSON** - Full data export
- **Excel** - Multi-sheet spreadsheet with tables

---

## 📁 Project Structure

```
overton-analyzer/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
│
├── backend/
│   ├── api/
│   │   ├── overton_client.py      # Overton API integration
│   │   └── openalex_client.py     # OpenAlex API integration
│   │
│   └── analysis/
│       ├── bibliometric.py         # Bibliometric analysis
│       ├── network_analysis.py     # Network/co-citation analysis
│       ├── temporal_analysis.py    # Temporal analysis
│       ├── thematic_analysis.py    # Thematic analysis
│       ├── geographic_analysis.py  # Geographic analysis
│       └── sector_comparison.py    # Sector comparison
│
├── frontend/
│   ├── templates/
│   │   └── index.html             # Main web interface
│   │
│   └── static/
│       ├── css/
│       │   └── style.css          # Styles
│       └── js/
│           └── main.js            # Frontend logic
│
├── data/                          # Cached data files
└── reports/                       # Generated reports
```

---

## 🔧 API Endpoints

### `POST /api/search`
Search and collect data from Overton and OpenAlex

**Request:**
```json
{
  "api_key": "your-overton-key",
  "query": "agent based models",
  "max_results": 200
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "num_policies": 150,
    "num_works": 180,
    "data_file": "/path/to/data.json"
  }
}
```

### `POST /api/analyze`
Perform comprehensive analysis

**Request:**
```json
{
  "data_file": "/path/to/data.json"
}
```

**Response:**
```json
{
  "status": "success",
  "report": { ... },
  "report_file": "/path/to/report.json"
}
```

### `POST /api/export/<format>`
Export results in specified format (json or excel)

### `GET /api/status`
Check API status

---

## 📊 Analysis Modules

### 1. Bibliometric Analysis
- Total works and citations
- H-index calculation
- Top cited works
- Author productivity and impact
- Institution analysis
- Publication venue analysis
- Collaboration patterns
- Open access statistics

### 2. Co-Citation Network Analysis
- Network construction from co-citations
- Centrality metrics:
  - Degree centrality
  - Betweenness centrality
  - Closeness centrality
  - Eigenvector centrality
  - PageRank
- Community detection
- Network statistics (density, clustering, diameter)
- Interactive network visualization

### 3. Temporal Analysis
- Publications over time
- Citations over time
- Emerging research trends
- Policy citation timeline
- Citation lag analysis (time from publication to policy citation)

### 4. Thematic Analysis
- Topic distribution
- Concept hierarchy analysis
- SDG (Sustainable Development Goals) coverage
- Multidisciplinary work identification
- Topic co-occurrence analysis

### 5. Geographic Analysis
- Country-level publication statistics
- International collaboration patterns
- Regional distribution
- Institution-country mapping
- Policy document geography

### 6. Sector Comparison
- Policy distribution across sectors:
  - Government
  - Think Tanks
  - Academia
  - Private Sector
  - NGOs
  - International Organizations
- Citation pattern comparison
- Sector-specific topics
- Geographic patterns by sector
- Sector-specific highly-cited works

---

## 🎨 Visualizations

The application includes:
- **Bar charts** - Top countries, institutions, topics
- **Pie charts** - Sector distribution, regional distribution, SDGs
- **Line charts** - Publications and citations over time
- **Network graph** - Interactive co-citation network (D3.js)
- **Tables** - Detailed data for all analyses

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# API Settings
OVERTON_API_KEY = 'your-key'
MAX_RESULTS = 500

# Analysis Settings
MIN_CITATIONS = 1
NETWORK_MIN_CONNECTIONS = 2
TOP_N_RESULTS = 50

# Sector Categories
SECTORS = {
    'think_tank': 'Think Tanks',
    'government': 'Government',
    'academia': 'Academia',
    'private': 'Private Sector',
    ...
}
```

---

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production (with Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Optional)
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t overton-analyzer .
docker run -p 5000:5000 -e OVERTON_API_KEY=your-key overton-analyzer
```

---

## 🐛 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "API Key invalid"
- Check your key at [overton.io](https://overton.io/)
- Ensure no extra spaces in the key
- Try setting as environment variable

### Slow performance
- Reduce `max_results` in search
- Limit network visualization to top 50 nodes (already configured)

### Network visualization not showing
- Check browser console for errors
- Ensure D3.js is loading (check internet connection)
- Try refreshing the page

### Export not working
```bash
pip install openpyxl --upgrade
```

---

## 📝 Example Queries

- `"agent based models"`
- `"climate change policy"`
- `"machine learning healthcare"`
- `"renewable energy"`
- `"covid-19 vaccination"`
- `"artificial intelligence ethics"`
- `"sustainable development"`

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional visualization types
- More export formats (PDF reports)
- Real-time analysis updates
- Comparison between multiple queries
- Machine learning predictions
- Dashboard for monitoring queries

---

## 📄 License

MIT License - feel free to use and modify

---

## 🙏 Acknowledgments

- **Overton** - Policy document database
- **OpenAlex** - Open academic metadata
- **Flask** - Web framework
- **Chart.js** - Visualization library
- **D3.js** - Network visualization
- **NetworkX** - Network analysis

---

## 📞 Support

For issues or questions:
1. Check this README
2. Review the code documentation
3. Open an issue on GitHub
4. Consult [Overton API docs](https://docs.overton.io/)
5. Consult [OpenAlex API docs](https://docs.openalex.org/)

---

## 🎯 Roadmap

- [ ] Dashboard for multiple queries
- [ ] Real-time analysis streaming
- [ ] PDF report generation
- [ ] Advanced filtering options
- [ ] User authentication
- [ ] Database integration for caching
- [ ] API rate limiting
- [ ] Batch processing
- [ ] Email notifications
- [ ] Scheduled analysis

---

**Made with ❤️ for research impact analysis**

*Last updated: 2024*
