# 📱 Stock Predictor macOS App - User Guide

## 🎉 Your App is Ready!

You now have a native macOS application called **"Stock Predictor.app"** that you can use just like any other Mac app!

---

## 🚀 How to Use the App

### Method 1: Double-Click (Easiest)
1. Find **"Stock Predictor.app"** in your current folder
2. **Double-click** the app icon
3. Terminal will open automatically with the wizard
4. Follow the step-by-step wizard!

### Method 2: Move to Applications (Recommended)
1. Drag **"Stock Predictor.app"** to your **Applications** folder
2. Open Launchpad or Applications folder
3. Click **"Stock Predictor"**
4. The app runs!

### Method 3: Add to Dock
1. Open the app once (double-click)
2. Right-click the app icon in Dock
3. Select **Options → Keep in Dock**
4. Now you can launch it from Dock anytime!

---

## 📋 First Time Setup

### What Happens on First Launch:
1. **Terminal opens automatically**
2. **Python environment is set up** (happens only once, ~2 minutes)
3. **All dependencies are installed automatically**
4. **The wizard starts!**

**Note:** First launch takes 2-3 minutes. After that, it starts instantly!

---

## 🎯 Using the Wizard

When you open the app, you'll see a beautiful step-by-step wizard:

### Step 1: Choose Your Stock
```
📊 Enter a stock ticker symbol
   Popular choices: AAPL, TSLA, MSFT, GOOGL, NVDA, AMZN

➤ Your choice: AAPL
```
**Just type the ticker and press Enter!**

### Step 2: Select Time Period
```
⏰ How much historical data should we analyze?

   [1] 1 month    - Very recent trends only
   [2] 3 months   - Short term analysis
   [3] 6 months   - Medium term view
   [4] 1 year     - Annual perspective
   [5] 2 years    - Recommended ⭐ (best balance)
   [6] 5 years    - Long term patterns

➤ Your choice [5]: 
```
**Press Enter for recommended option, or type a number (1-6)**

### Step 3-7: Similar Easy Choices
- Number of states (press Enter for default)
- Prediction method (press Enter for default)
- Forecast horizon (1, 3, 5, or 10 days)
- Run backtest? (Y/N)
- Show charts? (Y/N)

### Summary & Confirmation
```
📋 YOUR CHOICES SUMMARY
═══════════════════════════════════════
Stock:          AAPL
Time Period:    2 years
States:         5
Method:         Returns-based
Forecast:       Tomorrow only
Backtest:       Yes
Visualizations: Yes

🚀 Press Enter to start the analysis...
```

---

## 📊 What You'll Get

### Results Include:
1. ✅ **Tomorrow's predicted price**
2. ✅ **Confidence intervals** (68% and 95%)
3. ✅ **Probability of increase/decrease**
4. ✅ **BUY/SELL/HOLD recommendation**
5. ✅ **Risk metrics** (VaR, CVaR)
6. ✅ **Interactive charts** (if enabled)
7. ✅ **Backtest results** (if enabled)

### Example Output:
```
════════════════════════════════════════════════════
STOCK PRICE PREDICTION SUMMARY
════════════════════════════════════════════════════

Current Price: $247.77

Expected Price (Next Day): $248.50
Expected Return: 0.29%

95% Confidence Interval: $238.12 - $258.83
Probability of Increase: 58.3%

════════════════════════════════════════════════════
RECOMMENDATION: BUY (Confidence: Medium)
════════════════════════════════════════════════════
```

---

## 💡 Tips & Tricks

### Beginner Tips:
1. **Use defaults** - Just press Enter for all questions
2. **Start with Apple (AAPL)** - Good for learning
3. **Enable visualizations** - Very helpful to see patterns
4. **Run backtest** - Shows model accuracy

### Advanced Tips:
1. **Try different methods** - Compare returns vs volatility
2. **Test different time periods** - See how it affects predictions
3. **Multi-day forecasts** - Choose 5 or 10 days
4. **Run multiple times** - Predictions are probabilistic

### Speed Tips:
- **Disable charts** for faster results
- **Skip backtest** if you're in a hurry
- **Use 1 month** data for quick tests

---

## 🔧 Troubleshooting

### Problem: App won't open
**Solution:**
1. Right-click the app
2. Select "Open"
3. Click "Open" in the security dialog
4. macOS will remember your choice

### Problem: "Cannot be opened" message
**Solution:**
```bash
# In Terminal, run:
xattr -cr "Stock Predictor.app"
```

### Problem: First launch is slow
**Answer:** This is normal! First launch installs Python packages (~2 min). Subsequent launches are instant.

### Problem: Terminal closes immediately
**Solution:** 
- The script includes "Press any key to close"
- If it closes too fast, there might be an error
- Check Terminal history or run from command line to see errors

### Problem: "No data found for ticker"
**Solution:** 
- Check ticker symbol spelling (AAPL not APPLE)
- Verify it's a US stock ticker
- Try a different stock

---

## 📁 App Structure

```
Stock Predictor.app/
├── Contents/
│   ├── Info.plist              # App metadata
│   ├── MacOS/
│   │   └── StockPredictor      # Main launcher
│   └── Resources/
│       ├── *.py                # Python scripts
│       ├── requirements.txt    # Dependencies
│       ├── launch_app.sh       # Setup script
│       └── venv/               # Python environment (created on first run)
```

---

## 🎨 Customization

### Change Default Settings
Edit `Stock Predictor.app/Contents/Resources/main.py`:
- Line ~285: Change default period
- Line ~293: Change default states
- Line ~301: Change default method

### Add Your Own Stocks
The app accepts any valid US stock ticker!

---

## 🔄 Updating the App

If you update the Python code:
1. Copy new `.py` files to `Stock Predictor.app/Contents/Resources/`
2. That's it! Next launch uses new code

If you update dependencies:
1. Delete `Stock Predictor.app/Contents/Resources/venv/`
2. Next launch will recreate it with new packages

---

## 📤 Sharing the App

### To Share with Others:
1. **Zip the app**: Right-click → Compress
2. **Share the .zip file**
3. **Include these instructions**

### Requirements for Recipients:
- ✅ macOS 10.13 or later
- ✅ Python 3 installed (usually pre-installed on Mac)
- ✅ Internet connection (for first launch only)

---

## ⚠️ Important Disclaimers

- This is an **educational tool** for learning Markov chains
- **NOT financial advice** - always do your own research
- Past performance doesn't guarantee future results
- Use as ONE factor in decision-making
- Never invest more than you can afford to lose

---

## 🆘 Need Help?

### Quick References:
- **QUICK_START.md** - Command reference
- **TESTING_GUIDE.md** - Detailed testing examples
- **README.md** - Technical documentation

### Common Questions:

**Q: How accurate are the predictions?**
A: The app shows probability distributions, not guarantees. Always check the backtest results to see historical accuracy.

**Q: Can I use it for crypto?**
A: Currently only US stocks are supported (via Yahoo Finance).

**Q: How often should I run it?**
A: Daily for best results, as predictions are for the next day.

**Q: Can I automate it?**
A: Yes! Use command-line mode with cron jobs (see TESTING_GUIDE.md).

---

## 🎓 Learning Resources

### Understanding the Output:
- **Expected Price**: Average of all simulated outcomes
- **Confidence Interval**: Range where true price likely falls
- **Probability Up/Down**: Likelihood of price movement
- **VaR (Value at Risk)**: Maximum expected loss in worst 5% scenarios

### The Math Behind It:
- **Markov Chains**: Model state transitions based on history
- **Monte Carlo**: Runs thousands of simulations
- **State Discretization**: Groups similar price patterns
- **Ensemble Models**: Combines multiple approaches

---

## 🎉 You're All Set!

**To get started:**
1. Double-click **"Stock Predictor.app"**
2. Enter a stock ticker (try AAPL)
3. Press Enter through all questions (uses defaults)
4. Watch the magic happen! ✨

**Pro tip:** Add the app to your Dock for quick daily predictions!

---

Happy Predicting! 📈🚀

*Remember: This tool helps you understand market patterns using mathematics. Use it wisely alongside other research methods.*
