/**
 * Unified MVP - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initVendorScout();
});

// ==================== Vendor Scout ====================

function initVendorScout() {
    const form = document.getElementById('vendor-search-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const keyword = document.getElementById('keyword').value;
        const country = document.getElementById('country').value;

        if (!keyword) {
            alert('Please enter a product keyword');
            return;
        }

        // Show loading
        document.getElementById('loading-state').style.display = 'block';
        document.getElementById('results-section').style.display = 'none';

        try {
            const formData = new FormData();
            formData.append('keyword', keyword);
            formData.append('country', country);

            const response = await fetch('/api/vendor/search', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                displayVendorResults(data.data, keyword, country);
            } else {
                alert('Search failed: ' + (data.message || data.detail || 'Unknown error'));
            }
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            document.getElementById('loading-state').style.display = 'none';
        }
    });

    // Download buttons
    const excelBtn = document.getElementById('download-excel');
    const pdfBtn = document.getElementById('download-pdf');

    if (excelBtn) {
        excelBtn.addEventListener('click', function() {
            const keyword = document.getElementById('keyword').value;
            const country = document.getElementById('country').value;
            window.open(`/api/vendor/download/excel?keyword=${encodeURIComponent(keyword)}&country=${encodeURIComponent(country)}`, '_blank');
        });
    }

    if (pdfBtn) {
        pdfBtn.addEventListener('click', function() {
            const keyword = document.getElementById('keyword').value;
            const country = document.getElementById('country').value;
            window.open(`/api/vendor/download/pdf?keyword=${encodeURIComponent(keyword)}&country=${encodeURIComponent(country)}`, '_blank');
        });
    }
}

function displayVendorResults(vendors, keyword, country) {
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');

    if (vendors.length === 0) {
        resultsContent.innerHTML = '<p class="no-results">No vendors found matching your criteria</p>';
        resultsSection.style.display = 'block';
        return;
    }

    // Summary stats
    const exhibitions = [...new Set(vendors.map(v => v.exhibition).filter(Boolean))];
    const countries = [...new Set(vendors.map(v => v.country).filter(Boolean))];

    let html = '<div class="results-summary">';
    html += `<p><strong>${vendors.length}</strong> vendors found`;
    if (exhibitions.length > 0) {
        html += ` from <strong>${exhibitions.length}</strong> exhibitions`;
    }
    html += ` across <strong>${countries.length}</strong> countries</p>`;
    if (exhibitions.length > 0) {
        html += `<p class="exhibition-tags">Exhibitions: ${exhibitions.map(e => `<span class="tag-exhibition">${escapeHtml(e)}</span>`).join(' ')}</p>`;
    }
    html += '</div>';

    html += '<div class="vendor-grid">';

    vendors.forEach((vendor, index) => {
        const scoreClass = vendor.match_score >= 80 ? 'score-high' :
                          vendor.match_score >= 60 ? 'score-mid' : 'score-low';

        html += `
            <div class="vendor-card">
                <div class="vendor-rank">#${index + 1}</div>
                <h3>${escapeHtml(vendor.name)}</h3>
                <div class="vendor-meta">
                    <span class="vendor-country">${escapeHtml(vendor.country)}</span>
                    ${vendor.exhibition ? `<span class="vendor-exhibition">${escapeHtml(vendor.exhibition)}</span>` : ''}
                </div>
                <div class="vendor-meta">
                    <span class="vendor-score ${scoreClass}">${vendor.match_score}% match</span>
                </div>
                <p class="vendor-products"><strong>Products:</strong> ${escapeHtml(vendor.products)}</p>
                ${vendor.contact ? `<p class="vendor-contact"><strong>Contact:</strong> ${escapeHtml(vendor.contact)}</p>` : ''}
                ${vendor.website ? `<p class="vendor-website"><a href="${escapeHtml(vendor.website)}" target="_blank" rel="noopener">Visit website</a></p>` : ''}
            </div>
        `;
    });

    html += '</div>';

    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';
}

// ==================== Utility Functions ====================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
