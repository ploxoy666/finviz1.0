
import os
import sys
import io
import pandas as pd
import matplotlib.pyplot as plt
from contextlib import redirect_stdout
from loguru import logger

# Add the markov app directory to sys.path
# This points to backend/finanalyzer/markov
MARKOV_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "markov")
if MARKOV_DIR not in sys.path:
    sys.path.append(MARKOV_DIR)

# Force Matplotlib to use non-interactive backend
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    from data_fetcher import StockDataFetcher
    from state_discretizer import StateDiscretizer
    from markov_models import MarkovChain, EnsembleMarkovModel
    from predictor import StockPredictor
    from backtester import Backtester
    from visualizer import StockVisualizer
    MARKOV_AVAILABLE = True
except ImportError as e:
    # Try one more time with absolute local import if relative path fails
    try:
        sys.path.append(os.path.join(os.getcwd(), 'finanalyzer', 'markov'))
        from data_fetcher import StockDataFetcher
        from state_discretizer import StateDiscretizer
        from markov_models import MarkovChain, EnsembleMarkovModel
        from predictor import StockPredictor
        from backtester import Backtester
        from visualizer import StockVisualizer
        MARKOV_AVAILABLE = True
    except ImportError as e2:
        logger.error(f"Failed to import Markov Chain modules: {e}")
        logger.error(f"Secondary import attempt failed: {e2}")
        MARKOV_AVAILABLE = False

def run_markov_chain_analysis(ticker, period="2y", n_states=5, method="returns", n_days=5):
    """
    Runs the Markov Chain analysis and captures console output and plots.
    """
    if not MARKOV_AVAILABLE:
        return "Markov Chain modules not found. Check project structure.", None, None, None, None, None

    results_output = io.StringIO()
    
    with redirect_stdout(results_output):
        try:
            print(f"🚀 INITIALIZING MARKOV CHAIN ANALYSIS FOR {ticker}")
            print(f"Settings: Period={period}, States={n_states}, Method={method}, Forecast={n_days} days")
            print("-" * 60)

            # 1. Fetch Data
            fetcher = StockDataFetcher(ticker, period=period)
            if not fetcher.fetch_data():
                print(f"Error: Could not fetch data for {ticker}")
                return results_output.getvalue(), None, None, None, None, None
            
            data = fetcher.preprocess()
            stats = fetcher.get_summary_statistics()
            print(f"✓ Data fetched: {len(data)} points")
            print(f"✓ Current Price: ${stats['current_price']:.2f}")

            # 2. Build Models
            discretizer = StateDiscretizer(n_states=n_states, method=method)
            states = discretizer.fit_transform(data)
            data['State'] = states
            
            print(f"\nDiscretizing data using '{method}' method...")
            print(discretizer.describe_states())

            mc1 = MarkovChain(order=1)
            mc1.fit(states, n_states=n_states)
            
            mc2 = MarkovChain(order=2)
            mc2.fit(states, n_states=n_states)
            
            ensemble = EnsembleMarkovModel()
            ensemble.add_model(mc1)
            ensemble.add_model(mc2)
            
            print("✓ Markov models (Orders 1 & 2) trained and ensembled")

            # 3. Predictions
            predictor = StockPredictor(ensemble, discretizer, data)
            current_state = states[-1]
            
            print(f"\nGenerating {n_days}-day forecast...")
            if n_days == 1:
                predictions = predictor.predict_next_day(current_state, n_simulations=5000)
                print(predictor.get_prediction_summary(predictions))
            else:
                predictions = predictor.predict_multi_day(current_state, n_days=n_days, n_simulations=2000)
                # Normalize for UI: Add final expected price to top level
                predictions['expected_price'] = predictions['daily_predictions'][-1]['expected_price']
                
                print(f"Forecast for next {n_days} days generated.")
                last_day = predictions['daily_predictions'][-1]
                print(f"Final Day Expected Price: ${last_day['expected_price']:.2f} ({ (last_day['expected_price']/stats['current_price']-1)*100:+.2f}%)")

            # 4. Visualizations
            viz = StockVisualizer(data, ticker)
            
            print("\n" + "="*60)
            print("ANALYSIS COMPLETE")
            print("="*60)

            return results_output.getvalue(), predictions, data, viz, discretizer, mc1

        except Exception as e:
            print(f"\n❌ ERROR during analysis: {e}")
            import traceback
            traceback.print_exc(file=results_output)
            return results_output.getvalue(), None, None, None, None, None

