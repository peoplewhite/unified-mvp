/**
 * Global Vendor Scout - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    initVendorScout();
});

// ==================== Vendor Scout ====================

function initVendorScout() {
    const form = document.getElementById('vendor-search-form');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const keyword = document.getElementById('keyword').value.trim();
        const country = document.getElementById('country').value.trim();

        if (!keyword) {
            alert('請輸入產品關鍵字');
            return;
        }

        showLoading(true);
        document.getElementById('results-section').style.display = 'none';

        try {
            const formData = new FormData();
            formData.append('keyword', keyword);
            formData.append('country', country);

            const response = await fetch('/api/vendor/search', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.success) {
                displayResults(data.data, keyword, country);
            } else {
                alert('搜尋失敗：' + (data.detail || data.message || '未知錯誤'));
            }
        } catch (error) {
            alert('錯誤：' + error.message);
        } finally {
            showLoading(false);
        }
    });

    document.getElementById('download-excel')?.addEventListener('click', function () {
        const keyword = document.getElementById('keyword').value;
        const country = document.getElementById('country').value;
        window.open(
            `/api/vendor/download/excel?keyword=${encodeURIComponent(keyword)}&country=${encodeURIComponent(country)}`,
            '_blank'
        );
    });

    document.getElementById('download-pdf')?.addEventListener('click', function () {
        const keyword = document.getElementById('keyword').value;
        const country = document.getElementById('country').value;
        window.open(
            `/api/vendor/download/pdf?keyword=${encodeURIComponent(keyword)}&country=${encodeURIComponent(country)}`,
            '_blank'
        );
    });
}

function showLoading(show) {
    document.getElementById('loading-state').style.display = show ? 'block' : 'none';
}

function displayResults(exhibitors, keyword, country) {
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');

    if (!exhibitors || exhibitors.length === 0) {
        resultsContent.innerHTML = `<p class="no-results">找不到符合「${escapeHtml(keyword)}」的參展商，請嘗試其他關鍵字。</p>`;
        resultsSection.style.display = 'block';
        return;
    }

    let html = `
        <div class="results-summary">
            <p>共找到 <strong>${exhibitors.length}</strong> 家參展商
            ｜資料來源：<strong>electronica 2024</strong></p>
        </div>
        <div class="vendor-grid">
    `;

    exhibitors.forEach((ex, index) => {
        const scoreClass = ex.match_score >= 80 ? 'score-high'
            : ex.match_score >= 65 ? 'score-mid' : 'score-low';

        const products = Array.isArray(ex.products)
            ? ex.products.slice(0, 4).join(' · ')
            : (ex.products || '');

        const areas = Array.isArray(ex.application_areas)
            ? ex.application_areas.slice(0, 3).join(' · ')
            : '';

        html += `
            <div class="vendor-card">
                <div class="vendor-card-header">
                    <div class="vendor-rank">#${index + 1}</div>
                    <span class="vendor-score ${scoreClass}">${ex.match_score}%</span>
                </div>
                <h3>${escapeHtml(ex.name)}</h3>
                ${ex.booth ? `<div class="vendor-booth">📍 展位 ${escapeHtml(ex.booth)}</div>` : ''}
                ${ex.description ? `<p class="vendor-desc">${escapeHtml(ex.description.slice(0, 180))}${ex.description.length > 180 ? '…' : ''}</p>` : ''}
                ${products ? `<p class="vendor-products"><strong>產品：</strong>${escapeHtml(products)}</p>` : ''}
                ${areas ? `<p class="vendor-areas"><strong>應用領域：</strong>${escapeHtml(areas)}</p>` : ''}
                <div class="vendor-contact">
                    ${ex.website ? `<a href="${escapeHtml(ex.website)}" target="_blank" rel="noopener" class="contact-link">🌐 官網</a>` : ''}
                    ${ex.email ? `<a href="mailto:${escapeHtml(ex.email)}" class="contact-link">✉️ ${escapeHtml(ex.email)}</a>` : ''}
                    ${ex.phone ? `<span class="contact-link">📞 ${escapeHtml(ex.phone)}</span>` : ''}
                </div>
                ${ex.address ? `<p class="vendor-address">📬 ${escapeHtml(ex.address)}</p>` : ''}
            </div>
        `;
    });

    html += '</div>';
    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ==================== Utility ====================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}
