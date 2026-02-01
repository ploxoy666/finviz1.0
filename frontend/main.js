// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State Management
const state = {
    currentPage: 'home',
    currentStock: null,
    insiderOption: 'latest'
};

// ===== Navigation =====
function navigateTo(page) {
    // Update state
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
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Setup navigation listeners
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            navigateTo(page);
        });
    });

    // Setup tab listeners
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
});

// ===== Tab Management =====
function setupTabs() {
    // Stock quote tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;

            // Update buttons
            btn.parentElement.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update content
            btn.closest('.tab-content').parentElement.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            document.getElementById(`${tab}-tab`).classList.add('active');
        });
    });

    // News tabs
    document.querySelectorAll('[data-news-tab]').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.newsTab;

            // Update buttons
            btn.parentElement.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Show/hide content
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
        // Fetch stock data
        const response = await fetch(`${API_BASE_URL}/quote/${ticker}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch stock data');
        }

        // Display stock data
        displayStockData(data);

        // Load additional data
        loadStockNews(ticker);
        loadStockInsider(ticker);
        loadStockRatings(ticker);

    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById('stock-loading').style.display = 'none';
    }
}

function displayStockData(data) {
    const { ticker, fundament, description, peers, etf_holders } = data;

    // Show results
    document.getElementById('stock-results').style.display = 'block';

    // Update header
    document.getElementById('stock-ticker').textContent = ticker;
    document.getElementById('stock-company').textContent = fundament.Company || ticker;

    // Update price section
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

    // Update description
    document.getElementById('stock-description').textContent = description || 'No description available';

    // Update key metrics
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

    // Update peers
    const peersContainer = document.getElementById('stock-peers');
    if (peers && peers.length > 0) {
        peersContainer.innerHTML = peers.map(peer =>
            `<span class="peer-badge" onclick="searchStockByTicker('${peer}')">${peer}</span>`
        ).join('');
    } else {
        peersContainer.innerHTML = '<p class="text-secondary">No peer data available</p>';
    }

    // Update ETF holders
    const etfContainer = document.getElementById('stock-etf');
    if (etf_holders && etf_holders.length > 0) {
        etfContainer.innerHTML = etf_holders.map(etf =>
            `<span class="peer-badge">${etf}</span>`
        ).join('');
    } else {
        etfContainer.innerHTML = '<p class="text-secondary">No ETF holder data available</p>';
    }

    // Update fundamentals tab
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
    searchStock();
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
            insiderContainer.innerHTML = createTable(data.insider);
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

    // Build query params
    const params = new URLSearchParams({ type });
    if (index) params.append('Index', index);
    if (sector) params.append('Sector', sector);
    if (marketCap) params.append('Market Cap', marketCap);

    // Show loading
    document.getElementById('screener-loading').style.display = 'block';
    document.getElementById('screener-results').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/screener?${params}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to run screener');
        }

        displayScreenerResults(data);

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

        // Display news
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

        // Display blogs
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

    // Update active button
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
            table.innerHTML = createTable(data.insider);
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

// ===== Utility Functions =====
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

// Make functions globally available
window.navigateTo = navigateTo;
window.searchStock = searchStock;
window.searchStockByTicker = searchStockByTicker;
window.runScreener = runScreener;
window.loadInsider = loadInsider;
