# 🚀 Quick Start Guide - Stock Market Prediction

## ✅ System is Ready!

All dependencies are installed and the system has been tested successfully.

---

## 📋 Quick Command Reference

### 1️⃣ **Easiest Way - Interactive Mode**
```bash
python3 main.py
```
**Just press Enter to use defaults!** The wizard will guide you through everything.

---

### 2️⃣ **Quick Stock Analysis**
```bash
python3 main.py --ticker AAPL
```
**What you get:**
- Tomorrow's predicted price: $XXX.XX
- Confidence intervals (68% and 95%)
- Probability of increase/decrease
- BUY/SELL/HOLD recommendation
- Risk metrics (VaR, CVaR)
- Interactive charts

**Test confirmed working:** ✅
```
Current Price: $247.77
Expected Price: $247.73
Expected Return: -0.02%
Recommendation: HOLD
Probability of Increase: 52.6%
```

---

### 3️⃣ **Multi-Day Forecast**
```bash
python3 main.py --ticker TSLA --predict 5
```
Predicts next 5 days with confidence bands

---

### 4️⃣ **Different Stocks to Try**
```bash
python3 main.py --ticker TSLA    # Tesla
python3 main.py --ticker MSFT    # Microsoft
python3 main.py --ticker GOOGL   # Google
python3 main.py --ticker NVDA    # NVIDIA
python3 main.py --ticker AMZN    # Amazon
```

---

### 5️⃣ **Full Analysis with Backtesting**
```bash
python3 main.py --ticker MSFT --full
```
Includes historical validation of model accuracy

---

### 6️⃣ **Faster Analysis (No Charts)**
```bash
python3 main.py --ticker AAPL --no-viz
```
Get results without waiting for visualizations

---

## 🎯 Understanding the Output

### Main Prediction Results:
```
Current Price: $247.77
Expected Price (Next Day): $247.73
Expected Return: -0.02%

95% Confidence Interval: $238.12 - $256.83
68% Confidence Interval: $244.77 - $251.02

Probability of Increase: 52.6%
Probability of Decrease: 47.1%
```

### Recommendation:
- **STRONG BUY** = High confidence price will increase significantly
- **BUY** = Moderate confidence in price increase
- **HOLD** = Uncertain direction or small expected change
- **SELL** = Moderate confidence in price decrease
- **STRONG SELL** = High confidence price will decrease significantly

### Risk Metrics:
- **Value at Risk (95%)** = Maximum expected loss in 95% of scenarios
- **Conditional VaR** = Average loss in the worst 5% of scenarios
- **Max Potential Loss** = Worst-case scenario loss

---

## 📊 Available Options

```
--ticker, -t     Stock symbol (e.g., AAPL, TSLA)
--period, -p     Data period: 1mo, 3mo, 6mo, 1y, 2y, 5y
--states, -s     Number of states: 3, 5, or 7
--method, -m     Method: returns, volatility, kmeans, hybrid
--predict N      Forecast N days ahead
--backtest       Validate on historical data
--full           Complete analysis with everything
--no-viz         Skip visualizations (faster)
```

---

## 🔥 Recommended Workflows

### For Beginners:
```bash
# 1. Try Apple stock
python3 main.py --ticker AAPL

# 2. Compare with Tesla
python3 main.py --ticker TSLA

# 3. Try a 3-day forecast
python3 main.py --ticker MSFT --predict 3
```

### For Advanced Analysis:
```bash
# Full analysis with different methods
python3 main.py --ticker AAPL --method kmeans --full

# Long-term data
python3 main.py --ticker GOOGL --period 5y --backtest

# Compare different state configurations
python3 main.py --ticker NVDA --states 3
python3 main.py --ticker NVDA --states 7
```

---

## 💡 Pro Tips

1. **Use 2 years of data** (default) - best balance
2. **Start with 5 states** (default) - most accurate
3. **Try different methods** - each captures different patterns
4. **Run multiple times** - predictions use probability
5. **Compare with news** - use as ONE data point
6. **Never risk more than you can lose** - this is educational

---

## 📈 What Makes Good Predictions?

✅ **Good Signals:**
- Probability > 60% in one direction
- Low volatility (narrow confidence bands)
- Consistent with recent trends
- Validated by backtesting

⚠️ **Uncertain Signals:**
- Probability ~50% (coin flip)
- Very wide confidence bands
- High volatility
- Recent major news/events

---

## 🎨 Visualizations Explained

When not using `--no-viz`, you'll see:

1. **Historical Price Chart** - Past prices with moving averages
2. **Technical Indicators** - RSI, MACD, Bollinger Bands
3. **Prediction Distribution** - Probability of different outcomes
4. **State Analysis** - Market regime transitions
5. **Forecast Chart** - Multi-day predictions (if using --predict)
6. **Backtest Results** - Model accuracy (if using --backtest)

---

## 🐛 Troubleshooting

**Problem:** "No data found"
- Check ticker symbol (AAPL not APPLE)
- Try different period: `--period 1y`

**Problem:** Slow performance
- Use `--no-viz` flag
- Reduce period: `--period 6mo`
- Reduce states: `--states 3`

**Problem:** Charts don't show
- Normal on remote servers
- Use `--no-viz` for text-only output

---

## 📚 Documentation Files

- **TESTING_GUIDE.md** - Detailed testing instructions
- **README.md** - Complete system documentation
- **This file** - Quick reference

---

## ⚠️ Important Disclaimer

This is an **educational tool** to learn about Markov chains and probability.
- NOT financial advice
- Past performance ≠ future results
- Always do your own research
- Never invest more than you can afford to lose

---

## 🎓 Next Steps

1. ✅ **Test the system** (you are here!)
2. Try different stocks and compare results
3. Experiment with different parameters
4. Track predictions vs actual outcomes
5. Learn about the math behind it
6. Build your own improvements

---

## 🆘 Need More Help?

- Read `TESTING_GUIDE.md` for detailed examples
- Check `README.md` for technical details
- Experiment with different options
- Each prediction is probabilistic - run multiple times

---

**Ready to predict? Start with:**
```bash
python3 main.py --ticker AAPL
```

Happy trading! 🚀📈

*Remember: This tool helps you understand market patterns using mathematics. Use it wisely alongside other research methods.*
