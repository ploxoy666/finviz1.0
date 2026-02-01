"""
Predictor Module
Handles predictions using Markov models with Monte Carlo simulation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


class StockPredictor:
    """Main predictor class that uses Markov models to forecast stock prices"""
    
    def __init__(self, markov_model, discretizer, data):
        """
        Initialize predictor
        
        Args:
            markov_model: Fitted Markov model
            discretizer: Fitted state discretizer
            data (pd.DataFrame): Historical stock data with states
        """
        self.markov_model = markov_model
        self.discretizer = discretizer
        self.data = data
        self.predictions = None
        
    def predict_next_day(self, current_state, n_simulations=5000):
        """
        Predict next day's price using Monte Carlo simulation
        (Increased from 1000 to 5000 for better accuracy)
        
        Args:
            current_state: Current market state
            n_simulations (int): Number of Monte Carlo simulations (default: 5000)
            
        Returns:
            dict: Prediction results with statistics
        """
        # Get probability distribution for next state
        # Handle both regular Markov models and ensemble models
        if hasattr(self.markov_model, 'predict_next_state_distribution'):
            state_probs = self.markov_model.predict_next_state_distribution(current_state)
        elif hasattr(self.markov_model, 'predict_distribution'):
            state_probs = self.markov_model.predict_distribution(current_state)
        else:
            # Fallback for single prediction
            next_state = self.markov_model.predict_next_state(current_state)
            state_probs = {next_state: 1.0}
        
        # Run Monte Carlo simulations
        simulated_returns = []
        simulated_states = []
        
        for _ in range(n_simulations):
            # Sample next state based on probability distribution
            states = list(state_probs.keys())
            probs = list(state_probs.values())
            next_state = np.random.choice(states, p=probs)
            simulated_states.append(next_state)
            
            # Get historical returns for this state
            state_mask = self.data['State'] == next_state
            state_returns = self.data.loc[state_mask, 'Returns'].values
            
            if len(state_returns) > 0:
                # Sample a return from historical returns in this state
                sampled_return = np.random.choice(state_returns)
                simulated_returns.append(sampled_return)
            else:
                # If no historical data for this state, use mean return
                simulated_returns.append(self.data['Returns'].mean())
        
        simulated_returns = np.array(simulated_returns)
        
        # Calculate statistics
        current_price = self.data['Close'].iloc[-1]
        
        # Calculate predicted prices
        predicted_prices = current_price * (1 + simulated_returns)
        
        results = {
            'current_price': current_price,
            'expected_price': np.mean(predicted_prices),
            'median_price': np.median(predicted_prices),
            'price_std': np.std(predicted_prices),
            'expected_return': np.mean(simulated_returns),
            'return_std': np.std(simulated_returns),
            'confidence_95_lower': np.percentile(predicted_prices, 2.5),
            'confidence_95_upper': np.percentile(predicted_prices, 97.5),
            'confidence_68_lower': np.percentile(predicted_prices, 16),
            'confidence_68_upper': np.percentile(predicted_prices, 84),
            'probability_up': np.sum(simulated_returns > 0) / n_simulations,
            'probability_down': np.sum(simulated_returns < 0) / n_simulations,
            'simulated_prices': predicted_prices,
            'simulated_returns': simulated_returns,
            'simulated_states': simulated_states,
            'state_distribution': state_probs
        }
        
        return results
    
    def predict_multi_day(self, current_state, n_days=5, n_simulations=2000):
        """
        Predict multiple days ahead using Monte Carlo simulation
        (Increased from 500 to 2000 for better accuracy)
        
        Args:
            current_state: Current market state
            n_days (int): Number of days to predict
            n_simulations (int): Number of simulation paths (default: 2000)
            
        Returns:
            dict: Multi-day prediction results
        """
        current_price = self.data['Close'].iloc[-1]
        
        # Store all simulation paths
        all_paths = []
        
        for sim in range(n_simulations):
            # Initialize path with current price
            price_path = [current_price]
            state_path = [current_state]
            
            current_sim_state = current_state
            
            for day in range(n_days):
                # Get next state
                if hasattr(self.markov_model, 'predict_next_state_distribution'):
                    state_probs = self.markov_model.predict_next_state_distribution(current_sim_state)
                elif hasattr(self.markov_model, 'predict_distribution'):
                    state_probs = self.markov_model.predict_distribution(current_sim_state)
                else:
                    next_state = self.markov_model.predict_next_state(current_sim_state)
                    state_probs = {next_state: 1.0}
                states = list(state_probs.keys())
                probs = list(state_probs.values())
                next_state = np.random.choice(states, p=probs)
                
                # Get return for next state
                state_mask = self.data['State'] == next_state
                state_returns = self.data.loc[state_mask, 'Returns'].values
                
                if len(state_returns) > 0:
                    sampled_return = np.random.choice(state_returns)
                else:
                    sampled_return = self.data['Returns'].mean()
                
                # Calculate next price
                next_price = price_path[-1] * (1 + sampled_return)
                
                price_path.append(next_price)
                state_path.append(next_state)
                current_sim_state = next_state
            
            all_paths.append(price_path[1:])  # Exclude current price
        
        all_paths = np.array(all_paths)
        
        # Calculate statistics for each day
        daily_predictions = []
        for day in range(n_days):
            day_prices = all_paths[:, day]
            
            daily_pred = {
                'day': day + 1,
                'expected_price': np.mean(day_prices),
                'median_price': np.median(day_prices),
                'std': np.std(day_prices),
                'confidence_95_lower': np.percentile(day_prices, 2.5),
                'confidence_95_upper': np.percentile(day_prices, 97.5),
                'confidence_68_lower': np.percentile(day_prices, 16),
                'confidence_68_upper': np.percentile(day_prices, 84),
                'min_price': np.min(day_prices),
                'max_price': np.max(day_prices)
            }
            daily_predictions.append(daily_pred)
        
        results = {
            'current_price': current_price,
            'n_days': n_days,
            'n_simulations': n_simulations,
            'daily_predictions': daily_predictions,
            'all_paths': all_paths
        }
        
        return results
    
    def calculate_var_cvar(self, predictions, confidence_level=0.95):
        """
        Calculate Value at Risk (VaR) and Conditional VaR (CVaR)
        
        Args:
            predictions (dict): Prediction results
            confidence_level (float): Confidence level for VaR
            
        Returns:
            dict: Risk metrics
        """
        returns = predictions['simulated_returns']
        current_price = predictions['current_price']
        
        # Calculate VaR (Value at Risk)
        var_percentile = (1 - confidence_level) * 100
        var_return = np.percentile(returns, var_percentile)
        var_loss = current_price * abs(var_return) if var_return < 0 else 0
        
        # Calculate CVaR (Conditional VaR) - expected loss beyond VaR
        cvar_returns = returns[returns <= var_return]
        cvar_return = np.mean(cvar_returns) if len(cvar_returns) > 0 else var_return
        cvar_loss = current_price * abs(cvar_return) if cvar_return < 0 else 0
        
        # Maximum drawdown potential
        max_loss = current_price * abs(np.min(returns))
        
        risk_metrics = {
            'var_return': var_return,
            'var_loss': var_loss,
            'cvar_return': cvar_return,
            'cvar_loss': cvar_loss,
            'max_potential_loss': max_loss,
            'confidence_level': confidence_level
        }
        
        return risk_metrics
    
    def get_recommendation(self, predictions):
        """
        Generate trading recommendation based on predictions
        
        Args:
            predictions (dict): Prediction results
            
        Returns:
            dict: Trading recommendation
        """
        prob_up = predictions['probability_up']
        expected_return = predictions['expected_return']
        return_std = predictions['return_std']
        
        # Calculate risk-adjusted return (Sharpe-like ratio)
        risk_adjusted_return = expected_return / return_std if return_std > 0 else 0
        
        # Decision logic
        if prob_up > 0.65 and expected_return > 0.01:
            signal = "STRONG BUY"
            confidence = "High"
        elif prob_up > 0.55 and expected_return > 0.005:
            signal = "BUY"
            confidence = "Medium"
        elif prob_up < 0.35 and expected_return < -0.01:
            signal = "STRONG SELL"
            confidence = "High"
        elif prob_up < 0.45 and expected_return < -0.005:
            signal = "SELL"
            confidence = "Medium"
        else:
            signal = "HOLD"
            confidence = "Medium"
        
        recommendation = {
            'signal': signal,
            'confidence': confidence,
            'expected_return_pct': expected_return * 100,
            'probability_up': prob_up * 100,
            'risk_adjusted_return': risk_adjusted_return,
            'reasoning': self._generate_reasoning(signal, prob_up, expected_return, return_std)
        }
        
        return recommendation
    
    def _generate_reasoning(self, signal, prob_up, expected_return, return_std):
        """Generate reasoning for recommendation"""
        reasoning = []
        
        if signal in ["STRONG BUY", "BUY"]:
            reasoning.append(f"Probability of price increase: {prob_up*100:.1f}%")
            reasoning.append(f"Expected return: {expected_return*100:.2f}%")
        elif signal in ["STRONG SELL", "SELL"]:
            reasoning.append(f"Probability of price decrease: {(1-prob_up)*100:.1f}%")
            reasoning.append(f"Expected return: {expected_return*100:.2f}%")
        else:
            reasoning.append(f"Uncertain market direction (Up: {prob_up*100:.1f}%)")
        
        if return_std > 0.02:
            reasoning.append(f"High volatility expected (σ={return_std*100:.2f}%)")
        elif return_std < 0.01:
            reasoning.append(f"Low volatility expected (σ={return_std*100:.2f}%)")
        
        return " | ".join(reasoning)
    
    def analyze_state_transitions(self):
        """
        Analyze the most likely state transitions
        
        Returns:
            pd.DataFrame: Transition analysis
        """
        if hasattr(self.markov_model, 'transition_matrix'):
            if isinstance(self.markov_model.transition_matrix, np.ndarray):
                # First-order Markov chain
                transitions = []
                for i in range(self.markov_model.n_states):
                    for j in range(self.markov_model.n_states):
                        prob = self.markov_model.transition_matrix[i, j]
                        if prob > 0:
                            from_label = self.discretizer.state_labels.get(i, f'State_{i}')
                            to_label = self.discretizer.state_labels.get(j, f'State_{j}')
                            transitions.append({
                                'from_state': from_label,
                                'to_state': to_label,
                                'probability': prob
                            })
                
                df = pd.DataFrame(transitions)
                return df.sort_values('probability', ascending=False).head(20)
        
        return None
    
    def get_prediction_summary(self, predictions):
        """
        Generate a comprehensive summary of predictions
        
        Args:
            predictions (dict): Prediction results
            
        Returns:
            str: Formatted summary
        """
        summary = []
        summary.append("=" * 60)
        summary.append("STOCK PRICE PREDICTION SUMMARY")
        summary.append("=" * 60)
        summary.append(f"\nCurrent Price: ${predictions['current_price']:.2f}")
        summary.append(f"\nExpected Price (Next Day): ${predictions['expected_price']:.2f}")
        summary.append(f"Expected Return: {predictions['expected_return']*100:.2f}%")
        summary.append(f"\n95% Confidence Interval: ${predictions['confidence_95_lower']:.2f} - ${predictions['confidence_95_upper']:.2f}")
        summary.append(f"68% Confidence Interval: ${predictions['confidence_68_lower']:.2f} - ${predictions['confidence_68_upper']:.2f}")
        summary.append(f"\nProbability of Increase: {predictions['probability_up']*100:.1f}%")
        summary.append(f"Probability of Decrease: {predictions['probability_down']*100:.1f}%")
        
        # Get recommendation
        rec = self.get_recommendation(predictions)
        summary.append(f"\n{'='*60}")
        summary.append(f"RECOMMENDATION: {rec['signal']} (Confidence: {rec['confidence']})")
        summary.append(f"{'='*60}")
        summary.append(f"\n{rec['reasoning']}")
        
        # Risk metrics
        risk = self.calculate_var_cvar(predictions)
        summary.append(f"\n{'='*60}")
        summary.append("RISK METRICS")
        summary.append(f"{'='*60}")
        summary.append(f"Value at Risk (95%): ${risk['var_loss']:.2f} ({risk['var_return']*100:.2f}%)")
        summary.append(f"Conditional VaR: ${risk['cvar_loss']:.2f} ({risk['cvar_return']*100:.2f}%)")
        summary.append(f"Max Potential Loss: ${risk['max_potential_loss']:.2f}")
        
        return "\n".join(summary)
