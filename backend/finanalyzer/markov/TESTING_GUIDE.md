# Stock Market Prediction - Step-by-Step Testing Guide

## Prerequisites Check ✓
- Python 3.13.1 installed ✓
- Dependencies installed ✓

---

## 🚀 Quick Start - 5 Steps to Your First Prediction

### Step 1: Test the Help Command
```bash
python3 main.py --help
```
**What this does:** Shows all available options and examples

---

### Step 2: Run a Quick Analysis (Easiest Way)
```bash
python3 main.py --ticker AAPL
```
**What this does:** 
- Fetches 2 years of Apple stock data
- Builds Markov models
- Predicts tomorrow's price
- Shows visualizations automatically

**Expected output:**
- Data summary statistics
- Model training progress
- Price prediction with confidence intervals
- Trading recommendation (BUY/SELL/HOLD)
- Multiple interactive charts

---

### Step 3: Try Interactive Mode (Most User-Friendly)
```bash
python3 main.py
```
**What this does:** Starts a guided wizard that asks you:
1. Which stock? (e.g., AAPL, TSLA, MSFT, GOOGL)
2. How much historical data? (default: 2 years)
3. How many states? (default: 5 - recommended)
4. Which method? (default: returns-based)
5. What analysis? (default: full analysis)
6. Show visualizations? (default: yes)

**Recommendation:** Just press Enter to use defaults!

---

### Step 4: Multi-Day Forecast
```bash
python3 main.py --ticker TSLA --predict 5
```
**What this does:**
- Predicts next 5 days for Tesla
- Shows confidence bands for each day
- Generates forecast chart with multiple scenarios

---

### Step 5: Full Analysis with Backtesting
```bash
python3 main.py --ticker MSFT --full
```
**What this does:**
- Complete prediction analysis
- Historical backtesting to validate accuracy
- Performance metrics
- All visualizations

---

## 🎯 Detailed Testing Scenarios

### Test 1: Single Stock Analysis
```bash
python3 main.py --ticker AAPL
```
**Expected Results:**
```
============================================================
FETCHING DATA FOR AAPL
============================================================
Successfully fetched XXX data points for AAPL

============================================================
DATA SUMMARY
============================================================
Current Price:        $XXX.XX
Period Return:        X.XX%
Avg Daily Return:     X.XX%
Volatility:           X.XX%
...

============================================================
STOCK PRICE PREDICTION SUMMARY
============================================================
Current Price: $XXX.XX
Expected Price (Next Day): $XXX.XX
Expected Return: X.XX%
...
RECOMMENDATION: BUY/SELL/HOLD (Confidence: Medium/High)
```

---

### Test 2: Different Discretization Methods
```bash
# Returns-based (default, recommended)
python3 main.py --ticker AAPL --method returns

# Volatility-based (captures market regime changes)
python3 main.py --ticker AAPL --method volatility

# K-Means clustering (most sophisticated)
python3 main.py --ticker AAPL --method kmeans

# Hybrid approach
python3 main.py --ticker AAPL --method hybrid
```

---

### Test 3: Different Time Periods
```bash
# 1 month of data
python3 main.py --ticker AAPL --period 1mo

# 6 months
python3 main.py --ticker AAPL --period 6mo

# 1 year
python3 main.py --ticker AAPL --period 1y

# 5 years (more data = potentially better model)
python3 main.py --ticker AAPL --period 5y
```

---

### Test 4: Different Number of States
```bash
# 3 states (Simple: Down, Neutral, Up)
python3 main.py --ticker AAPL --states 3

# 5 states (Detailed - recommended)
python3 main.py --ticker AAPL --states 5

# 7 states (Very detailed)
python3 main.py --ticker AAPL --states 7
```

---

### Test 5: Backtesting Only
```bash
python3 main.py --ticker GOOGL --backtest
```
**What this shows:**
- Model accuracy on historical data
- Direction prediction accuracy
- Mean Absolute Error
- RMSE and other metrics
- Trading performance simulation

---

### Test 6: Skip Visualizations (Faster)
```bash
python3 main.py --ticker AAPL --no-viz
```
**Use case:** When you only want the numerical results

---

## 📊 Understanding the Output

### 1. Data Summary
Shows statistics about the fetched stock data:
- Current price
- Historical return over the period
- Average daily return
- Volatility (risk measure)
- Price range

### 2. Model Training
You'll see messages like:
```
Discretizing data using 'returns' method with 5 states...
Training First-Order Markov Chain...
✓ First-order model trained
✓ Second-order model trained
✓ Ensemble model created
```

### 3. Prediction Results
```
Current Price: $XXX.XX
Expected Price (Next Day): $XXX.XX
Expected Return: X.XX%

95% Confidence Interval: $XXX.XX - $XXX.XX
Probability of Increase: XX.X%
Probability of Decrease: XX.X%
```

### 4. Trading Recommendation
```
RECOMMENDATION: BUY/SELL/HOLD
Confidence: High/Medium

Reasoning: 
Probability of price increase: XX.X% | Expected return: X.XX%
```

### 5. Risk Metrics
```
Value at Risk (95%): $X.XX (-X.XX%)
Conditional VaR: $X.XX (-X.XX%)
Max Potential Loss: $X.XX
```

---

## 🎨 Visualizations Explained

When you run the analysis, you'll see 4-6 charts:

### Chart 1: Historical Prices
- Shows past price movements
- Moving averages (SMA 20, SMA 50)
- Trading volume

### Chart 2: Technical Indicators
- Bollinger Bands
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)

### Chart 3: Prediction Analysis (Single Day)
- **Top Left:** Predicted price distribution
- **Top Right:** Return distribution
- **Bottom Left:** State probabilities
- **Bottom Right:** Summary statistics

### Chart 4: Multi-Day Forecast (if using --predict N)
- Multiple possible price paths (gray lines)
- Expected price trajectory (green line)
- Confidence bands (68% and 95%)

### Chart 5: State Analysis
- State frequencies
- Average returns by state
- Risk-return profiles

### Chart 6: Backtest Results (if using --backtest or --full)
- Predicted vs actual prices
- Prediction errors over time
- Cumulative accuracy

---

## 🧪 Recommended Test Sequence

### For Beginners:
```bash
# Step 1: Start simple
python3 main.py --ticker AAPL

# Step 2: Try interactive mode
python3 main.py

# Step 3: Test a multi-day forecast
python3 main.py --ticker TSLA --predict 3
```

### For Advanced Users:
```bash
# Test different methods
python3 main.py --ticker AAPL --method kmeans --full

# Long-term data with backtest
python3 main.py --ticker MSFT --period 5y --backtest

# Compare different state configurations
python3 main.py --ticker GOOGL --states 3
python3 main.py --ticker GOOGL --states 7
```

---

## 🔍 Troubleshooting

### Problem: "No data found for ticker"
**Solution:** Check that the ticker symbol is correct (e.g., AAPL not APPLE)

### Problem: Charts not displaying
**Solution:** 
- Make sure you're not using `--no-viz` flag
- On remote servers, charts may not display - use `--no-viz` instead

### Problem: Slow performance
**Solution:** 
- Use shorter time periods: `--period 6mo`
- Reduce states: `--states 3`
- Skip visualizations: `--no-viz`

### Problem: Import errors
**Solution:**
```bash
# Reinstall dependencies
pip3 install -r requirements.txt
```

---

## 📈 Example Test Run

Here's what a typical test looks like:

```bash
python3 main.py --ticker AAPL
```

**Output:**
```
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     STOCK MARKET PREDICTION USING MARKOV CHAINS              ║
    ║     Advanced Probabilistic Forecasting System                ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝

============================================================
FETCHING DATA FOR AAPL
============================================================
Successfully fetched 503 data points for AAPL

============================================================
DATA SUMMARY
============================================================
Current Price:        $150.25
Period Return:        23.45%
Avg Daily Return:     0.09%
Volatility:           1.85%
Price Range:          $120.30 - $180.50
Data Points:          450

============================================================
BUILDING MARKOV MODELS
============================================================
Discretizing data using 'returns' method with 5 states...

State Discretization Method: returns
Number of States: 5

State Labels:
  State 0: Strong Down
  State 1: Down
  State 2: Neutral
  State 3: Up
  State 4: Strong Up

Training First-Order Markov Chain...
✓ First-order model trained
Training Second-Order Markov Chain...
✓ Second-order model trained
✓ Ensemble model created

============================================================
GENERATING PREDICTIONS FOR AAPL
============================================================
Current Price: $150.25
Current State: Up

Running Monte Carlo simulation (1000 simulations)...

============================================================
STOCK PRICE PREDICTION SUMMARY
============================================================

Current Price: $150.25

Expected Price (Next Day): $151.03
Expected Return: 0.52%

95% Confidence Interval: $147.50 - $154.80
68% Confidence Interval: $149.20 - $152.90

Probability of Increase: 58.7%
Probability of Decrease: 41.3%

============================================================
RECOMMENDATION: BUY (Confidence: Medium)
============================================================

Probability of price increase: 58.7% | Expected return: 0.52%

============================================================
RISK METRICS
============================================================
Value at Risk (95%): $2.75 (-1.83%)
Conditional VaR: $4.10 (-2.73%)
Max Potential Loss: $8.50

============================================================
GENERATING VISUALIZATIONS
============================================================
[Charts appear]
```

---

## 🎓 Tips for Best Results

1. **Use 2 years of data** - Good balance between relevance and statistical power
2. **Start with 5 states** - Most effective for stock prediction
3. **Try returns-based method first** - Most reliable for beginners
4. **Run full analysis** - Get complete picture with backtesting
5. **Test multiple stocks** - Each stock has different behavior patterns
6. **Compare predictions** - Run same stock multiple times to see consistency

---

## 📚 Next Steps

After testing:
1. Try different stocks (tech, finance, energy sectors)
2. Compare prediction accuracy across different methods
3. Analyze backtest results to understand model performance
4. Use predictions as ONE input in your trading decisions
5. Track predictions vs actual outcomes over time

---

## ⚠️ Important Disclaimers

- This is an **educational tool** for learning about Markov chains
- **NOT financial advice** - always do your own research
- Past performance doesn't guarantee future results
- Use predictions as ONE of many factors in decision-making
- Never invest more than you can afford to lose

---

## 🆘 Need Help?

If something doesn't work:
1. Check this guide's troubleshooting section
2. Review the README.md file
3. Verify all dependencies are installed
4. Try with a different stock ticker
5. Use simpler options (fewer states, shorter period)

Happy testing! 🚀📈
