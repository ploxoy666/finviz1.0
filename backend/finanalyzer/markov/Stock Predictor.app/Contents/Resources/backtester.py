"""
Backtester Module
Tests the performance of Markov models on historical data
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List


class Backtester:
    """Backtests Markov chain predictions against historical data"""
    
    def __init__(self, data, states, markov_model, discretizer):
        """
        Initialize backtester
        
        Args:
            data (pd.DataFrame): Historical stock data
            states (np.array): State assignments
            markov_model: Fitted Markov model
            discretizer: State discretizer
        """
        self.data = data.copy()
        self.data['State'] = states
        self.markov_model = markov_model
        self.discretizer = discretizer
        self.results = None
        
    def run_backtest(self, train_size=0.7, n_simulations=100):
        """
        Run backtest by splitting data into train/test sets
        
        Args:
            train_size (float): Proportion of data to use for training
            n_simulations (int): Number of simulations per prediction
            
        Returns:
            dict: Backtest results
        """
        split_idx = int(len(self.data) * train_size)
        train_data = self.data.iloc[:split_idx]
        test_data = self.data.iloc[split_idx:]
        
        print(f"Backtesting with {len(train_data)} training samples and {len(test_data)} test samples")
        
        predictions = []
        actuals = []
        dates = []
        
        # For each day in test set, predict and compare
        for i in range(len(test_data) - 1):
            current_state = test_data['State'].iloc[i]
            actual_return = test_data['Returns'].iloc[i + 1]
            actual_price = test_data['Close'].iloc[i + 1]
            current_price = test_data['Close'].iloc[i]
            date = test_data.index[i + 1]
            
            # Predict next state
            predicted_state_dist = self.markov_model.predict_next_state_distribution(current_state)
            
            # Run simulations
            simulated_returns = []
            for _ in range(n_simulations):
                states = list(predicted_state_dist.keys())
                probs = list(predicted_state_dist.values())
                next_state = np.random.choice(states, p=probs)
                
                # Sample return from predicted state
                state_mask = train_data['State'] == next_state
                state_returns = train_data.loc[state_mask, 'Returns'].values
                
                if len(state_returns) > 0:
                    simulated_return = np.random.choice(state_returns)
                    simulated_returns.append(simulated_return)
            
            predicted_return = np.mean(simulated_returns)
            predicted_price = current_price * (1 + predicted_return)
            
            predictions.append({
                'date': date,
                'predicted_price': predicted_price,
                'actual_price': actual_price,
                'predicted_return': predicted_return,
                'actual_return': actual_return,
                'current_price': current_price,
                'error': abs(predicted_price - actual_price),
                'error_pct': abs(predicted_price - actual_price) / actual_price,
                'direction_correct': (predicted_return > 0) == (actual_return > 0)
            })
        
        results_df = pd.DataFrame(predictions)
        
        # Calculate metrics
        metrics = self._calculate_metrics(results_df)
        
        self.results = {
            'predictions': results_df,
            'metrics': metrics,
            'train_size': train_size,
            'test_size': len(test_data),
            'n_simulations': n_simulations
        }
        
        return self.results
    
    def _calculate_metrics(self, results_df):
        """Calculate performance metrics"""
        metrics = {}
        
        # Direction accuracy
        metrics['direction_accuracy'] = results_df['direction_correct'].mean()
        
        # Mean Absolute Error (MAE)
        metrics['mae'] = results_df['error'].mean()
        metrics['mae_pct'] = results_df['error_pct'].mean() * 100
        
        # Root Mean Squared Error (RMSE)
        metrics['rmse'] = np.sqrt((results_df['error'] ** 2).mean())
        metrics['rmse_pct'] = np.sqrt((results_df['error_pct'] ** 2).mean()) * 100
        
        # Mean Absolute Percentage Error (MAPE)
        metrics['mape'] = (results_df['error_pct'] * 100).mean()
        
        # R-squared
        ss_res = ((results_df['actual_price'] - results_df['predicted_price']) ** 2).sum()
        ss_tot = ((results_df['actual_price'] - results_df['actual_price'].mean()) ** 2).sum()
        metrics['r_squared'] = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Correlation
        metrics['correlation'] = results_df['predicted_price'].corr(results_df['actual_price'])
        
        # Return prediction metrics
        return_mae = (results_df['predicted_return'] - results_df['actual_return']).abs().mean()
        metrics['return_mae'] = return_mae
        
        return metrics
    
    def run_walk_forward_backtest(self, initial_train_size=200, step_size=20):
        """
        Run walk-forward backtest with rolling window
        
        Args:
            initial_train_size (int): Initial training window size
            step_size (int): Number of steps to advance window
            
        Returns:
            dict: Walk-forward backtest results
        """
        all_predictions = []
        all_metrics = []
        
        start_idx = initial_train_size
        
        while start_idx < len(self.data) - step_size:
            # Define train and test windows
            train_data = self.data.iloc[start_idx - initial_train_size:start_idx]
            test_data = self.data.iloc[start_idx:start_idx + step_size]
            
            # Retrain model on current window
            train_states = train_data['State'].values
            self.markov_model.fit(train_states)
            
            # Make predictions
            for i in range(len(test_data) - 1):
                current_state = test_data['State'].iloc[i]
                actual_return = test_data['Returns'].iloc[i + 1]
                actual_price = test_data['Close'].iloc[i + 1]
                current_price = test_data['Close'].iloc[i]
                
                # Predict
                predicted_state_dist = self.markov_model.predict_next_state_distribution(current_state)
                
                # Simple prediction using expected value
                predicted_return = 0
                for state, prob in predicted_state_dist.items():
                    state_mask = train_data['State'] == state
                    state_returns = train_data.loc[state_mask, 'Returns'].values
                    if len(state_returns) > 0:
                        predicted_return += prob * state_returns.mean()
                
                predicted_price = current_price * (1 + predicted_return)
                
                all_predictions.append({
                    'date': test_data.index[i + 1],
                    'predicted_price': predicted_price,
                    'actual_price': actual_price,
                    'predicted_return': predicted_return,
                    'actual_return': actual_return,
                    'error': abs(predicted_price - actual_price),
                    'direction_correct': (predicted_return > 0) == (actual_return > 0)
                })
            
            start_idx += step_size
        
        results_df = pd.DataFrame(all_predictions)
        metrics = self._calculate_metrics(results_df)
        
        return {
            'predictions': results_df,
            'metrics': metrics,
            'method': 'walk_forward',
            'initial_train_size': initial_train_size,
            'step_size': step_size
        }
    
    def calculate_trading_performance(self, results, initial_capital=10000):
        """
        Calculate trading performance metrics
        
        Args:
            results (dict): Backtest results
            initial_capital (float): Starting capital
            
        Returns:
            dict: Trading performance metrics
        """
        predictions = results['predictions']
        capital = initial_capital
        positions = []
        
        for idx, row in predictions.iterrows():
            # Simple strategy: Buy if predicted return > 0, Sell if < 0
            if row['predicted_return'] > 0:
                # Buy position
                shares = capital / row['current_price']
                position_value = shares * row['actual_price']
                profit = position_value - capital
                capital = position_value
                positions.append({
                    'date': row['date'],
                    'action': 'BUY',
                    'entry_price': row['current_price'],
                    'exit_price': row['actual_price'],
                    'profit': profit,
                    'capital': capital
                })
        
        if len(positions) > 0:
            total_return = (capital - initial_capital) / initial_capital
            trades_df = pd.DataFrame(positions)
            
            winning_trades = trades_df[trades_df['profit'] > 0]
            losing_trades = trades_df[trades_df['profit'] < 0]
            
            performance = {
                'initial_capital': initial_capital,
                'final_capital': capital,
                'total_return': total_return * 100,
                'total_trades': len(positions),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / len(positions) * 100 if len(positions) > 0 else 0,
                'avg_profit': trades_df['profit'].mean(),
                'max_profit': trades_df['profit'].max(),
                'max_loss': trades_df['profit'].min(),
                'profit_factor': abs(winning_trades['profit'].sum() / losing_trades['profit'].sum()) 
                                if len(losing_trades) > 0 and losing_trades['profit'].sum() != 0 else 0
            }
            
            # Calculate max drawdown
            cumulative_returns = trades_df['capital'].values
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            performance['max_drawdown'] = abs(drawdowns.min() * 100) if len(drawdowns) > 0 else 0
            
            # Sharpe ratio (simplified)
            returns = trades_df['profit'] / initial_capital
            performance['sharpe_ratio'] = returns.mean() / returns.std() if returns.std() > 0 else 0
            
            return performance
        else:
            return None
    
    def get_backtest_summary(self):
        """Generate a summary of backtest results"""
        if self.results is None:
            return "No backtest results available. Run run_backtest() first."
        
        metrics = self.results['metrics']
        
        summary = []
        summary.append("=" * 60)
        summary.append("BACKTEST RESULTS")
        summary.append("=" * 60)
        summary.append(f"\nTest Period: {self.results['test_size']} days")
        summary.append(f"Simulations per prediction: {self.results['n_simulations']}")
        
        summary.append(f"\n{'='*60}")
        summary.append("ACCURACY METRICS")
        summary.append(f"{'='*60}")
        summary.append(f"Direction Accuracy: {metrics['direction_accuracy']*100:.2f}%")
        summary.append(f"Mean Absolute Error: ${metrics['mae']:.2f} ({metrics['mae_pct']:.2f}%)")
        summary.append(f"Root Mean Squared Error: ${metrics['rmse']:.2f} ({metrics['rmse_pct']:.2f}%)")
        summary.append(f"MAPE: {metrics['mape']:.2f}%")
        summary.append(f"R-squared: {metrics['r_squared']:.4f}")
        summary.append(f"Correlation: {metrics['correlation']:.4f}")
        
        # Trading performance
        trading_perf = self.calculate_trading_performance(self.results)
        if trading_perf:
            summary.append(f"\n{'='*60}")
            summary.append("TRADING PERFORMANCE")
            summary.append(f"{'='*60}")
            summary.append(f"Total Return: {trading_perf['total_return']:.2f}%")
            summary.append(f"Win Rate: {trading_perf['win_rate']:.2f}%")
            summary.append(f"Total Trades: {trading_perf['total_trades']}")
            summary.append(f"Sharpe Ratio: {trading_perf['sharpe_ratio']:.2f}")
            summary.append(f"Max Drawdown: {trading_perf['max_drawdown']:.2f}%")
            summary.append(f"Profit Factor: {trading_perf['profit_factor']:.2f}")
        
        return "\n".join(summary)
    
    def compare_with_baseline(self):
        """Compare model performance with baseline strategies"""
        if self.results is None:
            return None
        
        predictions = self.results['predictions']
        
        # Baseline 1: Random prediction (50/50 up/down)
        random_correct = 0.5
        
        # Baseline 2: Always predict up
        always_up_correct = (predictions['actual_return'] > 0).mean()
        
        # Baseline 3: Naive (previous day's return)
        naive_predictions = []
        for i in range(len(predictions) - 1):
            naive_pred = predictions.iloc[i]['actual_return']
            actual = predictions.iloc[i + 1]['actual_return']
            naive_predictions.append((naive_pred > 0) == (actual > 0))
        
        naive_accuracy = np.mean(naive_predictions) if naive_predictions else 0.5
        
        model_accuracy = self.results['metrics']['direction_accuracy']
        
        comparison = {
            'model_accuracy': model_accuracy * 100,
            'random_baseline': random_correct * 100,
            'always_up_baseline': always_up_correct * 100,
            'naive_baseline': naive_accuracy * 100,
            'improvement_over_random': (model_accuracy - random_correct) * 100,
            'improvement_over_naive': (model_accuracy - naive_accuracy) * 100
        }
        
        return comparison
