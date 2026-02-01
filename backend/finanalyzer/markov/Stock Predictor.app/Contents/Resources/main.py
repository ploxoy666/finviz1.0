#!/usr/bin/env python3
"""
Stock Market Prediction using Markov Chains
Main CLI Application
"""

import sys
import argparse
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from data_fetcher import StockDataFetcher
from state_discretizer import StateDiscretizer
from markov_models import MarkovChain, HiddenMarkovModel, EnsembleMarkovModel
from predictor import StockPredictor
from backtester import Backtester
from visualizer import StockVisualizer
from market_context import MarketContextAnalyzer, SentimentAnalyzer


def print_banner():
    """Print application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     STOCK MARKET PREDICTION USING MARKOV CHAINS              ║
    ║     Advanced Probabilistic Forecasting System                ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def fetch_and_preprocess_data(ticker, period="2y"):
    """Fetch and preprocess stock data"""
    print(f"\n{'='*60}")
    print(f"FETCHING DATA FOR {ticker}")
    print(f"{'='*60}")
    
    fetcher = StockDataFetcher(ticker, period=period)
    
    if not fetcher.fetch_data():
        print("Error: Could not fetch stock data. Please check the ticker symbol.")
        return None, None
    
    data = fetcher.preprocess()
    
    # Fetch market context
    print("\nFetching market context (S&P 500 & VIX)...")
    market_analyzer = MarketContextAnalyzer()
    try:
        market_analyzer.fetch_sp500_data(period=period)
        market_analyzer.fetch_vix_data(period=period)
        correlation = market_analyzer.calculate_market_correlation(data)
        print(market_analyzer.get_market_summary())
    except Exception as e:
        print(f"Note: Market context unavailable ({str(e)[:50]}...)")
    
    # Display summary statistics
    stats = fetcher.get_summary_statistics()
    print(f"\n{'='*60}")
    print("DATA SUMMARY")
    print(f"{'='*60}")
    print(f"Current Price:        ${stats['current_price']:.2f}")
    print(f"Period Return:        {stats['period_return']:.2f}%")
    print(f"Avg Daily Return:     {stats['avg_daily_return']:.2f}%")
    print(f"Volatility:           {stats['volatility']:.2f}%")
    print(f"Price Range:          ${stats['min_price']:.2f} - ${stats['max_price']:.2f}")
    print(f"Data Points:          {stats['data_points']}")
    
    return fetcher, data


def build_models(data, n_states=5, discretization_method='returns'):
    """Build and train Markov models"""
    print(f"\n{'='*60}")
    print("BUILDING MARKOV MODELS")
    print(f"{'='*60}")
    
    # Discretize states
    print(f"\nDiscretizing data using '{discretization_method}' method with {n_states} states...")
    discretizer = StateDiscretizer(n_states=n_states, method=discretization_method)
    states = discretizer.fit_transform(data)
    
    # Add states to data
    data['State'] = states
    
    # Display state information
    print(f"\n{discretizer.describe_states()}")
    
    # Get state statistics
    state_stats = discretizer.get_state_statistics(data, states)
    print("\nState Statistics:")
    for state, stats in state_stats.items():
        print(f"  {stats['label']}: {stats['frequency']*100:.1f}% frequency, "
              f"Avg Return: {stats['avg_return']*100:.2f}% (if available)")
    
    # Build first-order Markov chain
    print("\nTraining First-Order Markov Chain...")
    mc1 = MarkovChain(order=1)
    mc1.fit(states)
    print("✓ First-order model trained")
    
    # Build second-order Markov chain
    print("Training Second-Order Markov Chain...")
    mc2 = MarkovChain(order=2)
    mc2.fit(states)
    print("✓ Second-order model trained")
    
    # Build third-order Markov chain
    print("Training Third-Order Markov Chain...")
    mc3 = MarkovChain(order=3)
    mc3.fit(states)
    print("✓ Third-order model trained")
    
    # Build weighted ensemble
    print("Creating Weighted Ensemble...")
    ensemble = EnsembleMarkovModel()
    ensemble.add_model(mc1)
    ensemble.add_model(mc2)
    ensemble.add_model(mc3)
    
    # Optimize weights based on recent data
    print("Optimizing ensemble weights...")
    try:
        ensemble.optimize_weights_backtest(data, states)
        print(f"✓ Optimized weights: {[f'{w:.2f}' for w in ensemble.weights]}")
    except:
        print("✓ Using equal weights (optimization skipped)")
    
    print("✓ Weighted ensemble created")
    
    return discretizer, states, mc1, ensemble, state_stats


def make_predictions(ticker, data, markov_model, discretizer, n_days=1):
    """Make price predictions"""
    print(f"\n{'='*60}")
    print(f"GENERATING PREDICTIONS FOR {ticker}")
    print(f"{'='*60}")
    
    # Get current state
    current_state = data['State'].iloc[-1]
    current_price = data['Close'].iloc[-1]
    
    print(f"\nCurrent Price: ${current_price:.2f}")
    print(f"Current State: {discretizer.state_labels.get(current_state, f'State {current_state}')}")
    
    # Create predictor
    predictor = StockPredictor(markov_model, discretizer, data)
    
    if n_days == 1:
        # Single day prediction
        print("\nRunning Monte Carlo simulation (5000 simulations)...")
        predictions = predictor.predict_next_day(current_state, n_simulations=5000)
        
        # Display results
        summary = predictor.get_prediction_summary(predictions)
        print(f"\n{summary}")
        
        return predictions, predictor
    else:
        # Multi-day prediction
        print(f"\nGenerating {n_days}-day forecast (2000 simulations)...")
        predictions = predictor.predict_multi_day(current_state, n_days=n_days, n_simulations=2000)
        
        # Display results
        print(f"\n{'='*60}")
        print(f"{n_days}-DAY FORECAST")
        print(f"{'='*60}")
        
        for day_pred in predictions['daily_predictions']:
            print(f"\nDay {day_pred['day']}:")
            print(f"  Expected Price: ${day_pred['expected_price']:.2f}")
            print(f"  95% CI: ${day_pred['confidence_95_lower']:.2f} - ${day_pred['confidence_95_upper']:.2f}")
            print(f"  Expected Return: {(day_pred['expected_price']-current_price)/current_price*100:.2f}%")
        
        return predictions, predictor


def run_backtest(ticker, data, states, markov_model, discretizer):
    """Run backtest analysis"""
    print(f"\n{'='*60}")
    print("RUNNING BACKTEST")
    print(f"{'='*60}")
    
    # Create backtester
    backtester = Backtester(data, states, markov_model, discretizer)
    
    # Run backtest
    print("\nSplitting data (70% train, 30% test)...")
    results = backtester.run_backtest(train_size=0.7, n_simulations=100)
    
    # Display results
    summary = backtester.get_backtest_summary()
    print(f"\n{summary}")
    
    # Compare with baselines
    comparison = backtester.compare_with_baseline()
    if comparison:
        print(f"\n{'='*60}")
        print("BASELINE COMPARISON")
        print(f"{'='*60}")
        print(f"Model Accuracy:              {comparison['model_accuracy']:.2f}%")
        print(f"Random Baseline:             {comparison['random_baseline']:.2f}%")
        print(f"Always Up Baseline:          {comparison['always_up_baseline']:.2f}%")
        print(f"Naive Baseline:              {comparison['naive_baseline']:.2f}%")
        print(f"Improvement over Random:     {comparison['improvement_over_random']:+.2f}%")
        print(f"Improvement over Naive:      {comparison['improvement_over_naive']:+.2f}%")
    
    return results, backtester


def visualize_results(ticker, data, predictions, state_stats, discretizer, markov_model, backtest_results=None):
    """Create visualizations"""
    print(f"\n{'='*60}")
    print("GENERATING VISUALIZATIONS")
    print(f"{'='*60}")
    
    visualizer = StockVisualizer(data, ticker)
    
    # Historical prices
    print("\n1. Plotting historical prices...")
    visualizer.plot_historical_prices()
    
    # Technical indicators
    print("2. Plotting technical indicators...")
    visualizer.plot_technical_indicators()
    
    # Predictions
    if 'all_paths' in predictions:
        # Multi-day prediction
        print("3. Plotting multi-day forecast...")
        visualizer.plot_multi_day_prediction(predictions)
    else:
        # Single-day prediction
        print("3. Plotting prediction analysis...")
        visualizer.plot_prediction(predictions)
    
    # State analysis
    print("4. Plotting state statistics...")
    visualizer.plot_state_statistics(state_stats)
    
    # Transition matrix
    if hasattr(markov_model, 'transition_matrix') and isinstance(markov_model.transition_matrix, dict) == False:
        print("5. Plotting transition matrix...")
        visualizer.plot_transition_matrix(markov_model.transition_matrix, discretizer.state_labels)
    
    # Backtest results
    if backtest_results:
        print("6. Plotting backtest results...")
        visualizer.plot_backtest_results(backtest_results)
    
    print("\n✓ All visualizations generated")


def print_step_header(step, total, title):
    """Print formatted step header"""
    print("\n" + "─" * 65)
    print(f"📍 Step {step} of {total}: {title}")
    print("─" * 65)


def interactive_mode():
    """Run in enhanced interactive mode with step-by-step wizard"""
    print_banner()
    
    print("\n" + "=" * 65)
    print("           📈 WELCOME TO THE PREDICTION WIZARD")
    print("=" * 65)
    print("\nLet's predict stock prices using Markov chains!")
    print("Just answer a few questions, and we'll handle the rest.\n")
    print("💡 Press Enter to use recommended defaults (marked with ⭐)")
    
    # STEP 1: Ticker
    print_step_header(1, 7, "Choose Your Stock")
    print("\n📊 Enter a stock ticker symbol")
    print("   Popular choices: AAPL, TSLA, MSFT, GOOGL, NVDA, AMZN")
    print("   (Must be a valid US stock ticker)")
    
    ticker = ""
    while not ticker:
        ticker = input("\n➤ Your choice: ").strip().upper()
        if not ticker:
            print("❌ Please enter a ticker symbol")
    
    print(f"✓ Selected: {ticker}")
    
    # STEP 2: Period
    print_step_header(2, 7, "Select Time Period")
    print("\n⏰ How much historical data should we analyze?")
    print("\n   [1] 1 month    - Very recent trends only")
    print("   [2] 3 months   - Short term analysis")
    print("   [3] 6 months   - Medium term view")
    print("   [4] 1 year     - Annual perspective")
    print("   [5] 2 years    - Recommended ⭐ (best balance)")
    print("   [6] 5 years    - Long term patterns")
    
    period_map = {'1': '1mo', '2': '3mo', '3': '6mo', '4': '1y', '5': '2y', '6': '5y'}
    period_desc = {'1': '1 month', '2': '3 months', '3': '6 months', '4': '1 year', '5': '2 years', '6': '5 years'}
    
    period_choice = input("\n➤ Your choice [5]: ").strip() or '5'
    period = period_map.get(period_choice, '2y')
    print(f"✓ Selected: {period_desc.get(period_choice, '2 years')}")
    
    # STEP 3: States
    print_step_header(3, 7, "Number of Market States")
    print("\n📈 How detailed should the model be?")
    print("   (More states = more detailed predictions)")
    print("\n   [1] 3 states   - Simple (Down, Neutral, Up)")
    print("   [2] 5 states   - Recommended ⭐ (detailed)")
    print("   [3] 7 states   - Very detailed (complex)")
    
    n_states_map = {'1': 3, '2': 5, '3': 7}
    n_states_choice = input("\n➤ Your choice [2]: ").strip() or '2'
    n_states = n_states_map.get(n_states_choice, 5)
    print(f"✓ Selected: {n_states} states")
    
    # STEP 4: Method
    print_step_header(4, 7, "Prediction Method")
    print("\n🔬 Which mathematical approach should we use?")
    print("\n   [1] Returns-based    - Recommended ⭐ (price changes)")
    print("   [2] Volatility-based - Focus on risk/stability")
    print("   [3] K-Means         - AI clustering (advanced)")
    print("   [4] Hybrid          - Combined approach")
    
    method_map = {'1': 'returns', '2': 'volatility', '3': 'kmeans', '4': 'hybrid'}
    method_desc = {'1': 'Returns-based', '2': 'Volatility-based', '3': 'K-Means clustering', '4': 'Hybrid'}
    method_choice = input("\n➤ Your choice [1]: ").strip() or '1'
    method = method_map.get(method_choice, 'returns')
    print(f"✓ Selected: {method_desc.get(method_choice, 'Returns-based')}")
    
    # Fetch and process data
    fetcher, data = fetch_and_preprocess_data(ticker, period)
    if data is None:
        print("\n❌ Failed to fetch data. Please check the ticker symbol and try again.")
        return
    
    # Build models
    discretizer, states, mc1, ensemble, state_stats = build_models(data, n_states, method)
    
    # STEP 5: Forecast days
    print_step_header(5, 7, "Forecast Horizon")
    print("\n🔮 How many days ahead should we predict?")
    print("\n   [1] Tomorrow only  - Single day ⭐ (most accurate)")
    print("   [2] Next 3 days    - Short term forecast")
    print("   [3] Next 5 days    - Week ahead view")
    print("   [4] Next 10 days   - Extended forecast")
    
    n_days_map = {'1': 1, '2': 3, '3': 5, '4': 10}
    n_days_desc = {'1': 'Tomorrow only', '2': '3 days', '3': '5 days', '4': '10 days'}
    n_days_choice = input("\n➤ Your choice [1]: ").strip() or '1'
    n_days = n_days_map.get(n_days_choice, 1)
    print(f"✓ Selected: {n_days_desc.get(n_days_choice, 'Tomorrow only')}")
    
    # STEP 6: Backtest
    print_step_header(6, 7, "Run Backtest")
    print("\n✅ Should we validate the model on historical data?")
    print("   (Shows how accurate predictions would have been)")
    print("\n   [Y] Yes - Validate accuracy ⭐")
    print("   [N] No  - Skip validation (faster)")
    
    backtest_choice = input("\n➤ Your choice [Y]: ").strip().upper() or 'Y'
    run_backtest_flag = backtest_choice == 'Y'
    print(f"✓ Selected: {'Yes, run backtest' if run_backtest_flag else 'No, skip backtest'}")
    
    # STEP 7: Visualizations
    print_step_header(7, 7, "Show Visualizations")
    print("\n📊 Should we generate charts and graphs?")
    print("   (Takes a bit longer but very helpful)")
    print("\n   [Y] Yes - Show all charts ⭐")
    print("   [N] No  - Text results only (faster)")
    
    viz_choice = input("\n➤ Your choice [Y]: ").strip().upper() or 'Y'
    show_viz = viz_choice == 'Y'
    print(f"✓ Selected: {'Yes, show visualizations' if show_viz else 'No, text only'}")
    
    # Summary of choices
    print("\n" + "=" * 65)
    print("📋 YOUR CHOICES SUMMARY")
    print("=" * 65)
    print(f"Stock:          {ticker}")
    print(f"Time Period:    {period_desc.get(period_choice, '2 years')}")
    print(f"States:         {n_states}")
    print(f"Method:         {method_desc.get(method_choice, 'Returns-based')}")
    print(f"Forecast:       {n_days_desc.get(n_days_choice, 'Tomorrow only')}")
    print(f"Backtest:       {'Yes' if run_backtest_flag else 'No'}")
    print(f"Visualizations: {'Yes' if show_viz else 'No'}")
    print("=" * 65)
    
    input("\n🚀 Press Enter to start the analysis...")
    
    # Run analysis
    predictions = None
    backtest_results = None
    
    # Make predictions
    predictions, predictor = make_predictions(ticker, data, ensemble, discretizer, n_days=n_days)
    
    # Run backtest if requested
    if run_backtest_flag:
        backtest_results, backtester = run_backtest(ticker, data, states, mc1, discretizer)
    
    # Generate visualizations
    if show_viz:
        visualize_results(ticker, data, predictions, state_stats, discretizer, mc1, backtest_results)
    
    print(f"\n{'='*65}")
    print("✨ ANALYSIS COMPLETE")
    print(f"{'='*65}")
    print(f"\n🎉 Thank you for using the Stock Market Prediction System!")
    print(f"💡 Tip: Run again with different parameters to compare results.\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Stock Market Prediction using Markov Chains',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Interactive mode
  %(prog)s --ticker AAPL                # Quick analysis of AAPL
  %(prog)s --ticker TSLA --predict 5    # 5-day forecast for TSLA
  %(prog)s --ticker MSFT --backtest     # Backtest MSFT predictions
  %(prog)s --ticker GOOGL --full        # Full analysis with visualizations
        """
    )
    
    parser.add_argument('--ticker', '-t', type=str,
                       help='Stock ticker symbol (e.g., AAPL, TSLA)')
    parser.add_argument('--period', '-p', type=str, default='2y',
                       choices=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
                       help='Historical data period (default: 2y)')
    parser.add_argument('--states', '-s', type=int, default=5,
                       choices=[3, 5, 7],
                       help='Number of states (default: 5)')
    parser.add_argument('--method', '-m', type=str, default='returns',
                       choices=['returns', 'volatility', 'kmeans', 'hybrid'],
                       help='Discretization method (default: returns)')
    parser.add_argument('--predict', type=int, metavar='DAYS',
                       help='Generate N-day price forecast')
    parser.add_argument('--backtest', action='store_true',
                       help='Run backtest analysis')
    parser.add_argument('--full', action='store_true',
                       help='Run full analysis with all features')
    parser.add_argument('--no-viz', action='store_true',
                       help='Skip visualization generation')
    
    args = parser.parse_args()
    
    # If no ticker provided, run interactive mode
    if not args.ticker:
        interactive_mode()
        return
    
    # Command-line mode
    print_banner()
    
    # Fetch data
    fetcher, data = fetch_and_preprocess_data(args.ticker, args.period)
    if data is None:
        sys.exit(1)
    
    # Build models
    discretizer, states, mc1, ensemble, state_stats = build_models(
        data, args.states, args.method
    )
    
    predictions = None
    backtest_results = None
    
    # Run analysis
    if args.full or args.predict:
        n_days = args.predict if args.predict else 1
        predictions, predictor = make_predictions(args.ticker, data, ensemble, discretizer, n_days)
    
    if args.full or args.backtest:
        backtest_results, backtester = run_backtest(args.ticker, data, states, mc1, discretizer)
    
    # Generate visualizations
    if not args.no_viz:
        if predictions is None:
            predictions, predictor = make_predictions(args.ticker, data, ensemble, discretizer, n_days=1)
        visualize_results(args.ticker, data, predictions, state_stats, discretizer, mc1, backtest_results)
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
