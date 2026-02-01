// API Configuration loaded from config.js

// State Management
const state = {
    currentPage: 'home',
    currentStock: null,
    insiderOption: 'latest',
    watchlist: JSON.parse(localStorage.getItem('watchlist') || '[]'),
    recentActivity: JSON.parse(localStorage.getItem('recentActivity') || '[]'),
    comparisonChart: null
};

// ===== LocalStorage Helpers =====
function saveWatchlist() {
    localStorage.setItem('watchlist', JSON.stringify(state.watchlist));
    updateWatchlistCount();
}

function saveActivity(action, ticker) {
    const activity = {
        action,
        ticker,
        timestamp: new Date().toISOString()
    };
    state.recentActivity.unshift(activity);
    if (state.recentActivity.length > 10) {
        state.recentActivity = state.recentActivity.slice(0, 10);
    }
    localStorage.setItem('recentActivity', JSON.stringify(state.recentActivity));
}

// ===== Navigation =====
function navigateTo(page) {
    state.currentPage = page;

    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    // Show selected page
    const pageElement = document.getElementById(`${page}-page`);
    if (pageElement) {
        pageElement.classList.add('active');
    }

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === page) {
            link.classList.add('active');
        }
    });

    // Load page data if needed
    if (page === 'news') {
        loadNews();
    } else if (page === 'insider') {
        loadInsider('latest');
    } else if (page === 'dashboard') {
        loadDashboard();
    } else if (page === 'watchlist') {
        loadWatchlist();
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ===== Dashboard Functions =====
async function loadDashboard() {
    updateWatchlistCount();
    loadRecentActivity();

    // Load top gainers/losers (simulated - would need real API endpoint)
    setTimeout(() => {
        document.getElementById('top-gainers').innerHTML = `
            <div class="market-stat">
                <span class="stat-label">NVDA</span>
                <span class="stat-value positive">+8.5%</span>
            </div>
            <div class="market-stat">
                <span class="stat-label">AMD</span>
                <span class="stat-value positive">+6.2%</span>
            </div>
        `;

        document.getElementById('top-losers').innerHTML = `
            <div class="market-stat">
                <span class="stat-label">INTC</span>
                <span class="stat-value negative">-4.3%</span>
            </div>
            <div class="market-stat">
                <span class="stat-label">NFLX</span>
                <span class="stat-value negative">-2.1%</span>
            </div>
        `;
    }, 500);
}

function updateWatchlistCount() {
    const countElement = document.getElementById('watchlist-count');
    if (countElement) {
        countElement.textContent = state.watchlist.length;
    }
}

function loadRecentActivity() {
    const activityContainer = document.getElementById('recent-activity');
    if (!activityContainer) return;

    if (state.recentActivity.length === 0) {
        activityContainer.innerHTML = '<p class="text-secondary">No recent activity</p>';
        return;
    }

    activityContainer.innerHTML = state.recentActivity.map(activity => {
        const date = new Date(activity.timestamp);
        return `
            <div class="activity-item">
                <strong>${activity.action}</strong> ${activity.ticker}
                <div class="text-secondary" style="font-size: 0.875rem; margin-top: 0.25rem;">
                    ${date.toLocaleString()}
                </div>
            </div>
        `;
    }).join('');
}

// ===== Watchlist Functions =====
function showAddToWatchlist() {
    document.getElementById('add-watchlist-modal').style.display = 'flex';
    document.getElementById('watchlist-ticker-input').focus();
}

function closeAddToWatchlist() {
    document.getElementById('add-watchlist-modal').style.display = 'none';
    document.getElementById('watchlist-ticker-input').value = '';
}

async function addToWatchlist() {
    const input = document.getElementById('watchlist-ticker-input');
    const ticker = input.value.trim().toUpperCase();

    if (!ticker) {
        alert('Please enter a ticker symbol');
        return;
    }

    if (state.watchlist.includes(ticker)) {
        alert('This stock is already in your watchlist');
        return;
    }

    // Verify ticker exists
    try {
        const response = await fetch(`${API_BASE_URL}/quote/${ticker}`);
        if (!response.ok) {
            throw new Error('Invalid ticker');
        }

        state.watchlist.push(ticker);
        saveWatchlist();
        saveActivity('Added to watchlist', ticker);
        closeAddToWatchlist();
        loadWatchlist();

    } catch (error) {
        alert('Invalid ticker symbol or API error');
    }
}

async function loadWatchlist() {
    const emptyState = document.getElementById('watchlist-empty');
    const content = document.getElementById('watchlist-content');
    const tbody = document.getElementById('watchlist-table-body');

    if (state.watchlist.length === 0) {
        emptyState.style.display = 'block';
        content.style.display = 'none';
        return;
    }

    emptyState.style.display = 'none';
    content.style.display = 'block';
    tbody.innerHTML = '<tr><td colspan="8" class="text-center">Loading...</td></tr>';

    // Load data for each stock
    const stocksData = [];
    for (const ticker of state.watchlist) {
        try {
            const response = await fetch(`${API_BASE_URL}/quote/${ticker}`);
            const data = await response.json();
            stocksData.push({
                ticker,
                data: data.fundament
            });
        } catch (error) {
            console.error(`Error loading ${ticker}:`, error);
        }
    }

    tbody.innerHTML = stocksData.map(stock => {
        const f = stock.data;

        // Calculate change in dollars
        const price = parseFloat(f.Price) || 0;
        const prevClose = parseFloat(f['Prev Close']) || 0;
        const changeDollar = price - prevClose;
        const changeDollarStr = changeDollar >= 0 ? `+$${changeDollar.toFixed(2)}` : `-$${Math.abs(changeDollar).toFixed(2)}`;

        // Get change percentage (from 'Change' field which actually contains percentage)
        const changePercent = f.Change || 'N/A';

        // Determine color class based on change
        const changeClass = changeDollar >= 0 ? 'positive' : 'negative';

        return `
            <tr class="watchlist-row ${changeClass}">
                <td><strong>${stock.ticker}</strong></td>
                <td>${f.Company || 'N/A'}</td>
                <td class="price-cell">$${f.Price || 'N/A'}</td>
                <td class="${changeClass}">${changeDollarStr}</td>
                <td class="${changeClass}">${changePercent}</td>
                <td>${f.Volume || 'N/A'}</td>
                <td>${f['Market Cap'] || 'N/A'}</td>
                <td>
                    <button class="action-btn" onclick="searchStockByTicker('${stock.ticker}')" title="View Details">
                        👁️
                    </button>
                    <button class="action-btn delete" onclick="removeFromWatchlist('${stock.ticker}')" title="Remove">
                        🗑️
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function removeFromWatchlist(ticker) {
    if (confirm(`Remove ${ticker} from watchlist?`)) {
        state.watchlist = state.watchlist.filter(t => t !== ticker);
        saveWatchlist();
        saveActivity('Removed from watchlist', ticker);
        loadWatchlist();
    }
}

// ===== Compare Functions =====
async function compareStocks() {
    const ticker1 = document.getElementById('compare-ticker-1').value.trim().toUpperCase();
    const ticker2 = document.getElementById('compare-ticker-2').value.trim().toUpperCase();
    const ticker3 = document.getElementById('compare-ticker-3').value.trim().toUpperCase();

    if (!ticker1 || !ticker2) {
        alert('Please enter at least 2 tickers to compare');
        return;
    }

    const tickers = [ticker1, ticker2];
    if (ticker3) tickers.push(ticker3);

    document.getElementById('compare-loading').style.display = 'block';
    document.getElementById('compare-results').style.display = 'none';

    try {
        const stocksData = [];
        for (const ticker of tickers) {
            const response = await fetch(`${API_BASE_URL}/quote/${ticker}`);
            const data = await response.json();
            if (!response.ok) throw new Error(`Failed to load ${ticker}`);
            stocksData.push({ ticker, data: data.fundament });
        }

        displayComparison(stocksData);
        saveActivity('Compared stocks', tickers.join(', '));

    } catch (error) {
        alert('Error loading comparison data: ' + error.message);
    } finally {
        document.getElementById('compare-loading').style.display = 'none';
    }
}

function displayComparison(stocksData) {
    document.getElementById('compare-results').style.display = 'block';

    // Create comparison table
    const table = document.getElementById('comparison-table');
    const metrics = ['Price', 'Change', 'Change %', 'Volume', 'Market Cap', 'P/E', 'EPS (ttm)',
        'Dividend %', '52W High', '52W Low', 'Avg Volume'];

    let html = '<thead><tr><th>Metric</th>';
    stocksData.forEach(stock => {
        html += `<th>${stock.ticker}</th>`;
    });
    html += '</tr></thead><tbody>';

    metrics.forEach(metric => {
        html += `<tr><td>${metric}</td>`;
        stocksData.forEach(stock => {
            const value = stock.data[metric] || 'N/A';
            const isChange = metric.includes('Change');
            const className = isChange && parseFloat(value) >= 0 ? 'positive' : isChange && parseFloat(value) < 0 ? 'negative' : '';
            html += `<td class="${className}">${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody>';
    table.innerHTML = html;

    // Create chart
    createComparisonChart(stocksData);
}

function createComparisonChart(stocksData) {
    const ctx = document.getElementById('comparison-chart');

    // Destroy previous chart if exists
    if (state.comparisonChart) {
        state.comparisonChart.destroy();
    }

    const labels = stocksData.map(s => s.ticker);
    const prices = stocksData.map(s => parseFloat(s.data.Price?.replace('$', '').replace(',', '')) || 0);
    const volumes = stocksData.map(s => {
        const vol = s.data.Volume?.replace(/[KMB]/g, match => {
            return match === 'K' ? '000' : match === 'M' ? '000000' : '000000000';
        });
        return parseFloat(vol?.replace(',', '')) || 0;
    });

    state.comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Price ($)',
                data: prices,
                backgroundColor: 'rgba(99, 102, 241, 0.6)',
                borderColor: 'rgba(99, 102, 241, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#a1a1aa'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#a1a1aa'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// ===== Stock Quote Functions =====
async function searchStock() {
    const ticker = document.getElementById('ticker-input').value.trim().toUpperCase();

    if (!ticker) {
        showError('Please enter a stock ticker');
        return;
    }

    state.currentStock = ticker;

    // Show loading
    document.getElementById('stock-loading').style.display = 'block';
    document.getElementById('stock-error').style.display = 'none';
    document.getElementById('stock-results').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/quote/${ticker}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch stock data');
        }

        displayStockData(data);
        loadStockNews(ticker);
        loadStockInsider(ticker);
        loadStockRatings(ticker);
        saveActivity('Searched stock', ticker);

    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById('stock-loading').style.display = 'none';
    }
}

function displayStockData(data) {
    const { ticker, fundament, description, peers, etf_holders } = data;

    document.getElementById('stock-results').style.display = 'block';
    document.getElementById('stock-ticker').textContent = ticker;
    document.getElementById('stock-company').textContent = fundament.Company || ticker;

    const priceSection = document.getElementById('stock-price-section');
    priceSection.innerHTML = `
        <div class="metric-item">
            <div class="metric-label">Price</div>
            <div class="metric-value">${fundament.Price || 'N/A'}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Change</div>
            <div class="metric-value ${parseFloat(fundament.Change) >= 0 ? 'positive' : 'negative'}">
                ${fundament.Change || 'N/A'}
            </div>
        </div>
    `;

    document.getElementById('stock-description').textContent = description || 'No description available';

    const keyMetrics = document.getElementById('key-metrics');
    const metrics = [
        { label: 'Market Cap', value: fundament['Market Cap'] },
        { label: 'P/E', value: fundament['P/E'] },
        { label: 'EPS', value: fundament['EPS (ttm)'] },
        { label: 'Dividend', value: fundament['Dividend %'] },
        { label: 'Volume', value: fundament.Volume },
        { label: '52W High', value: fundament['52W High'] },
        { label: '52W Low', value: fundament['52W Low'] },
        { label: 'Avg Volume', value: fundament['Avg Volume'] }
    ];

    keyMetrics.innerHTML = metrics.map(m => `
        <div class="metric-item">
            <div class="metric-label">${m.label}</div>
            <div class="metric-value">${m.value || 'N/A'}</div>
        </div>
    `).join('');

    const peersContainer = document.getElementById('stock-peers');
    if (peers && peers.length > 0) {
        peersContainer.innerHTML = peers.map(peer =>
            `<span class="peer-badge" onclick="searchStockByTicker('${peer}')">${peer}</span>`
        ).join('');
    } else {
        peersContainer.innerHTML = '<p class="text-secondary">No peer data available</p>';
    }

    const etfContainer = document.getElementById('stock-etf');
    if (etf_holders && etf_holders.length > 0) {
        etfContainer.innerHTML = etf_holders.map(etf =>
            `<span class="peer-badge">${etf}</span>`
        ).join('');
    } else {
        etfContainer.innerHTML = '<p class="text-secondary">No ETF holder data available</p>';
    }

    const fundamentalsGrid = document.getElementById('fundamentals-grid');
    fundamentalsGrid.innerHTML = Object.entries(fundament).map(([key, value]) => `
        <div class="metric-item">
            <div class="metric-label">${key}</div>
            <div class="metric-value">${value || 'N/A'}</div>
        </div>
    `).join('');
}

function searchStockByTicker(ticker) {
    document.getElementById('ticker-input').value = ticker;
    navigateTo('quote');
    setTimeout(() => searchStock(), 100);
}

async function loadStockNews(ticker) {
    try {
        const response = await fetch(`${API_BASE_URL}/quote/${ticker}/news`);
        const data = await response.json();

        const newsContainer = document.getElementById('stock-news-list');

        if (data.news && data.news.length > 0) {
            newsContainer.innerHTML = data.news.map(item => `
                <div class="news-card" onclick="window.open('${item.Link}', '_blank')">
                    <div class="news-title">${item.Title}</div>
                    <div class="news-meta">
                        <span>${item.Date || ''}</span>
                    </div>
                </div>
            `).join('');
        } else {
            newsContainer.innerHTML = '<p class="text-secondary">No news available</p>';
        }
    } catch (error) {
        console.error('Error loading news:', error);
    }
}

async function loadStockInsider(ticker) {
    try {
        const response = await fetch(`${API_BASE_URL}/quote/${ticker}/insider`);
        const data = await response.json();

        const insiderContainer = document.getElementById('stock-insider-table');

        if (data.insider && data.insider.length > 0) {
            insiderContainer.innerHTML = createInsiderTable(data.insider);
        } else {
            insiderContainer.innerHTML = '<p class="text-secondary">No insider trading data available</p>';
        }
    } catch (error) {
        console.error('Error loading insider data:', error);
    }
}

async function loadStockRatings(ticker) {
    try {
        const response = await fetch(`${API_BASE_URL}/quote/${ticker}/ratings`);
        const data = await response.json();

        const ratingsContainer = document.getElementById('stock-ratings-table');

        if (data.ratings && data.ratings.length > 0) {
            ratingsContainer.innerHTML = createTable(data.ratings);
        } else {
            ratingsContainer.innerHTML = '<p class="text-secondary">No analyst ratings available</p>';
        }
    } catch (error) {
        console.error('Error loading ratings:', error);
    }
}

// ===== Screener Functions =====
async function runScreener() {
    const type = document.getElementById('screener-type').value;
    const index = document.getElementById('filter-index').value;
    const sector = document.getElementById('filter-sector').value;
    const marketCap = document.getElementById('filter-marketcap').value;

    const params = new URLSearchParams({ type });
    if (index) params.append('Index', index);
    if (sector) params.append('Sector', sector);
    if (marketCap) params.append('Market Cap', marketCap);

    document.getElementById('screener-loading').style.display = 'block';
    document.getElementById('screener-results').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/screener?${params}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to run screener');
        }

        displayScreenerResults(data);
        saveActivity('Ran screener', type);

    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        document.getElementById('screener-loading').style.display = 'none';
    }
}

function displayScreenerResults(data) {
    document.getElementById('screener-results').style.display = 'block';
    document.getElementById('screener-count').textContent = `Found ${data.count} stocks`;

    const table = document.getElementById('screener-table');

    if (data.stocks && data.stocks.length > 0) {
        table.innerHTML = createTable(data.stocks);
    } else {
        table.innerHTML = '<p class="text-secondary">No stocks found matching the criteria</p>';
    }
}

// ===== News Functions =====
async function loadNews() {
    document.getElementById('news-loading').style.display = 'block';
    document.getElementById('news-content').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/news`);
        const data = await response.json();

        const newsList = document.getElementById('news-list');
        if (data.news && data.news.length > 0) {
            newsList.innerHTML = data.news.map(item => `
                <div class="news-card" onclick="window.open('${item.link}', '_blank')">
                    <div class="news-title">${item.title}</div>
                    <div class="news-meta">
                        <span>${item.date || ''}</span>
                    </div>
                </div>
            `).join('');
        } else {
            newsList.innerHTML = '<p class="text-secondary">No news available</p>';
        }

        const blogsList = document.getElementById('blogs-list');
        if (data.blogs && data.blogs.length > 0) {
            blogsList.innerHTML = data.blogs.map(item => `
                <div class="news-card" onclick="window.open('${item.link}', '_blank')">
                    <div class="news-title">${item.title}</div>
                    <div class="news-meta">
                        <span>${item.date || ''}</span>
                    </div>
                </div>
            `).join('');
        } else {
            blogsList.innerHTML = '<p class="text-secondary">No blogs available</p>';
        }

        document.getElementById('news-content').style.display = 'block';

    } catch (error) {
        alert('Error loading news: ' + error.message);
    } finally {
        document.getElementById('news-loading').style.display = 'none';
    }
}

// ===== Insider Functions =====
async function loadInsider(option) {
    state.insiderOption = option;

    document.querySelectorAll('.insider-controls .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    document.getElementById('insider-loading').style.display = 'block';
    document.getElementById('insider-content').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/insider?option=${encodeURIComponent(option)}`);
        const data = await response.json();

        const table = document.getElementById('insider-table');

        if (data.insider && data.insider.length > 0) {
            table.innerHTML = createInsiderTable(data.insider);
        } else {
            table.innerHTML = '<p class="text-secondary">No insider trading data available</p>';
        }

        document.getElementById('insider-content').style.display = 'block';

    } catch (error) {
        alert('Error loading insider data: ' + error.message);
    } finally {
        document.getElementById('insider-loading').style.display = 'none';
    }
}

// ===== Tab Management =====
function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;

            // Only process if this is a stock quote tab
            if (!tab) return;

            // Remove active class from all tab buttons in the same group
            btn.parentElement.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Find the tab content container and hide all tab panes
            const tabContent = document.querySelector('.tab-content');
            if (tabContent) {
                tabContent.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('active');
                });
                // Show the selected tab pane
                const selectedPane = document.getElementById(`${tab}-tab`);
                if (selectedPane) {
                    selectedPane.classList.add('active');
                }
            }
        });
    });

    document.querySelectorAll('[data-news-tab]').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.newsTab;

            btn.parentElement.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (tab === 'news') {
                document.getElementById('news-list').style.display = 'grid';
                document.getElementById('blogs-list').style.display = 'none';
            } else {
                document.getElementById('news-list').style.display = 'none';
                document.getElementById('blogs-list').style.display = 'grid';
            }
        });
    });
}

// ===== Utility Functions =====
function createInsiderTable(data) {
    if (!data || data.length === 0) {
        return '<p class="text-secondary">No data available</p>';
    }

    // Define the order of columns we want to display
    const priorityColumns = ['Ticker', 'Transaction', 'Owner', 'Relationship', 'Date', 'Cost', '#Shares', 'Value ($)', '#Shares Total', 'SEC Form 4'];

    // Get all available columns from the first row
    const allColumns = Object.keys(data[0]);

    // Create final column list: priority columns first, then any remaining columns
    const headers = priorityColumns.filter(col => allColumns.includes(col));
    const remainingColumns = allColumns.filter(col => !priorityColumns.includes(col));
    const finalHeaders = [...headers, ...remainingColumns];

    let html = '<table class="data-table"><thead><tr>';
    finalHeaders.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        finalHeaders.forEach(header => {
            const value = row[header] || '';
            let cellContent = value;
            let className = '';

            // Special handling for Ticker - make it clickable
            if (header === 'Ticker' && value) {
                cellContent = `<span class="ticker-link" onclick="searchStockByTicker('${value}')" title="View ${value} details">${value}</span>`;
            }
            // Special handling for Transaction - add color badge
            else if (header === 'Transaction' && value) {
                const isBuy = value.toLowerCase().includes('buy') || value.toLowerCase().includes('purchase');
                const isSell = value.toLowerCase().includes('sell') || value.toLowerCase().includes('sale');

                if (isBuy) {
                    cellContent = `<span class="transaction-badge buy">${value}</span>`;
                } else if (isSell) {
                    cellContent = `<span class="transaction-badge sell">${value}</span>`;
                } else {
                    cellContent = `<span class="transaction-badge">${value}</span>`;
                }
            }
            // Numeric values with percentage
            else if (!isNaN(parseFloat(value)) && value.toString().includes('%')) {
                className = parseFloat(value) >= 0 ? 'positive' : 'negative';
            }

            html += `<td class="${className}">${cellContent}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function createTable(data) {
    if (!data || data.length === 0) {
        return '<p class="text-secondary">No data available</p>';
    }

    const headers = Object.keys(data[0]);

    let html = '<table class="data-table"><thead><tr>';
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        headers.forEach(header => {
            const value = row[header] || '';
            const isNumeric = !isNaN(parseFloat(value)) && value.toString().includes('%');
            const className = isNumeric && parseFloat(value) >= 0 ? 'positive' : isNumeric ? 'negative' : '';
            html += `<td class="${className}">${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function showError(message) {
    const errorElement = document.getElementById('stock-error');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    document.getElementById('stock-results').style.display = 'none';
}

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    // Setup navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            // Only intercept if it's an internal page link
            if (link.dataset.page) {
                e.preventDefault();
                const page = link.dataset.page;
                navigateTo(page);
            }
        });
    });

    // Setup tabs
    setupTabs();

    // Setup enter key for stock search
    const tickerInput = document.getElementById('ticker-input');
    if (tickerInput) {
        tickerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchStock();
            }
        });
    }

    // Setup enter key for watchlist modal
    const watchlistInput = document.getElementById('watchlist-ticker-input');
    if (watchlistInput) {
        watchlistInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                addToWatchlist();
            }
        });
    }

    // Setup enter key for compare inputs
    ['compare-ticker-1', 'compare-ticker-2', 'compare-ticker-3'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    compareStocks();
                }
            });
        }
    });

    // Close modal on outside click
    document.getElementById('add-watchlist-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'add-watchlist-modal') {
            closeAddToWatchlist();
        }
    });

    // Initialize dashboard
    updateWatchlistCount();
});

// Make functions globally available
window.navigateTo = navigateTo;
window.searchStock = searchStock;
window.searchStockByTicker = searchStockByTicker;
window.runScreener = runScreener;
window.loadInsider = loadInsider;
window.showAddToWatchlist = showAddToWatchlist;
window.closeAddToWatchlist = closeAddToWatchlist;
window.addToWatchlist = addToWatchlist;
window.removeFromWatchlist = removeFromWatchlist;
window.compareStocks = compareStocks;
