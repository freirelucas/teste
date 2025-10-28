// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Load stats on page load
    loadStats();

    // Allow Enter key to trigger search
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});

async function performSearch() {
    const query = document.getElementById('searchInput').value.trim() || 'agent based models';
    const openAlexEnabled = document.getElementById('sourceOpenAlex').checked;
    const overtonEnabled = document.getElementById('sourceOverton').checked;
    const limit = document.getElementById('limitSelect').value;

    // Determine which sources to query
    let source = 'both';
    if (openAlexEnabled && !overtonEnabled) source = 'openalex';
    if (!openAlexEnabled && overtonEnabled) source = 'overton';
    if (!openAlexEnabled && !overtonEnabled) {
        showError('Please select at least one data source');
        return;
    }

    // Show loading state
    showLoading();
    hideError();
    hideResults();

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&source=${source}&limit=${limit}`);
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            hideLoading();
            return;
        }

        // Display results
        displayResults(data);
        hideLoading();

    } catch (error) {
        showError('Failed to fetch results: ' + error.message);
        hideLoading();
    }
}

function displayResults(data) {
    // Display OpenAlex results
    if (data.openalex && data.openalex.works) {
        displayOpenAlexResults(data.openalex);
        document.getElementById('openalexResults').style.display = 'block';
    } else {
        document.getElementById('openalexResults').style.display = 'none';
    }

    // Display Overton results
    if (data.overton && !data.overton.error) {
        displayOvertonResults(data.overton);
        document.getElementById('overtonResults').style.display = 'block';
    } else if (data.overton && data.overton.error) {
        document.getElementById('overtonResults').style.display = 'block';
        document.getElementById('overtonCount').innerHTML =
            `<span style="color: #ef4444;">${data.overton.message || data.overton.error}</span>`;
        document.getElementById('overtonList').innerHTML = '';
    } else {
        document.getElementById('overtonResults').style.display = 'none';
    }
}

function displayOpenAlexResults(data) {
    const countEl = document.getElementById('openalexCount');
    const listEl = document.getElementById('openalexList');

    countEl.textContent = `Found ${data.count.toLocaleString()} works`;

    if (data.works.length === 0) {
        listEl.innerHTML = '<p>No results found.</p>';
        return;
    }

    listEl.innerHTML = data.works.map(work => `
        <div class="result-card">
            <h3 class="result-title">
                ${work.url ? `<a href="${work.url}" target="_blank">${work.display_name || work.title || 'Untitled'}</a>` : (work.display_name || work.title || 'Untitled')}
            </h3>

            <div class="result-meta">
                ${work.publication_year ? `<span>📅 ${work.publication_year}</span>` : ''}
                ${work.type ? `<span>📄 ${work.type}</span>` : ''}
                ${work.cited_by_count ? `<span>📊 ${work.cited_by_count} citations</span>` : ''}
                ${work.source ? `<span>📚 ${work.source}</span>` : ''}
            </div>

            ${work.authors && work.authors.length > 0 ? `
                <div class="result-authors">
                    <strong>Authors:</strong> ${work.authors.map(a => a.name).filter(n => n).join(', ')}
                </div>
            ` : ''}

            <div class="result-badges">
                ${work.is_open_access ? '<span class="badge badge-success">Open Access</span>' : ''}
                ${work.oa_status ? `<span class="badge badge-info">${work.oa_status.toUpperCase()}</span>` : ''}
                ${work.doi ? `<span class="badge badge-info">DOI</span>` : ''}
            </div>

            ${work.concepts && work.concepts.length > 0 ? `
                <div class="result-concepts">
                    <h4>Key Concepts:</h4>
                    <div class="concept-tags">
                        ${work.concepts.map(c => `
                            <span class="concept-tag">${c.name} (${Math.round(c.score * 100)}%)</span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            ${work.oa_url ? `
                <div style="margin-top: 1rem;">
                    <a href="${work.oa_url}" target="_blank" style="color: var(--success-color);">
                        🔓 Access Open Version
                    </a>
                </div>
            ` : ''}
        </div>
    `).join('');
}

function displayOvertonResults(data) {
    const countEl = document.getElementById('overtonCount');
    const listEl = document.getElementById('overtonList');

    countEl.textContent = `Found ${data.count?.toLocaleString() || 0} documents`;

    if (!data.documents || data.documents.length === 0) {
        listEl.innerHTML = '<p>No results found.</p>';
        return;
    }

    listEl.innerHTML = data.documents.map(doc => `
        <div class="result-card">
            <h3 class="result-title">
                ${doc.url ? `<a href="${doc.url}" target="_blank">${doc.title || 'Untitled'}</a>` : (doc.title || 'Untitled')}
            </h3>

            <div class="result-meta">
                ${doc.year ? `<span>📅 ${doc.year}</span>` : ''}
                ${doc.type ? `<span>📄 ${doc.type}</span>` : ''}
                ${doc.policy_mentions ? `<span>🏛️ ${doc.policy_mentions} policy mentions</span>` : ''}
                ${doc.source ? `<span>📚 ${doc.source}</span>` : ''}
            </div>

            ${doc.authors && doc.authors.length > 0 ? `
                <div class="result-authors">
                    <strong>Authors:</strong> ${doc.authors.join(', ')}
                </div>
            ` : ''}

            ${doc.abstract ? `
                <div class="result-abstract">
                    ${doc.abstract}
                </div>
            ` : ''}

            <div class="result-badges">
                ${doc.doi ? '<span class="badge badge-info">DOI</span>' : ''}
                ${doc.policy_mentions > 0 ? '<span class="badge badge-warning">Policy Impact</span>' : ''}
            </div>

            ${doc.countries && doc.countries.length > 0 ? `
                <div class="result-concepts">
                    <h4>Countries:</h4>
                    <div class="concept-tags">
                        ${doc.countries.map(c => `<span class="concept-tag">${c}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `).join('');
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        if (data.openalex) {
            document.getElementById('openalexStats').innerHTML = `
                <p><strong>Total Works:</strong> ${data.openalex.total_works?.toLocaleString() || 'N/A'}</p>
            `;
        }

        if (data.overton && !data.overton.error) {
            document.getElementById('overtonStats').innerHTML = `
                <p><strong>Total Documents:</strong> ${data.overton.total_documents?.toLocaleString() || 'N/A'}</p>
                <p><strong>Policy Mentions:</strong> ${data.overton.total_policy_mentions?.toLocaleString() || 'N/A'}</p>
            `;
        } else {
            document.getElementById('overtonStats').innerHTML = `
                <p style="color: #ef4444;">Not configured or unavailable</p>
            `;
        }

        document.getElementById('stats').style.display = 'grid';

    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const errorEl = document.getElementById('error');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
}

function hideError() {
    document.getElementById('error').style.display = 'none';
}

function hideResults() {
    document.getElementById('openalexResults').style.display = 'none';
    document.getElementById('overtonResults').style.display = 'none';
}
