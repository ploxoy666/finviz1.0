from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yfinance as yf
from finvizfinance.quote import finvizfinance
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.valuation import Valuation
from finvizfinance.screener.financial import Financial
from finvizfinance.screener.ownership import Ownership
from finvizfinance.screener.performance import Performance
from finvizfinance.screener.technical import Technical
from finvizfinance.news import News
from finvizfinance.insider import Insider
import traceback
import os

# Import financial analyzer blueprint
try:
    from financial_analyzer_api import analyzer_bp
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    print("Warning: Financial analyzer not available")

# Get the directory paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(backend_dir)
frontend_dir = os.path.join(project_dir, 'frontend')

app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
CORS(app)

# Register financial analyzer blueprint
if ANALYZER_AVAILABLE:
    app.register_blueprint(analyzer_bp)
    print("✓ Financial Analyzer API registered")

@app.route('/')
def home():
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/api')
def api_info():
    return jsonify({
        'message': 'Finvizfinance API',
        'version': '1.0.0',
        'endpoints': {
            'quote': '/api/quote/<ticker>',
            'chart': '/api/quote/<ticker>/chart',
            'news': '/api/quote/<ticker>/news',
            'insider': '/api/quote/<ticker>/insider',
            'screener': '/api/screener',
            'general_news': '/api/news',
            'general_insider': '/api/insider'
        }
    })


@app.route('/api/financials/<ticker>')
def get_financials(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        # Get financials (Income Statement)
        financials = stock.financials
        if financials.empty:
            financials = stock.quarterly_financials
            
        if financials.empty:
             return jsonify({'error': 'No financial data found'}), 404

        # Get Balance Sheet
        balance_sheet = stock.balance_sheet
        if balance_sheet.empty:
            balance_sheet = stock.quarterly_balance_sheet
        
        # Get Cash Flow
        cashflow = stock.cashflow
        if cashflow.empty:
            cashflow = stock.quarterly_cashflow
        
        # Helper to convert DF to simpler dict for frontend
        def clean_df(df):
            if df.empty: return {}
            # Take last 5 columns (years/quarters)
            df = df.iloc[:, :5]
            # Convert timestamp columns to string
            df.columns = [col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col) for col in df.columns]
            # Reset index to make the metrics (rows) keys in JSON
            # But to_dict() does that by default if we use 'index'? 
            # Actually to_dict() default is fine: {col: {index: val}}
            # Let's pivot slightly for easier frontend use: {metric: {date: val}}
            return df.fillna(0).to_dict('index')

        return jsonify({
            'income_statement': clean_df(financials),
            'balance_sheet': clean_df(balance_sheet),
            'cash_flow': clean_df(cashflow),
            'currency': stock.info.get('currency', 'USD')
        })
    except Exception as e:
        print(f"Error fetching financials for {ticker}: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/company_profile/<ticker>')
def get_company_profile(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Simplify officers list
        officers = []
        for off in info.get('companyOfficers', []):
            officers.append({
                'name': off.get('name'),
                'title': off.get('title'),
                'pay': off.get('totalPay', 'N/A'),
                'yearBorn': off.get('yearBorn', '')
            })
            
        return jsonify({
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'website': info.get('website', ''),
            'city': info.get('city', ''),
            'state': info.get('state', ''),
            'country': info.get('country', ''),
            'address': info.get('address1', ''),
            'fullTimeEmployees': info.get('fullTimeEmployees', 'N/A'),
            'longBusinessSummary': info.get('longBusinessSummary', 'No description available.'),
            'management': officers[:5], # Top 5
            'marketCap': info.get('marketCap'),
            'beta': info.get('beta'),
            'floatShares': info.get('floatShares'),
            'sharesOutstanding': info.get('sharesOutstanding'),
            'heldPercentInsiders': info.get('heldPercentInsiders'),
            'heldPercentInstitutions': info.get('heldPercentInstitutions')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/segments/<ticker>')
def get_segments(ticker):
    # Mock data for demonstration as real segment data requires paid APIs usually
    # specific mocks for popular tickers
    import random
    
    ticker = ticker.upper()
    years = ['2020', '2021', '2022', '2023', '2024']
    
    if ticker == 'AAPL':
        # Business Line
        business = {
            'iPhone': [137, 191, 205, 200, 201],
            'Mac': [28, 35, 40, 29, 30],
            'iPad': [23, 31, 29, 28, 26],
            'Wearables': [30, 38, 41, 39, 37],
            'Services': [53, 68, 78, 85, 96]
        }
        # Geography
        geo = {
            'Americas': [112, 133, 169, 162, 165],
            'Europe': [58, 89, 95, 94, 98],
            'China': [40, 68, 74, 72, 66],
            'Japan': [21, 28, 25, 24, 23],
            'Asia Pacific': [19, 26, 29, 29, 30]
        }
    elif ticker == 'MSFT':
         business = {
            'Productivity': [46, 53, 63, 69, 75],
            'Cloud': [48, 60, 75, 87, 105],
            'Computing': [48, 54, 59, 54, 58]
        }
         geo = {
            'US': [70, 85, 100, 106, 120],
            'International': [72, 83, 98, 105, 125]
        }
    else:
        # Generic Random Data
        business = {
            'Product A': [random.randint(10,50) for _ in years],
            'Product B': [random.randint(10,50) for _ in years],
            'Services': [random.randint(10,50) for _ in years]
        }
        geo = {
            'North America': [random.randint(20,60) for _ in years],
            'International': [random.randint(20,60) for _ in years]
        }
        
    return jsonify({
        'years': years,
        'business': business,
        'geography': geo
    })

@app.route('/api/valuation/<ticker>')
def get_valuation(ticker):
    # Calculate mock historical valuations based on price history
    # Real calc requires complex matching of daily price to quarterly financials
    # We will simulate the "look" of the chart with reasonable ranges based on current P/E
    try:
        stock = yf.Ticker(ticker)
        # fast_info = stock.fast_info
        current_pe = stock.info.get('trailingPE', 25)
        if current_pe is None: current_pe = 25
        
        dates = []
        pe_ratio = []
        ps_ratio = [] 
        pb_ratio = []
        
        # Base trends
        import datetime
        import math
        base_date = datetime.datetime.today() - datetime.timedelta(days=365*5) # 5 years
        
        for i in range(20): # 4 points per year approx
             dates.append((base_date + datetime.timedelta(days=i*90)).strftime('%Y'))
        
        # Actually lets provide quarterly points
        current_year = 2020
        for i in range(20):
            year = current_year + (i // 4)
            q = (i % 4) + 1
            dates.append(f"FY {year} Q{q}")
             # Add some volatility
            noise = math.sin(i/3.0) * (current_pe * 0.4)
            p_e = abs(current_pe + noise)
            if p_e > 200: p_e = 200 # cap
            pe_ratio.append(p_e)
            ps_ratio.append(p_e / 6) 
            pb_ratio.append(p_e / 4)

        return jsonify({
            'dates': dates,
            'pe': pe_ratio,
            'ps': ps_ratio,
            'pb': pb_ratio
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/history/<ticker>')
def get_history(ticker):
    try:
        # Get 1 year of data
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y", interval="1d", auto_adjust=True)
        
        if df.empty:
            return jsonify({'error': 'No data found'}), 404
            
        df.reset_index(inplace=True)
        
        # Format for Chart.js
        data = {
            'ticker': ticker.upper(),
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'prices': df['Close'].tolist(),
            'open': df['Open'].tolist(),
            'high': df['High'].tolist(),
            'low': df['Low'].tolist(),
            'volumes': df['Volume'].tolist()
        }
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching history for {ticker}: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/quote/<ticker>')
def get_quote(ticker):
    try:
        stock = finvizfinance(ticker.upper())
        
        # Get fundamental data
        fundament = stock.ticker_fundament()
        
        # Get description
        description = stock.ticker_description()
        
        # Get peers
        try:
            peers = stock.ticker_peer()
        except:
            peers = []
        
        # Get ETF holders
        try:
            etf_holders = stock.ticker_etf_holders()
        except:
            etf_holders = []
        
        return jsonify({
            'ticker': ticker.upper(),
            'fundament': fundament,
            'description': description,
            'peers': peers,
            'etf_holders': etf_holders
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 400

@app.route('/api/quote/<ticker>/chart')
def get_chart(ticker):
    try:
        stock = finvizfinance(ticker.upper())
        chart_url = stock.ticker_charts()
        return jsonify({
            'ticker': ticker.upper(),
            'chart_url': chart_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/quote/<ticker>/news')
def get_stock_news(ticker):
    try:
        stock = finvizfinance(ticker.upper())
        news_df = stock.ticker_news()
        news_list = news_df.fillna('').to_dict('records') if not news_df.empty else []
        return jsonify({
            'ticker': ticker.upper(),
            'news': news_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/quote/<ticker>/insider')
def get_stock_insider(ticker):
    try:
        stock = finvizfinance(ticker.upper())
        insider_df = stock.ticker_inside_trader()
        insider_list = insider_df.fillna('').to_dict('records') if not insider_df.empty else []
        return jsonify({
            'ticker': ticker.upper(),
            'insider': insider_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/quote/<ticker>/ratings')
def get_stock_ratings(ticker):
    try:
        stock = finvizfinance(ticker.upper())
        ratings_df = stock.ticker_outer_ratings()
        ratings_list = ratings_df.fillna('').to_dict('records') if not ratings_df.empty else []
        return jsonify({
            'ticker': ticker.upper(),
            'ratings': ratings_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/screener')
def screener():
    try:
        screener_type = request.args.get('type', 'overview')
        filters = {}
        
        # Parse filters from query params
        for key, value in request.args.items():
            if key != 'type':
                filters[key] = value
        
        # Select screener type
        screener_map = {
            'overview': Overview,
            'valuation': Valuation,
            'financial': Financial,
            'ownership': Ownership,
            'performance': Performance,
            'technical': Technical
        }
        
        ScreenerClass = screener_map.get(screener_type, Overview)
        screener_obj = ScreenerClass()
        
        if filters:
            screener_obj.set_filter(filters_dict=filters)
        
        df = screener_obj.screener_view()
        stocks = df.fillna('').to_dict('records') if not df.empty else []
        
        return jsonify({
            'type': screener_type,
            'filters': filters,
            'count': len(stocks),
            'stocks': stocks
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 400

@app.route('/api/news')
def get_news():
    try:
        fnews = News()
        all_news = fnews.get_news()
        
        news_list = all_news['news'].fillna('').to_dict('records') if 'news' in all_news and not all_news['news'].empty else []
        blogs_list = all_news['blogs'].fillna('').to_dict('records') if 'blogs' in all_news and not all_news['blogs'].empty else []
        
        return jsonify({
            'news': news_list,
            'blogs': blogs_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/insider')
def get_insider():
    try:
        option = request.args.get('option', 'latest')
        finsider = Insider(option=option)
        insider_df = finsider.get_insider()
        # Replace NaN values with None to avoid JSON serialization errors
        insider_list = insider_df.fillna('').to_dict('records') if not insider_df.empty else []
        
        return jsonify({
            'option': option,
            'insider': insider_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/screener/filters')
def get_screener_filters():
    """Return available screener filters"""
    return jsonify({
        'screener_types': ['overview', 'valuation', 'financial', 'ownership', 'performance', 'technical'],
        'common_filters': {
            'Index': ['S&P 500', 'NASDAQ 100', 'Dow Jones', 'Russell 2000'],
            'Sector': ['Basic Materials', 'Communication Services', 'Consumer Cyclical', 
                      'Consumer Defensive', 'Energy', 'Financial', 'Healthcare', 
                      'Industrials', 'Real Estate', 'Technology', 'Utilities'],
            'Market Cap': ['+Large (over $10bln)', '+Mid (over $2bln)', '+Small (over $300mln)', 
                          '+Micro (over $50mln)', '+Nano (under $50mln)'],
            'P/E': ['Low (<15)', 'Profitable (>0)', 'High (>50)', 'Under 5', 'Under 10', 
                   'Under 15', 'Under 20', 'Under 25', 'Under 30', 'Under 35', 'Under 40', 
                   'Under 45', 'Under 50', 'Over 5', 'Over 10', 'Over 15', 'Over 20', 
                   'Over 25', 'Over 30', 'Over 35', 'Over 40', 'Over 45', 'Over 50']
        }
    })

# Catch-all route for serving static files (must be last)
@app.route('/<path:path>')
def serve_static(path):
    # Serve static files (CSS, JS, images, etc.)
    if os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    # If file doesn't exist, return index.html for client-side routing
    return send_from_directory(frontend_dir, 'index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
