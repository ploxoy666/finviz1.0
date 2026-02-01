// OpenBB Dashboard Logic

const searchInput = document.getElementById('global-ticker-input');
let currentTicker = 'AAPL';
let tvWidget = null;
let charts = {};

// Initialize
window.onload = () => {
    loadDashboard(currentTicker);

    // Input Handler
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const ticker = searchInput.value.trim().toUpperCase();
            if (ticker) {
                loadDashboard(ticker);
            }
        }
    });
};

async function loadDashboard(ticker) {
    currentTicker = ticker;
    searchInput.value = ticker;

    // Reset Loaders
    document.querySelectorAll('.loading-overlay').forEach(el => el.style.display = 'flex');

    // 1. Initialize/Update TradingView Widget immediately
    updateTradingView(ticker);

    // 2. Fetch Data Parallel
    Promise.allSettled([
        loadQuote(ticker),
        loadHistory(ticker),
        loadProfile(ticker),
        loadFinancials(ticker),
        loadSegments(ticker),
        loadValuation(ticker),
        loadEarnings(ticker),
        loadDividends(ticker)
    ]).then(() => {
        // console.log("Dashboard Updated");
    });
}

async function loadValuation(ticker) {
    try {
        const res = await fetch(`${API_BASE_URL}/valuation/${ticker}`);
        const data = await res.json();

        if (data.error) return;

        const ctx = document.getElementById('valuation-canvas').getContext('2d');
        if (charts['valuation']) charts['valuation'].destroy();

        charts['valuation'] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [
                    { label: 'P/E Ratio', data: data.pe, borderColor: '#3b82f6', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                    { label: 'P/S Ratio', data: data.ps, borderColor: '#f97316', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                    { label: 'P/B Ratio', data: data.pb, borderColor: '#22c55e', borderWidth: 2, pointRadius: 0, tension: 0.2 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        bottom: 20,
                        top: 10,
                        left: 10,
                        right: 10
                    }
                },
                plugins: {
                    legend: { labels: { color: '#e5e7eb' } },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    x: { ticks: { color: '#9ca3af', maxTicksLimit: 8 }, grid: { display: false } },
                    y: { ticks: { color: '#9ca3af' }, grid: { color: '#374151' } }
                }
            }
        });
        document.querySelector('#widget-valuation .loading-overlay').style.display = 'none';

    } catch (e) { console.error(e); }
}

async function loadSegments(ticker) {
    try {
        const res = await fetch(`${API_BASE_URL}/segments/${ticker}`);
        const data = await res.json();

        // Render Geography
        renderStackedChart('geo-canvas', data.years, data.geography, 'geo');
        document.querySelector('#widget-geo .loading-overlay').style.display = 'none';

        // Render Business
        renderStackedChart('bus-canvas', data.years, data.business, 'bus');
        document.querySelector('#widget-bus .loading-overlay').style.display = 'none';

    } catch (e) { console.error(e); }
}

function renderStackedChart(canvasId, labels, datasetData, keyPrefix) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (charts[keyPrefix]) charts[keyPrefix].destroy();

    // Generate colors
    const colors = ['#3b82f6', '#f97316', '#22c55e', '#a855f7', '#ec4899', '#eab308'];

    const datasets = Object.keys(datasetData).map((k, i) => ({
        label: k,
        data: datasetData[k],
        backgroundColor: colors[i % colors.length],
        borderWidth: 0, // No border
        borderRadius: 2, // Slight rounding
    }));

    charts[keyPrefix] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    bottom: 20, // Prevent date cutoff
                    top: 15,
                    left: 5,
                    right: 5
                }
            },
            scales: {
                x: {
                    stacked: true,
                    grid: { display: false },
                    ticks: {
                        color: '#9ca3af',
                        font: { size: 11 },
                        padding: 5
                    }
                },
                y: {
                    stacked: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9ca3af', font: { size: 10 } }
                }
            },
            plugins: {
                legend: { position: 'top', align: 'end', labels: { color: '#e5e7eb', boxWidth: 10, font: { size: 11 } } }
            },
            barPercentage: 0.6,
            categoryPercentage: 0.8
        }
    });
}

function updateTradingView(ticker) {
    if (document.getElementById('tradingview-container')) {
        document.getElementById('tradingview-container').innerHTML = "";

        new TradingView.widget({
            "autosize": true,
            "symbol": ticker,
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#15191e",
            "enable_publishing": false,
            "hide_top_toolbar": false,
            "hide_legend": false,
            "save_image": false,
            "container_id": "tradingview-container",
            "backgroundColor": "rgba(21, 25, 30, 1)",
            "gridColor": "rgba(255, 255, 255, 0.05)",
            "allow_symbol_change": true
        });
    }
}

// 1. Ticker Info (Price, Sparkline, Metrics, Stats)
async function loadQuote(ticker) {
    try {
        const res = await fetch(`${API_BASE_URL}/quote/${ticker}`);
        const data = await res.json();
        const f = data.fundament || {};

        // 1.1 Header Info (Price & Change)
        const price = parseFloat(f.Price) || 0;
        const changeStr = f.Change || '0%';
        const changeVal = parseFloat(changeStr);
        const isUp = changeVal >= 0;

        const changeDollar = (price * (changeVal / 100)).toFixed(2); // Approx calc

        const headerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                <div>
                    <div style="font-size:0.9rem; color:var(--text-gray); font-weight:600;">${f.Company || ticker}</div>
                    <div class="ticker-main-price">$${f.Price}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.8rem; color:var(--text-gray);">Day's Change</div>
                    <div class="ticker-change" style="color: ${isUp ? 'var(--text-success)' : 'var(--text-danger)'}">
                        ${isUp ? '▲' : '▼'} ${changeDollar} (${changeStr})
                    </div>
                </div>
            </div>
            <div style="font-size:0.8rem; color:var(--text-gray); margin-bottom:10px;">
                Volume: <span style="color:var(--text-white); font-weight:600">${f.Volume || '-'}</span>
                <span style="margin:0 8px">|</span>
                ${f.Sector || '-'} | ${f.Industry || '-'}
            </div>
        `;
        document.getElementById('ticker-header-content').innerHTML = headerHTML;

        // 1.2 Key Metrics Widget
        document.getElementById('metrics-content').innerHTML = `
            <table class="clean-table">
                <tr><td>Beta</td><td>${f.Beta || '-'}</td></tr>
                <tr><td>Vol Avg</td><td>${f['Avg Volume'] || '-'}</td></tr>
                <tr><td>Market Cap</td><td>${f['Market Cap'] || '-'}</td></tr>
                <tr><td>PE Ratio</td><td>${f['P/E'] || '-'}</td></tr>
                <tr><td>EPS (ttm)</td><td>${f['EPS (ttm)'] || '-'}</td></tr>
                <tr><td>Dividend %</td><td>${f['Dividend %'] || '-'}</td></tr>
                <tr style="border-top: 1px solid var(--border-subtle)"><td>52W High</td><td>${f['52W High'] || '-'}</td></tr>
                <tr><td>52W Low</td><td>${f['52W Low'] || '-'}</td></tr>
            </table>
        `;

        // 1.3 Share Stats Widget
        document.getElementById('stats-content').innerHTML = `
            <table class="clean-table">
                <tr><td>Shares Out</td><td>${f['Shs Outstand'] || '-'}</td></tr>
                <tr><td>Float</td><td>${f['Shs Float'] || '-'}</td></tr>
                <tr><td>Insider Own</td><td>${f['Insider Own'] || '-'}</td></tr>
                <tr><td>Inst Own</td><td>${f['Inst Own'] || '-'}</td></tr>
                <tr><td>Short Float</td><td>${f['Short Float'] || '-'}</td></tr>
                <tr><td>Short Ratio</td><td>${f['Short Ratio'] || '-'}</td></tr>
                <tr><td>Rec</td><td>${f['Recom'] || '-'}</td></tr>
                <tr><td>Target Price</td><td>${f['Target Price'] || '-'}</td></tr>
            </table>
        `;

        // Hide Loaders
        document.querySelector('#widget-ticker-info .loading-overlay').style.display = 'none';
        document.querySelector('#widget-metrics .loading-overlay').style.display = 'none';
        document.querySelector('#widget-stats .loading-overlay').style.display = 'none';

    } catch (e) {
        console.error("Quote Error", e);
    }
}

// 2. Sparkline (History) - Simple Area Chart
async function loadHistory(ticker) {
    try {
        const res = await fetch(`${API_BASE_URL}/history/${ticker}`);
        const data = await res.json();

        if (data.error) return;

        // Sparkline is mostly just the last month or so for "Ticker Info" context
        const prices = data.prices.slice(-30);
        const labels = data.dates.slice(-30);

        const ctx = document.getElementById('sparkline-canvas').getContext('2d');
        if (charts['spark']) charts['spark'].destroy();

        if (!prices.length) return;

        const isUp = prices[prices.length - 1] >= prices[0];
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const padding = (maxPrice - minPrice) * 0.2; // Increase padding for visibility

        charts['spark'] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    data: prices,
                    borderColor: isUp ? '#00ff9d' : '#ff4d4d',
                    borderWidth: 2,
                    backgroundColor: isUp ? 'rgba(0, 255, 157, 0.1)' : 'rgba(255, 77, 77, 0.1)',
                    fill: true,
                    pointRadius: 0,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                scales: {
                    x: { display: false },
                    y: {
                        display: false,
                        min: minPrice - padding,
                        max: maxPrice + padding
                    }
                },
                layout: {
                    padding: {
                        bottom: 10,
                        top: 10,
                        left: 5,
                        right: 5
                    }
                }
            }
        });

    } catch (e) { console.error(e); }
}

// 3. Profile & Management
async function loadProfile(ticker) {
    try {
        const res = await fetch(`${API_BASE_URL}/company_profile/${ticker}`);
        const data = await res.json();

        // Profile Description
        let descHTML = `
            <div style="margin-bottom:10px;">
                <h3 style="color:var(--text-white);font-size:1rem;margin-bottom:4px;">${currentTicker}</h3>
                <div>${data.address || ''}, ${data.city}</div>
                <div><a href="${data.website}" target="_blank" style="color:var(--primary-blue)">${data.website}</a></div>
            </div>
            <div style="margin-bottom:10px;">
                <strong>Sector:</strong> ${data.sector} <br>
                <strong>Industry:</strong> ${data.industry} <br>
                <strong>Employees:</strong> ${data.fullTimeEmployees}
            </div>
            <div style="border-top:1px solid var(--border-subtle); padding-top:10px;">
                <strong>Description</strong><br>
                ${data.longBusinessSummary}
            </div>
        `;
        document.getElementById('profile-content').innerHTML = descHTML;

        // Management Table
        let mgmtHTML = `<table class="clean-table"><thead><tr><th>Name</th><th>Title</th><th>Pay</th></tr></thead><tbody>`;
        if (data.management && data.management.length > 0) {
            data.management.forEach(m => {
                mgmtHTML += `<tr>
                    <td>${m.name}</td>
                    <td style="font-size:0.75rem; color:var(--text-gray)">${m.title}</td>
                    <td>${m.pay}</td>
                </tr>`;
            });
        } else {
            mgmtHTML += `<tr><td colspan="3">No data</td></tr>`;
        }
        mgmtHTML += `</tbody></table>`;
        document.getElementById('management-container').innerHTML = mgmtHTML;

        document.querySelector('#widget-profile .loading-overlay').style.display = 'none';
        document.querySelector('#widget-management .loading-overlay').style.display = 'none';

    } catch (e) { console.error(e); }
}

// Store financial data globally for tab switching
let financialData = {
    income: null,
    balance: null,
    cash: null
};

// 4. Financials & Revenue Chart & Full Table
async function loadFinancials(ticker) {
    try {
        const res = await fetch(`${API_BASE_URL}/financials/${ticker}`);
        const data = await res.json();
        const income = data.income_statement;

        // Store for switcher
        financialData.income = data.income_statement;
        financialData.balance = data.balance_sheet;
        financialData.cash = data.cash_flow;

        if (income) {
            // Updated: Populate the new Full Width Financial Table (Default: Income)
            renderFinancialTable(financialData.income, 'financials-full-table-container');

            // Old small table (Keep or remove? User wants the big one. Let's keep it for compatibility or remove if unused)
            // Table
            const metrics = Object.keys(income);
            const dates = Object.keys(income[metrics[0]]).sort().reverse();
            const keyM = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income', 'EBITDA', 'Basic EPS'];

            let html = `<table class="clean-table"><thead><tr><th>Metric</th>`;
            dates.slice(0, 5).forEach(d => html += `<th>${d.substring(0, 4)}</th>`);
            html += `</tr></thead><tbody>`;
            keyM.forEach(m => {
                let realKey = metrics.find(k => k.includes(m));
                if (!realKey) return;
                html += `<tr><td>${m}</td>`;
                dates.slice(0, 5).forEach(d => html += `<td>${formatMoney(income[realKey][d])}</td>`);
                html += `</tr>`;
            });
            html += `</tbody></table>`;
            document.getElementById('financials-table-container').innerHTML = html;

            // Revenue Chart (Stacked Style Lookalike)
            renderRevenueChart(income);
        }

        document.querySelector('#widget-financials .loading-overlay').style.display = 'none';
        document.querySelector('#widget-revenue .loading-overlay').style.display = 'none';
        if (document.querySelector('#widget-financials-full .loading-overlay'))
            document.querySelector('#widget-financials-full .loading-overlay').style.display = 'none';

    } catch (e) { console.error(e); }
}

function renderFinancialTable(dataObj, containerId) {
    if (!dataObj || Object.keys(dataObj).length === 0) {
        document.getElementById(containerId).innerHTML = '<div class="text-secondary" style="padding:10px;">No data available</div>';
        return;
    }

    const metrics = Object.keys(dataObj);
    // Sort dates descending (newest first)
    const dates = Object.keys(dataObj[metrics[0]]).sort().reverse();

    let html = `<table class="clean-table" style="min-width: 100%;">
        <thead>
            <tr>
                <th style="position:sticky; left:0; background:var(--bg-panel); z-index:2;">Index</th>`;

    dates.forEach(d => html += `<th>${d.substring(0, 4)}</th>`);
    html += `</tr></thead><tbody>`;

    metrics.forEach(metric => {
        html += `<tr>
            <td style="position:sticky; left:0; background:var(--bg-panel); border-right:1px solid var(--border-subtle); font-weight:500;">${metric}</td>`;
        dates.forEach(d => {
            let val = dataObj[metric][d];
            // Simple formatting
            if (typeof val === 'number') {
                if (metric.includes('Ratio') || metric.includes('Margin') || metric.includes('%')) val = (val * 100).toFixed(2) + '%';
                else val = formatMoney(val);
            }
            html += `<td>${val}</td>`;
        });
        html += `</tr>`;
    });

    html += `</tbody></table>`;
    document.getElementById(containerId).innerHTML = html;
}

function switchFinancialTable(type, btn) {
    // Update active button state
    document.querySelectorAll('#widget-financials-full .nav-btn-mini').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    // Default to income if data missing
    if (!financialData.income) return;

    const container = 'financials-full-table-container';
    if (type === 'income') renderFinancialTable(financialData.income, container);
    if (type === 'balance') renderFinancialTable(financialData.balance, container);
    if (type === 'cash') renderFinancialTable(financialData.cash, container);
}

function renderRevenueChart(income) {
    const ctx = document.getElementById('revenue-canvas').getContext('2d');
    if (charts['revenue']) charts['revenue'].destroy();

    // Metric Keys
    const revKey = Object.keys(income).find(k => k.includes('Total Revenue'));
    const niKey = Object.keys(income).find(k => k.includes('Net Income')); // Use Net Income for 2nd stack

    if (!revKey) return;

    const dates = Object.keys(income[revKey]).sort();
    const revValues = dates.map(d => income[revKey][d]);
    const niValues = niKey ? dates.map(d => income[niKey][d]) : [];

    charts['revenue'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates.map(d => d.substring(0, 4)),
            datasets: [
                {
                    label: 'Net Income',
                    data: niValues,
                    backgroundColor: '#3b82f6', // OpenBB Blue
                    barPercentage: 0.6,
                    categoryPercentage: 0.8,
                    borderRadius: 2,
                    borderWidth: 0
                },
                {
                    label: 'Revenue',
                    data: revValues,
                    backgroundColor: '#1f2937', // Darker gray-blue
                    barPercentage: 0.6,
                    categoryPercentage: 0.8,
                    borderRadius: 2,
                    borderWidth: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    bottom: 20,
                    top: 10,
                    left: 5,
                    right: 5
                }
            },
            scales: {
                x: {
                    stacked: false,
                    grid: { display: false },
                    ticks: { color: '#9ca3af', font: { size: 11 } }
                },
                // Grouped bars look better actually
                y: { display: false }
            },
            plugins: { legend: { position: 'top', align: 'end', labels: { color: '#8b949e', boxWidth: 10, font: { size: 11 } } } }
        }
    });
}

// 5. Earnings History
async function loadEarnings(ticker) {
    try {
        const res = await fetch(`${API_BASE_URL}/earnings/${ticker}`);
        const data = await res.json();

        if (data.error) return;

        let html = `<table class="clean-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>EPS</th>
                    <th>EPS Est</th>
                    <th>Outcome</th>
                </tr>
            </thead>
            <tbody>`;

        data.forEach(item => {
            const eps = item.eps !== null ? item.eps.toFixed(2) : '-';
            const est = item.eps_est !== null ? item.eps_est.toFixed(2) : '-';
            let color = '';
            let outcome = '-';

            if (item.eps !== null && item.eps_est !== null) {
                if (item.eps >= item.eps_est) {
                    color = 'text-green';
                    outcome = '<span style="color:#00ff9d">beat</span>';
                } else {
                    color = 'text-red';
                    outcome = '<span style="color:#ff4d4d">miss</span>';
                }
            }

            html += `<tr>
                <td>${item.date}</td>
                <td class="${color}">${eps}</td>
                <td>${est}</td>
                <td>${outcome}</td>
            </tr>`;
        });

        html += `</tbody></table>`;
        document.getElementById('earnings-table-container').innerHTML = html;
        if (document.querySelector('#widget-earnings .loading-overlay'))
            document.querySelector('#widget-earnings .loading-overlay').style.display = 'none';

    } catch (e) { console.error('Earnings error', e); }
}

// 6. Dividends
async function loadDividends(ticker) {
    try {
        const res = await fetch(`${API_BASE_URL}/dividends/${ticker}`);
        const data = await res.json();

        if (data.error) return;

        let html = `<table class="clean-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Dividend</th>
                    <th>Payment Date</th>
                </tr>
            </thead>
            <tbody>`;

        if (data.length === 0) {
            html += `<tr><td colspan="3">No dividends found</td></tr>`;
        } else {
            data.forEach(item => {
                html += `<tr>
                    <td>${item.date}</td>
                    <td style="color:#00ff9d">${item.dividend}</td>
                    <td>${item.payment_date}</td>
                </tr>`;
            });
        }

        html += `</tbody></table>`;
        document.getElementById('dividends-table-container').innerHTML = html;
        if (document.querySelector('#widget-dividends .loading-overlay'))
            document.querySelector('#widget-dividends .loading-overlay').style.display = 'none';
    } catch (e) { console.error('Dividends error', e); }
}

function formatMoney(num) {
    if (isNaN(num)) return '-';
    if (Math.abs(num) >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    return num.toLocaleString();
}
