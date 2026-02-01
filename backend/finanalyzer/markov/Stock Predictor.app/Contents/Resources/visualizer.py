"""
Visualizer Module
Creates comprehensive visualizations for stock predictions
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class StockVisualizer:
    """Creates visualizations for stock prediction analysis"""
    
    def __init__(self, data, ticker):
        """
        Initialize visualizer
        
        Args:
            data (pd.DataFrame): Stock data
            ticker (str): Stock ticker symbol
        """
        self.data = data
        self.ticker = ticker
        
    def plot_historical_prices(self, save_path=None):
        """Plot historical stock prices with volume"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # Price plot
        ax1.plot(self.data.index, self.data['Close'], label='Close Price', 
                color='#2E86AB', linewidth=2)
        ax1.fill_between(self.data.index, self.data['Low'], self.data['High'],
                        alpha=0.3, color='#A23B72', label='Daily Range')
        
        # Moving averages
        if 'SMA_20' in self.data.columns:
            ax1.plot(self.data.index, self.data['SMA_20'], 
                    label='SMA 20', linestyle='--', alpha=0.7)
        if 'SMA_50' in self.data.columns:
            ax1.plot(self.data.index, self.data['SMA_50'], 
                    label='SMA 50', linestyle='--', alpha=0.7)
        
        ax1.set_title(f'{self.ticker} - Historical Stock Prices', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Volume plot
        colors = ['green' if self.data['Close'].iloc[i] >= self.data['Open'].iloc[i] 
                 else 'red' for i in range(len(self.data))]
        ax2.bar(self.data.index, self.data['Volume'], color=colors, alpha=0.5)
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
    def plot_prediction(self, predictions, save_path=None):
        """Plot single-day prediction results"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # Plot 1: Price distribution
        ax1 = axes[0, 0]
        simulated_prices = predictions['simulated_prices']
        ax1.hist(simulated_prices, bins=50, alpha=0.7, color='#2E86AB', edgecolor='black')
        ax1.axvline(predictions['current_price'], color='red', linestyle='--', 
                   linewidth=2, label=f'Current: ${predictions["current_price"]:.2f}')
        ax1.axvline(predictions['expected_price'], color='green', linestyle='--', 
                   linewidth=2, label=f'Expected: ${predictions["expected_price"]:.2f}')
        ax1.axvline(predictions['confidence_95_lower'], color='orange', linestyle=':', 
                   linewidth=1.5, label='95% CI')
        ax1.axvline(predictions['confidence_95_upper'], color='orange', linestyle=':', 
                   linewidth=1.5)
        ax1.set_xlabel('Price ($)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.set_title('Predicted Price Distribution', fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Return distribution
        ax2 = axes[0, 1]
        simulated_returns = predictions['simulated_returns'] * 100
        ax2.hist(simulated_returns, bins=50, alpha=0.7, color='#F18F01', edgecolor='black')
        ax2.axvline(0, color='red', linestyle='--', linewidth=2)
        ax2.axvline(predictions['expected_return']*100, color='green', 
                   linestyle='--', linewidth=2, 
                   label=f'Expected: {predictions["expected_return"]*100:.2f}%')
        ax2.set_xlabel('Return (%)', fontsize=11)
        ax2.set_ylabel('Frequency', fontsize=11)
        ax2.set_title('Predicted Return Distribution', fontsize=13, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: State distribution
        ax3 = axes[1, 0]
        state_dist = predictions['state_distribution']
        states = list(state_dist.keys())
        probs = list(state_dist.values())
        bars = ax3.bar(states, probs, color='#C73E1D', alpha=0.7, edgecolor='black')
        ax3.set_xlabel('State', fontsize=11)
        ax3.set_ylabel('Probability', fontsize=11)
        ax3.set_title('Next State Probability Distribution', fontsize=13, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Plot 4: Summary statistics
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        stats_text = f"""
        PREDICTION SUMMARY
        ═══════════════════════════════════════
        
        Current Price:     ${predictions['current_price']:.2f}
        Expected Price:    ${predictions['expected_price']:.2f}
        Expected Return:   {predictions['expected_return']*100:.2f}%
        
        Confidence Intervals:
        95% CI:  ${predictions['confidence_95_lower']:.2f} - ${predictions['confidence_95_upper']:.2f}
        68% CI:  ${predictions['confidence_68_lower']:.2f} - ${predictions['confidence_68_upper']:.2f}
        
        Probabilities:
        Up:      {predictions['probability_up']*100:.1f}%
        Down:    {predictions['probability_down']*100:.1f}%
        
        Risk (Std Dev):    {predictions['return_std']*100:.2f}%
        """
        
        ax4.text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
                verticalalignment='center')
        
        plt.suptitle(f'{self.ticker} - Price Prediction Analysis', 
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
    def plot_multi_day_prediction(self, predictions, save_path=None):
        """Plot multi-day prediction with confidence bands"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        current_price = predictions['current_price']
        daily_preds = predictions['daily_predictions']
        all_paths = predictions['all_paths']
        
        # Plot 1: Price trajectories
        days = [0] + [p['day'] for p in daily_preds]
        expected_prices = [current_price] + [p['expected_price'] for p in daily_preds]
        upper_95 = [current_price] + [p['confidence_95_upper'] for p in daily_preds]
        lower_95 = [current_price] + [p['confidence_95_lower'] for p in daily_preds]
        upper_68 = [current_price] + [p['confidence_68_upper'] for p in daily_preds]
        lower_68 = [current_price] + [p['confidence_68_lower'] for p in daily_preds]
        
        # Plot sample paths
        n_sample_paths = min(50, len(all_paths))
        for i in range(n_sample_paths):
            path = [current_price] + list(all_paths[i])
            ax1.plot(days, path, color='gray', alpha=0.1, linewidth=0.5)
        
        # Plot confidence bands
        ax1.fill_between(days, lower_95, upper_95, alpha=0.2, color='orange', 
                        label='95% Confidence Interval')
        ax1.fill_between(days, lower_68, upper_68, alpha=0.3, color='blue', 
                        label='68% Confidence Interval')
        
        # Plot expected price
        ax1.plot(days, expected_prices, color='green', linewidth=3, 
                label='Expected Price', marker='o')
        ax1.plot(0, current_price, 'ro', markersize=10, label='Current Price')
        
        ax1.set_xlabel('Days Ahead', fontsize=12)
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.set_title(f'{self.ticker} - Multi-Day Price Forecast', 
                     fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Expected returns
        expected_returns = [(p['expected_price'] - current_price) / current_price * 100 
                           for p in daily_preds]
        ax2.bar(range(1, len(expected_returns) + 1), expected_returns, 
               color=['green' if r > 0 else 'red' for r in expected_returns],
               alpha=0.7, edgecolor='black')
        ax2.axhline(0, color='black', linestyle='-', linewidth=1)
        ax2.set_xlabel('Days Ahead', fontsize=12)
        ax2.set_ylabel('Expected Return (%)', fontsize=12)
        ax2.set_title('Expected Returns by Day', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
    def plot_transition_matrix(self, transition_matrix, state_labels, save_path=None):
        """Plot state transition matrix heatmap"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create labels
        labels = [state_labels.get(i, f'S{i}') for i in range(len(state_labels))]
        
        # Plot heatmap
        sns.heatmap(transition_matrix, annot=True, fmt='.3f', cmap='YlOrRd',
                   xticklabels=labels, yticklabels=labels, ax=ax,
                   cbar_kws={'label': 'Transition Probability'})
        
        ax.set_title(f'{self.ticker} - State Transition Matrix', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('To State', fontsize=12)
        ax.set_ylabel('From State', fontsize=12)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
    def plot_state_statistics(self, state_stats, save_path=None):
        """Plot statistics for each state"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        states = list(state_stats.keys())
        labels = [state_stats[s]['label'] for s in states]
        frequencies = [state_stats[s]['frequency'] * 100 for s in states]
        avg_returns = [state_stats[s]['avg_return'] * 100 if state_stats[s]['avg_return'] else 0 
                      for s in states]
        avg_volatilities = [state_stats[s]['avg_volatility'] * 100 if state_stats[s]['avg_volatility'] else 0 
                           for s in states]
        
        # Plot 1: State frequencies
        ax1 = axes[0, 0]
        ax1.bar(range(len(states)), frequencies, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax1.set_xticks(range(len(states)))
        ax1.set_xticklabels(labels, rotation=45, ha='right')
        ax1.set_ylabel('Frequency (%)', fontsize=11)
        ax1.set_title('State Frequencies', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Plot 2: Average returns per state
        ax2 = axes[0, 1]
        colors = ['green' if r > 0 else 'red' for r in avg_returns]
        ax2.bar(range(len(states)), avg_returns, color=colors, alpha=0.7, edgecolor='black')
        ax2.axhline(0, color='black', linestyle='-', linewidth=1)
        ax2.set_xticks(range(len(states)))
        ax2.set_xticklabels(labels, rotation=45, ha='right')
        ax2.set_ylabel('Average Return (%)', fontsize=11)
        ax2.set_title('Average Returns by State', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Plot 3: Average volatility per state
        ax3 = axes[1, 0]
        ax3.bar(range(len(states)), avg_volatilities, color='#F18F01', 
               alpha=0.7, edgecolor='black')
        ax3.set_xticks(range(len(states)))
        ax3.set_xticklabels(labels, rotation=45, ha='right')
        ax3.set_ylabel('Average Volatility (%)', fontsize=11)
        ax3.set_title('Average Volatility by State', fontsize=13, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Plot 4: Risk-return scatter
        ax4 = axes[1, 1]
        ax4.scatter(avg_volatilities, avg_returns, s=200, alpha=0.6, 
                   c=range(len(states)), cmap='viridis', edgecolor='black', linewidth=2)
        
        for i, label in enumerate(labels):
            ax4.annotate(label, (avg_volatilities[i], avg_returns[i]), 
                        fontsize=9, ha='center')
        
        ax4.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax4.axvline(np.mean(avg_volatilities), color='gray', 
                   linestyle='--', linewidth=1, alpha=0.5)
        ax4.set_xlabel('Volatility (%)', fontsize=11)
        ax4.set_ylabel('Return (%)', fontsize=11)
        ax4.set_title('Risk-Return Profile by State', fontsize=13, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.suptitle(f'{self.ticker} - State Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
    def plot_backtest_results(self, backtest_results, save_path=None):
        """Plot backtest performance"""
        predictions = backtest_results['predictions']
        metrics = backtest_results['metrics']
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # Plot 1: Predicted vs Actual prices
        ax1 = axes[0, 0]
        ax1.plot(predictions['date'], predictions['actual_price'], 
                label='Actual Price', linewidth=2, color='blue')
        ax1.plot(predictions['date'], predictions['predicted_price'], 
                label='Predicted Price', linewidth=2, color='red', alpha=0.7)
        ax1.fill_between(predictions['date'], 
                        predictions['actual_price'], 
                        predictions['predicted_price'],
                        alpha=0.3, color='gray')
        ax1.set_xlabel('Date', fontsize=11)
        ax1.set_ylabel('Price ($)', fontsize=11)
        ax1.set_title('Predicted vs Actual Prices', fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Plot 2: Prediction errors
        ax2 = axes[0, 1]
        ax2.plot(predictions['date'], predictions['error'], 
                color='red', linewidth=1.5)
        ax2.fill_between(predictions['date'], 0, predictions['error'],
                        alpha=0.3, color='red')
        ax2.set_xlabel('Date', fontsize=11)
        ax2.set_ylabel('Absolute Error ($)', fontsize=11)
        ax2.set_title('Prediction Errors Over Time', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # Plot 3: Direction accuracy
        ax3 = axes[1, 0]
        correct = predictions['direction_correct'].astype(int)
        cumulative_accuracy = correct.expanding().mean() * 100
        ax3.plot(predictions['date'], cumulative_accuracy, 
                linewidth=2, color='green')
        ax3.axhline(50, color='red', linestyle='--', linewidth=1.5, 
                   label='Random Baseline (50%)')
        ax3.axhline(metrics['direction_accuracy']*100, color='blue', 
                   linestyle='--', linewidth=1.5, 
                   label=f'Overall: {metrics["direction_accuracy"]*100:.1f}%')
        ax3.set_xlabel('Date', fontsize=11)
        ax3.set_ylabel('Cumulative Accuracy (%)', fontsize=11)
        ax3.set_title('Direction Prediction Accuracy', fontsize=13, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim([0, 100])
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        # Plot 4: Performance metrics summary
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        metrics_text = f"""
        BACKTEST PERFORMANCE METRICS
        ═══════════════════════════════════════
        
        Direction Accuracy:    {metrics['direction_accuracy']*100:.2f}%
        
        Mean Abs Error (MAE):  ${metrics['mae']:.2f}
        MAE Percentage:        {metrics['mae_pct']:.2f}%
        
        RMSE:                  ${metrics['rmse']:.2f}
        RMSE Percentage:       {metrics['rmse_pct']:.2f}%
        
        MAPE:                  {metrics['mape']:.2f}%
        R-squared:             {metrics['r_squared']:.4f}
        Correlation:           {metrics['correlation']:.4f}
        
        Test Period:           {len(predictions)} days
        """
        
        ax4.text(0.1, 0.5, metrics_text, fontsize=11, family='monospace',
                verticalalignment='center')
        
        plt.suptitle(f'{self.ticker} - Backtest Results', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
    def plot_technical_indicators(self, save_path=None):
        """Plot technical indicators"""
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        # Plot 1: Price with Bollinger Bands
        ax1 = axes[0]
        ax1.plot(self.data.index, self.data['Close'], label='Close Price', linewidth=2)
        if 'BB_Upper' in self.data.columns:
            ax1.plot(self.data.index, self.data['BB_Upper'], 
                    linestyle='--', alpha=0.7, label='BB Upper')
            ax1.plot(self.data.index, self.data['BB_Lower'], 
                    linestyle='--', alpha=0.7, label='BB Lower')
            ax1.fill_between(self.data.index, self.data['BB_Lower'], 
                           self.data['BB_Upper'], alpha=0.1)
        ax1.set_ylabel('Price ($)', fontsize=11)
        ax1.set_title('Price with Bollinger Bands', fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: RSI
        ax2 = axes[1]
        if 'RSI' in self.data.columns:
            ax2.plot(self.data.index, self.data['RSI'], linewidth=2, color='purple')
            ax2.axhline(70, color='red', linestyle='--', linewidth=1, alpha=0.7)
            ax2.axhline(30, color='green', linestyle='--', linewidth=1, alpha=0.7)
            ax2.fill_between(self.data.index, 30, 70, alpha=0.1, color='gray')
        ax2.set_ylabel('RSI', fontsize=11)
        ax2.set_title('Relative Strength Index (RSI)', fontsize=13, fontweight='bold')
        ax2.set_ylim([0, 100])
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: MACD
        ax3 = axes[2]
        if 'MACD' in self.data.columns:
            ax3.plot(self.data.index, self.data['MACD'], label='MACD', linewidth=2)
            ax3.plot(self.data.index, self.data['MACD_Signal'], 
                    label='Signal', linewidth=2)
            ax3.bar(self.data.index, self.data['MACD_Hist'], 
                   label='Histogram', alpha=0.3)
            ax3.axhline(0, color='black', linestyle='-', linewidth=1)
        ax3.set_xlabel('Date', fontsize=11)
        ax3.set_ylabel('MACD', fontsize=11)
        ax3.set_title('MACD Indicator', fontsize=13, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        plt.suptitle(f'{self.ticker} - Technical Indicators', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
