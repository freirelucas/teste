// Overton Analyzer Main JavaScript

let currentReport = null;
let currentDataFile = null;
let charts = {};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('searchForm').addEventListener('submit', handleSearch);
    checkStatus();
});

// Check API status
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        console.log('API Status:', data);
    } catch (error) {
        console.error('API not available:', error);
    }
}

// Handle search form submission
async function handleSearch(e) {
    e.preventDefault();

    const apiKey = document.getElementById('apiKey').value;
    const query = document.getElementById('query').value;
    const maxResults = parseInt(document.getElementById('maxResults').value);

    if (!apiKey) {
        alert('Please enter your Overton API key');
        return;
    }

    // Show progress
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    setProgress(10, 'Searching Overton database...');

    // Disable button
    const btn = document.getElementById('searchBtn');
    btn.disabled = true;
    document.getElementById('searchBtnText').style.display = 'none';
    document.getElementById('searchBtnLoader').style.display = 'inline-block';

    try {
        // Step 1: Search and collect data
        setProgress(20, 'Collecting policy documents...');
        const searchResponse = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey, query: query, max_results: maxResults })
        });

        if (!searchResponse.ok) {
            const error = await searchResponse.json();
            throw new Error(error.error || 'Search failed');
        }

        const searchData = await searchResponse.json();
        currentDataFile = searchData.data.data_file;

        setProgress(50, `Found ${searchData.data.num_policies} policies citing ${searchData.data.num_works} works. Analyzing...`);

        // Step 2: Perform analysis
        setProgress(60, 'Running bibliometric analysis...');
        await new Promise(resolve => setTimeout(resolve, 1000));

        const analyzeResponse = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_file: currentDataFile })
        });

        if (!analyzeResponse.ok) {
            const error = await analyzeResponse.json();
            throw new Error(error.error || 'Analysis failed');
        }

        const analyzeData = await analyzeResponse.json();
        currentReport = analyzeData.report;

        setProgress(100, 'Analysis complete!');

        // Display results
        await new Promise(resolve => setTimeout(resolve, 500));
        displayResults(currentReport);

    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
        document.getElementById('progressSection').style.display = 'none';
    } finally {
        // Re-enable button
        btn.disabled = false;
        document.getElementById('searchBtnText').style.display = 'inline';
        document.getElementById('searchBtnLoader').style.display = 'none';
    }
}

// Set progress
function setProgress(percent, text) {
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressText').textContent = text;
}

// Display results
function displayResults(report) {
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('progressSection').style.display = 'none';

    // Overview
    displayOverview(report);

    // Bibliometric
    displayBibliometric(report.bibliometric);

    // Network
    displayNetwork(report.network);

    // Temporal
    displayTemporal(report.temporal);

    // Thematic
    displayThematic(report.thematic);

    // Geographic
    displayGeographic(report.geographic);

    // Sectors
    displaySectors(report.sector_comparison);

    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

// Display overview
function displayOverview(report) {
    const stats = report.bibliometric.basic_statistics;
    const meta = report.metadata;

    const html = `
        <div class="stat-item">
            <div class="stat-value">${meta.num_policies}</div>
            <div class="stat-label">Policy Documents</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${meta.num_works}</div>
            <div class="stat-label">Research Works</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${stats.total_citations || 0}</div>
            <div class="stat-label">Total Citations</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${stats.h_index || 0}</div>
            <div class="stat-label">H-Index</div>
        </div>
    `;

    document.getElementById('overviewStats').innerHTML = html;
}

// Display bibliometric analysis
function displayBibliometric(data) {
    // Basic stats
    const stats = data.basic_statistics;
    const statsHtml = `
        <table>
            <tr><td><strong>Total Works:</strong></td><td>${stats.total_works}</td></tr>
            <tr><td><strong>Total Citations:</strong></td><td>${stats.total_citations}</td></tr>
            <tr><td><strong>Average Citations:</strong></td><td>${stats.avg_citations.toFixed(2)}</td></tr>
            <tr><td><strong>H-Index:</strong></td><td>${stats.h_index}</td></tr>
            <tr><td><strong>Open Access:</strong></td><td>${stats.open_access_percentage.toFixed(1)}%</td></tr>
            <tr><td><strong>Year Range:</strong></td><td>${stats.earliest_year} - ${stats.latest_year}</td></tr>
        </table>
    `;
    document.getElementById('basicStats').innerHTML = statsHtml;

    // Top cited works
    if (data.top_cited_works && data.top_cited_works.length > 0) {
        const topCitedHtml = '<ul class="result-list">' +
            data.top_cited_works.slice(0, 10).map(work => `
                <li>
                    <strong>${work.title || 'Untitled'}</strong><br>
                    <small>Year: ${work.publication_year || 'N/A'} | Citations: ${work.cited_by_count || 0}</small>
                </li>
            `).join('') + '</ul>';
        document.getElementById('topCited').innerHTML = topCitedHtml;
    }

    // Top authors
    if (data.author_analysis && data.author_analysis.top_authors) {
        const authorsHtml = '<ul class="result-list">' +
            data.author_analysis.top_authors.slice(0, 10).map(author => `
                <li>
                    <strong>${author.name}</strong><br>
                    <small>Works: ${author.works_count} | Citations: ${author.total_citations}</small>
                </li>
            `).join('') + '</ul>';
        document.getElementById('topAuthors').innerHTML = authorsHtml;
    }

    // Institutions chart
    if (data.institution_analysis && data.institution_analysis.top_institutions) {
        const institutions = data.institution_analysis.top_institutions.slice(0, 10);
        createBarChart('institutionsChart',
            institutions.map(i => i.name.substring(0, 30)),
            institutions.map(i => i.count),
            'Top Institutions'
        );
    }
}

// Display network analysis
function displayNetwork(data) {
    // Network stats
    if (data.statistics) {
        const stats = data.statistics;
        const statsHtml = `
            <table>
                <tr><td><strong>Nodes:</strong></td><td>${stats.num_nodes}</td></tr>
                <tr><td><strong>Edges:</strong></td><td>${stats.num_edges}</td></tr>
                <tr><td><strong>Density:</strong></td><td>${(stats.density * 100).toFixed(2)}%</td></tr>
                <tr><td><strong>Avg Degree:</strong></td><td>${stats.avg_degree.toFixed(2)}</td></tr>
                <tr><td><strong>Connected:</strong></td><td>${stats.is_connected ? 'Yes' : 'No'}</td></tr>
                <tr><td><strong>Components:</strong></td><td>${stats.num_components}</td></tr>
            </table>
        `;
        document.getElementById('networkStats').innerHTML = statsHtml;
    }

    // Central nodes (PageRank)
    if (data.centrality && data.centrality.pagerank) {
        const centralHtml = '<ul class="result-list">' +
            data.centrality.pagerank.slice(0, 10).map(node => `
                <li>
                    <strong>Node:</strong> ${node.id.substring(0, 50)}<br>
                    <small>PageRank: ${node.score.toFixed(4)}</small>
                </li>
            `).join('') + '</ul>';
        document.getElementById('centralNodes').innerHTML = centralHtml;
    }

    // Network visualization (simplified)
    if (data.visualization_data) {
        visualizeNetwork(data.visualization_data);
    }
}

// Display temporal analysis
function displayTemporal(data) {
    // Timeline chart
    if (data.publications_over_time && data.publications_over_time.timeline) {
        const timeline = data.publications_over_time.timeline;
        createLineChart('timelineChart',
            timeline.map(t => t.year),
            [
                { label: 'Publications', data: timeline.map(t => t.publications), borderColor: '#3498db' },
                { label: 'Total Citations', data: timeline.map(t => t.total_citations), borderColor: '#e74c3c' }
            ],
            'Publications and Citations Over Time'
        );
    }

    // Emerging topics
    if (data.research_trends && data.research_trends.emerging_topics) {
        const topicsHtml = '<table><tr><th>Topic</th><th>Early</th><th>Late</th><th>Growth</th></tr>' +
            data.research_trends.emerging_topics.slice(0, 15).map(topic => `
                <tr>
                    <td>${topic.topic}</td>
                    <td>${topic.early_period_count}</td>
                    <td>${topic.late_period_count}</td>
                    <td><span class="badge badge-success">+${topic.growth_rate.toFixed(1)}%</span></td>
                </tr>
            `).join('') + '</table>';
        document.getElementById('emergingTopics').innerHTML = topicsHtml;
    }
}

// Display thematic analysis
function displayThematic(data) {
    // Topics chart
    if (data.topic_analysis && data.topic_analysis.top_topics) {
        const topics = data.topic_analysis.top_topics.slice(0, 15);
        createBarChart('topicsChart',
            topics.map(t => t.name.substring(0, 25)),
            topics.map(t => t.count),
            'Top Research Topics'
        );
    }

    // SDG chart
    if (data.sdg_coverage && data.sdg_coverage.sdg_distribution) {
        const sdgs = data.sdg_coverage.sdg_distribution.slice(0, 10);
        if (sdgs.length > 0) {
            createPieChart('sdgChart',
                sdgs.map(s => s.name),
                sdgs.map(s => s.count),
                'SDG Coverage'
            );
        }
    }

    // Topic co-occurrence
    if (data.topic_cooccurrence && data.topic_cooccurrence.length > 0) {
        const cooccHtml = '<table><tr><th>Topic 1</th><th>Topic 2</th><th>Count</th></tr>' +
            data.topic_cooccurrence.slice(0, 20).map(pair => `
                <tr>
                    <td>${pair.topic1}</td>
                    <td>${pair.topic2}</td>
                    <td>${pair.count}</td>
                </tr>
            `).join('') + '</table>';
        document.getElementById('topicCooccurrence').innerHTML = cooccHtml;
    }
}

// Display geographic analysis
function displayGeographic(data) {
    // Countries chart
    if (data.country_analysis && data.country_analysis.top_countries) {
        const countries = data.country_analysis.top_countries.slice(0, 15);
        createBarChart('countriesChart',
            countries.map(c => c.country),
            countries.map(c => c.publications),
            'Top Countries by Publications'
        );
    }

    // Regions chart
    if (data.regional_distribution && data.regional_distribution.regional_distribution) {
        const regions = data.regional_distribution.regional_distribution;
        createPieChart('regionsChart',
            regions.map(r => r.region),
            regions.map(r => r.publications),
            'Regional Distribution'
        );
    }

    // Collaborations
    if (data.international_collaboration && data.international_collaboration.top_collaborations) {
        const collabHtml = '<table><tr><th>Country 1</th><th>Country 2</th><th>Collaborations</th></tr>' +
            data.international_collaboration.top_collaborations.slice(0, 15).map(collab => `
                <tr>
                    <td>${collab.country1}</td>
                    <td>${collab.country2}</td>
                    <td>${collab.count}</td>
                </tr>
            `).join('') + '</table>';
        document.getElementById('collaborations').innerHTML = collabHtml;
    }
}

// Display sector comparison
function displaySectors(data) {
    // Sector distribution chart
    if (data.sector_distribution && data.sector_distribution.sector_distribution) {
        const sectors = data.sector_distribution.sector_distribution;
        createPieChart('sectorDistChart',
            sectors.map(s => s.sector),
            sectors.map(s => s.count),
            'Policy Distribution by Sector'
        );
    }

    // Citation patterns
    if (data.citation_patterns && data.citation_patterns.sector_comparison) {
        const citHtml = '<table><tr><th>Sector</th><th>Policies</th><th>Citations</th><th>Avg/Policy</th></tr>' +
            data.citation_patterns.sector_comparison.map(sector => `
                <tr>
                    <td><strong>${sector.sector}</strong></td>
                    <td>${sector.policy_count}</td>
                    <td>${sector.total_citations}</td>
                    <td>${sector.avg_citations_per_policy.toFixed(2)}</td>
                </tr>
            `).join('') + '</table>';
        document.getElementById('sectorCitations').innerHTML = citHtml;
    }

    // Sector topics
    if (data.sector_topics && data.sector_topics.sector_topics) {
        let topicsHtml = '<div class="analysis-grid">';
        for (const [sector, topics] of Object.entries(data.sector_topics.sector_topics)) {
            if (topics.length > 0) {
                topicsHtml += `
                    <div class="analysis-item">
                        <h5>${sector}</h5>
                        <ul class="result-list">
                            ${topics.slice(0, 5).map(t => `<li>${t.topic} (${t.count})</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
        }
        topicsHtml += '</div>';
        document.getElementById('sectorTopics').innerHTML = topicsHtml;
    }
}

// Chart creation helpers
function createBarChart(canvasId, labels, data, title) {
    const ctx = document.getElementById(canvasId);
    if (charts[canvasId]) charts[canvasId].destroy();

    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: data,
                backgroundColor: '#3498db'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } }
        }
    });
}

function createPieChart(canvasId, labels, data, title) {
    const ctx = document.getElementById(canvasId);
    if (charts[canvasId]) charts[canvasId].destroy();

    charts[canvasId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
                    '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#d35400'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: { title: { display: true, text: title } }
        }
    });
}

function createLineChart(canvasId, labels, datasets, title) {
    const ctx = document.getElementById(canvasId);
    if (charts[canvasId]) charts[canvasId].destroy();

    charts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets.map(ds => ({
                ...ds,
                fill: false,
                tension: 0.1
            }))
        },
        options: {
            responsive: true,
            plugins: { title: { display: true, text: title } }
        }
    });
}

// Network visualization (simplified with D3.js)
function visualizeNetwork(data) {
    const container = document.getElementById('networkViz');
    container.innerHTML = ''; // Clear previous

    if (!data.nodes || data.nodes.length === 0) {
        container.innerHTML = '<p style="padding: 20px; text-align: center;">No network data available</p>';
        return;
    }

    const width = container.clientWidth;
    const height = 600;

    const svg = d3.select('#networkViz')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.edges).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

    // Draw edges
    const link = svg.append('g')
        .selectAll('line')
        .data(data.edges)
        .enter().append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.weight || 1));

    // Draw nodes
    const node = svg.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .enter().append('circle')
        .attr('r', d => 5 + Math.sqrt(d.citations || 0) / 2)
        .attr('fill', '#3498db')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    // Add tooltips
    node.append('title')
        .text(d => `${d.label}\nYear: ${d.year}\nCitations: ${d.citations}`);

    // Update positions
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
    });

    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
}

// Export report
async function exportReport(format) {
    if (!currentReport) {
        alert('No report available to export');
        return;
    }

    try {
        const response = await fetch(`/api/export/${format}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                report_file: currentReport.report_file || currentDataFile
            })
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        // Download file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `overton_report_${Date.now()}.${format === 'excel' ? 'xlsx' : format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        console.error('Export error:', error);
        alert('Error exporting report: ' + error.message);
    }
}
