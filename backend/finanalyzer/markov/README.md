# Stock Market Prediction Using Markov Chains

An advanced probabilistic forecasting system that predicts stock prices using Markov chains, Hidden Markov Models (HMM), and Monte Carlo simulation.

## Features

### Core Capabilities
- **Multiple Markov Models**: First-order, second-order, and ensemble Markov chains
- **Hidden Markov Models**: Gaussian HMM for capturing latent market regimes
- **Advanced State Discretization**: 5 different methods including K-Means clustering
- **Monte Carlo Simulation**: Generate probabilistic predictions with confidence intervals
- **Comprehensive Backtesting**: Test model performance on historical data
- **Rich Visualizations**: Interactive charts for prices, predictions, and performance

### Technical Features
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages, ATR
- **Market Regime Detection**: Bull/Bear/Sideways market identification
- **Risk Analysis**: Value at Risk (VaR), Conditional VaR, maximum drawdown
- **Trading Recommendations**: Automated buy/sell/hold signals with confidence levels
- **Multi-day Forecasting**: Predict prices multiple days ahead with confidence bands

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode (Recommended for Beginners)

Simply run the program without arguments:
```bash
python main.py
```

The interactive mode will guide you through:
1. Selecting a stock ticker (e.g., AAPL, TSLA, MSFT)
2. Choosing historical data period
3. Configuring the number of states
4. Selecting discretization method
5. Choosing analysis type

### Command-Line Mode

#### Quick Analysis
Analyze a stock with default settings:
```bash
python main.py --ticker AAPL
```

#### Single-Day Prediction
Predict tomorrow's price:
```bash
python main.py --ticker TSLA --predict 1
```

#### Multi-Day Forecast
Generate a 5-day forecast:
```bash
python main.py --ticker MSFT --predict 5
```

#### Backtest Model Performance
Test accuracy on historical data:
```bash
python main.py --ticker GOOGL --backtest
```

#### Full Analysis
Run complete analysis with all features:
```bash
python main.py --ticker AAPL --full
```

#### Custom Configuration
```bash
python main.py --ticker NVDA --period 1y --states 5 --method kmeans --predict 3
```

### Command-Line Arguments

- `--ticker, -t`: Stock ticker symbol (e.g., AAPL, TSLA)
- `--period, -p`: Historical data period (1mo, 3mo, 6mo, 1y, 2y, 5y)
- `--states, -s`: Number of states (3, 5, or 7)
- `--method, -m`: Discretization method (returns, volatility, kmeans, hybrid)
- `--predict DAYS`: Generate N-day price forecast
- `--backtest`: Run backtest analysis
- `--full`: Run full analysis with all features
- `--no-viz`: Skip visualization generation

## State Discretization Methods

1. **Returns-based** (Recommended): Discretizes based on return percentiles
2. **Volatility-based**: Combines returns with volatility regimes
3. **K-Means**: Multi-feature clustering using returns, volatility, RSI, and volume
4. **Hybrid**: Advanced method combining multiple indicators

## Output

### Prediction Results
- Current and expected price
- Expected return percentage
- 95% and 68% confidence intervals
- Probability of price increase/decrease
- Risk metrics (VaR, CVaR)
- Trading recommendation (BUY/SELL/HOLD)

### Visualizations
1. **Historical Prices**: Price chart with moving averages and volume
2. **Technical Indicators**: Bollinger Bands, RSI, MACD
3. **Prediction Analysis**: Price and return distributions with confidence intervals
4. **State Analysis**: State frequencies, returns, and risk-return profiles
5. **Transition Matrix**: State transition probabilities heatmap
6. **Backtest Results**: Model performance and accuracy metrics

## How It Works

### 1. Data Collection
- Fetches historical stock data using yfinance API
- Calculates technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Identifies market regimes (bull/bear/sideways)

### 2. State Discretization
- Converts continuous price data into discrete states
- Uses various methods: return-based, volatility-based, K-Means clustering

### 3. Markov Model Training
- Builds first-order and second-order Markov chains
- Learns transition probabilities between states
- Creates ensemble model for robust predictions

### 4. Prediction Generation
- Uses current market state as input
- Runs Monte Carlo simulations (1000+ iterations)
- Samples future states from transition probabilities
- Generates probabilistic price forecasts

### 5. Risk Analysis
- Calculates Value at Risk (VaR) and Conditional VaR
- Estimates maximum potential loss
- Provides risk-adjusted recommendations

## Example Output

```
============================================================
STOCK PRICE PREDICTION SUMMARY
============================================================

Current Price: $180.50

Expected Price (Next Day): $181.23
Expected Return: 0.40%

95% Confidence Interval: $177.80 - $184.50
68% Confidence Interval: $179.20 - $183.10

Probability of Increase: 58.3%
Probability of Decrease: 41.7%

============================================================
RECOMMENDATION: BUY (Confidence: Medium)
============================================================

Probability of price increase: 58.3% | Expected return: 0.40%

============================================================
RISK METRICS
============================================================
Value at Risk (95%): $2.70 (-1.50%)
Conditional VaR: $4.10 (-2.27%)
Max Potential Loss: $8.50
```

## Performance Metrics

The backtesting system provides comprehensive metrics:
- **Direction Accuracy**: Percentage of correct up/down predictions
- **Mean Absolute Error (MAE)**: Average prediction error
- **Root Mean Squared Error (RMSE)**: Penalizes large errors
- **R-squared**: Correlation between predicted and actual prices
- **Trading Performance**: Win rate, profit factor, Sharpe ratio

## Limitations

⚠️ **Important Disclaimers:**
1. **Not Financial Advice**: This tool is for educational purposes only
2. **No Guarantees**: Past performance doesn't guarantee future results
3. **Market Complexity**: Stock markets are influenced by countless factors beyond historical patterns
4. **Use Responsibly**: Always do your own research and consult financial advisors

## Technical Architecture

```
markov_stock_predictor/
├── main.py                  # CLI interface
├── data_fetcher.py         # Data collection and preprocessing
├── state_discretizer.py    # State discretization methods
├── markov_models.py        # Markov chain implementations
├── predictor.py            # Prediction engine
├── backtester.py           # Backtesting framework
├── visualizer.py           # Visualization module
└── requirements.txt        # Dependencies
```

## Dependencies

- **yfinance**: Stock data fetching
- **numpy**: Numerical computations
- **pandas**: Data manipulation
- **matplotlib/seaborn**: Visualization
- **scipy**: Statistical functions
- **hmmlearn**: Hidden Markov Models
- **scikit-learn**: Machine learning utilities

## Advanced Features

### Ensemble Modeling
Combines predictions from multiple Markov models for improved accuracy.

### Monte Carlo Simulation
Generates thousands of possible future price paths to estimate probability distributions.

### Technical Indicators
Incorporates RSI, MACD, Bollinger Bands, and other indicators for enhanced state definition.

### Market Regime Detection
Automatically identifies bull, bear, and sideways market conditions.

## Troubleshooting

### Import Errors
```bash
pip install --upgrade -r requirements.txt
```

### Data Fetch Errors
- Check internet connection
- Verify ticker symbol is correct
- Try a different time period

### Visualization Issues
- Ensure matplotlib backend is properly configured
- On remote servers, use `--no-viz` flag

## Contributing

Contributions are welcome! Areas for improvement:
- Additional discretization methods
- More sophisticated models (LSTM, Transformer)
- Real-time data streaming
- Portfolio optimization
- Options pricing

## License

This project is provided as-is for educational purposes.

## Acknowledgments

- Built with advanced Markov chain theory
- Uses industry-standard technical indicators
- Inspired by quantitative finance research

---

**Remember**: This tool is for educational and research purposes only. Always conduct thorough research and consult with financial professionals before making investment decisions.
