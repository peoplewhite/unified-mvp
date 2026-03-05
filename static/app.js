/**
 * Unified MVP - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Vendor Scout
    initVendorScout();
    
    // Initialize Credit Scout
    initCreditScout();
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
            alert('請輸入產品關鍵字');
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
                alert('搜尋失敗: ' + data.message);
            }
        } catch (error) {
            alert('發生錯誤: ' + error.message);
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
        resultsContent.innerHTML = '<p class="no-results">⚠️ 沒有找到符合條件的供應商</p>';
        resultsSection.style.display = 'block';
        return;
    }
    
    let html = '<div class="vendor-grid">';
    
    vendors.forEach(vendor => {
        const stars = '★'.repeat(Math.floor(vendor.rating)) + '☆'.repeat(5 - Math.floor(vendor.rating));
        
        html += `
            <div class="vendor-card">
                <h3>${escapeHtml(vendor.name)}</h3>
                <div class="vendor-meta">
                    <span>📍 ${escapeHtml(vendor.country)}</span>
                    <span>🏷️ ${escapeHtml(vendor.category)}</span>
                </div>
                <div class="vendor-meta">
                    <span class="vendor-rating">${stars} ${vendor.rating}</span>
                    <span class="vendor-score">${vendor.match_score}% 匹配</span>
                </div>
                <p><strong>產品:</strong> ${escapeHtml(vendor.products)}</p>
                <p><strong>成立:</strong> ${vendor.established}年 | <strong>聯絡:</strong> ${escapeHtml(vendor.contact)}</p>
            </div>
        `;
    });
    
    html += '</div>';
    
    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';
}

// ==================== Credit Scout ====================

function initCreditScout() {
    const form = document.getElementById('credit-search-form');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const companyName = document.getElementById('company-name').value;
        
        if (!companyName) {
            alert('請輸入公司名稱');
            return;
        }
        
        // Show loading
        document.getElementById('loading-state').style.display = 'block';
        document.getElementById('results-section').style.display = 'none';
        
        try {
            const formData = new FormData();
            formData.append('company_name', companyName);
            
            const response = await fetch('/api/credit/analyze', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                displayCreditResults(data.data);
            } else {
                alert('分析失敗: ' + data.message);
            }
        } catch (error) {
            alert('發生錯誤: ' + error.message);
        } finally {
            document.getElementById('loading-state').style.display = 'none';
        }
    });
    
    // Download button
    const pdfBtn = document.getElementById('download-pdf');
    
    if (pdfBtn) {
        pdfBtn.addEventListener('click', function() {
            const companyName = document.getElementById('company-name').value;
            window.open(`/api/credit/download/pdf?company_name=${encodeURIComponent(companyName)}`, '_blank');
        });
    }
}

function displayCreditResults(report) {
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');
    
    const assessment = report.credit_assessment;
    const companyInfo = report.company_info;
    const financial = report.financial_health;
    
    const riskClass = assessment.risk_color === 'green' ? 'low-risk' : 
                      assessment.risk_color === 'yellow' ? 'medium-risk' : 'high-risk';
    const riskTextClass = assessment.risk_color === 'green' ? 'low' : 
                          assessment.risk_color === 'yellow' ? 'medium' : 'high';
    
    let html = `
        <div class="credit-report">
            <div class="credit-score-display">
                <div class="score-circle ${riskClass}">
                    <span class="score-value">${assessment.credit_score}</span>
                    <span class="score-label">信用評分</span>
                </div>
                <span class="risk-badge ${riskTextClass}">${assessment.risk_level}</span>
            </div>
            
            <div class="report-section">
                <h4>📊 信用評估</h4>
                <table class="info-table">
                    <tr>
                        <td>信用評分</td>
                        <td><strong>${assessment.credit_score}</strong> / 850</td>
                    </tr>
                    <tr>
                        <td>風險等級</td>
                        <td><span class="risk-badge ${riskTextClass}">${assessment.risk_level}</span></td>
                    </tr>
                    <tr>
                        <td>建議信用額度</td>
                        <td>$${assessment.credit_limit_millions.toFixed(2)}M</td>
                    </tr>
                    <tr>
                        <td>建議付款條件</td>
                        <td>${assessment.recommended_credit_period}</td>
                    </tr>
                </table>
            </div>
            
            <div class="report-section">
                <h4>🏢 公司資訊</h4>
                <table class="info-table">
                    <tr>
                        <td>成立年份</td>
                        <td>${companyInfo.year_established} (${companyInfo.years_in_business}年)</td>
                    </tr>
                    <tr>
                        <td>年營業額</td>
                        <td>$${companyInfo.annual_revenue_millions.toFixed(2)}M</td>
                    </tr>
                    <tr>
                        <td>員工人數</td>
                        <td>${companyInfo.employee_count.toLocaleString()}人</td>
                    </tr>
                    <tr>
                        <td>行業別</td>
                        <td>${companyInfo.industry}</td>
                    </tr>
                    <tr>
                        <td>企業類型</td>
                        <td>${companyInfo.business_type}</td>
                    </tr>
                </table>
            </div>
            
            <div class="report-section">
                <h4>💰 財務健康度</h4>
                <table class="info-table">
                    <tr>
                        <td>現有負債</td>
                        <td>$${financial.existing_debt_millions.toFixed(2)}M</td>
                    </tr>
                    <tr>
                        <td>負債營收比</td>
                        <td>${financial.debt_to_revenue_ratio}</td>
                    </tr>
                    <tr>
                        <td>財務穩定度</td>
                        <td>${financial.financial_stability}</td>
                    </tr>
                    <tr>
                        <td>付款紀錄</td>
                        <td>${financial.payment_history}</td>
                    </tr>
                    <tr>
                        <td>現金流狀況</td>
                        <td>${financial.cash_flow}</td>
                    </tr>
                    <tr>
                        <td>盈利能力</td>
                        <td>${financial.profitability}</td>
                    </tr>
                </table>
            </div>
            
            <div class="report-section">
                <h4>⚠️ 風險因素</h4>
                <ul class="risk-factors">
                    ${report.risk_factors.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
                </ul>
            </div>
            
            <div class="recommendation-box">
                <h4>✅ 評估建議</h4>
                <p>${escapeHtml(report.recommendation)}</p>
            </div>
            
            <p style="margin-top: 1rem; text-align: center; color: #6b7280; font-size: 0.9rem;">
                信心指數: ${report.confidence_score}% | 分析時間: ${report.analysis_date}
            </p>
        </div>
    `;
    
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