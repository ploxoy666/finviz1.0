# 📈 FinvizPro - Advanced Stock Analysis Platform

![FinvizPro](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Modern financial analysis platform powered by Finviz - Real-time stock quotes, advanced screening, news, and insider trading insights.

## ✨ Features

- 📊 **Real-time Stock Quotes** - Comprehensive fundamentals, technical indicators, and peer comparison
- 🔍 **Advanced Stock Screener** - Filter thousands of stocks by valuation, performance, and technical metrics
- 📰 **Market News** - Latest financial news and analysis from trusted sources
- 👔 **Insider Trading** - Track insider transactions and institutional ownership changes
- ⭐ **Watchlist** - Create and manage your personal stock watchlist
- 📈 **Stock Comparison** - Compare multiple stocks side-by-side
- 🎨 **Modern UI** - Beautiful dark theme with glassmorphism design

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/finvizpro.git
   cd finvizpro
   ```

2. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Run the backend**
   ```bash
   python app.py
   ```
   Backend will run on `http://localhost:5000`

4. **Run the frontend** (in a new terminal)
   ```bash
   cd frontend
   python -m http.server 8000
   ```
   Frontend will run on `http://localhost:8000`

5. **Open your browser**
   Navigate to `http://localhost:8000`

## 📁 Project Structure

```
finvizpro/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   └── render.yaml         # Render.com deployment config
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── app.js              # JavaScript application logic
│   └── style.css           # Styles and design
├── DEPLOYMENT.md           # Deployment guide
└── README.md               # This file
```

## 🛠️ Tech Stack

### Backend
- **Flask** - Web framework
- **finvizfinance** - Finviz data scraper
- **Flask-CORS** - Cross-origin resource sharing
- **Gunicorn** - WSGI HTTP server
- **Pandas** - Data manipulation

### Frontend
- **Vanilla JavaScript** - No frameworks, pure JS
- **HTML5 & CSS3** - Modern web standards
- **Chart.js** - Data visualization
- **Glassmorphism** - Modern UI design

## 📊 API Endpoints

### Stock Quotes
- `GET /api/quote/<ticker>` - Get stock fundamentals
- `GET /api/quote/<ticker>/chart` - Get chart URL
- `GET /api/quote/<ticker>/news` - Get stock news
- `GET /api/quote/<ticker>/insider` - Get insider trading data
- `GET /api/quote/<ticker>/ratings` - Get analyst ratings

### Screener
- `GET /api/screener?type=<type>&filters` - Screen stocks with filters

### News & Insider
- `GET /api/news` - Get general market news
- `GET /api/insider?option=<option>` - Get insider trading data

## 🌐 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy to Render.com

1. Push code to GitHub
2. Connect GitHub repo to Render
3. Deploy automatically

Free tier available!

## 🎨 Screenshots

### Home Page
Modern landing page with animated cards

### Stock Quote
Comprehensive stock analysis with tabs

### Watchlist
Color-coded watchlist with real-time data

### Insider Trading
Track insider transactions with Buy/Sell indicators

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This application is for educational and informational purposes only. It is not financial advice. Always do your own research before making investment decisions.

## 🙏 Acknowledgments

- [finvizfinance](https://github.com/lit26/finvizfinance) - Python library for Finviz data
- [Finviz](https://finviz.com) - Financial visualizations and data
- [Chart.js](https://www.chartjs.org/) - Data visualization library

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ by [Your Name]
