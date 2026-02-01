"""
State Discretizer Module
Converts continuous stock prices into discrete states for Markov chain modeling
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from scipy import stats


class StateDiscretizer:
    """Discretizes continuous stock data into states for Markov modeling"""
    
    def __init__(self, n_states=5, method='returns'):
        """
        Initialize the state discretizer
        
        Args:
            n_states (int): Number of discrete states to create
            method (str): Discretization method ('returns', 'price', 'volatility', 'kmeans', 'hybrid')
        """
        self.n_states = n_states
        self.method = method
        self.state_labels = None
        self.state_boundaries = None
        self.state_means = None
        
    def discretize_by_returns(self, data):
        """
        Discretize based on return percentiles
        States represent: Strong Down, Down, Neutral, Up, Strong Up
        """
        returns = data['Returns'].values
        
        # Create state boundaries based on percentiles
        percentiles = np.linspace(0, 100, self.n_states + 1)
        self.state_boundaries = np.percentile(returns, percentiles)
        
        # Assign states
        states = np.digitize(returns, self.state_boundaries[1:-1])
        
        # Create state labels
        if self.n_states == 3:
            self.state_labels = {0: 'Down', 1: 'Neutral', 2: 'Up'}
        elif self.n_states == 5:
            self.state_labels = {0: 'Strong Down', 1: 'Down', 2: 'Neutral', 3: 'Up', 4: 'Strong Up'}
        else:
            self.state_labels = {i: f'State_{i}' for i in range(self.n_states)}
        
        return states
    
    def discretize_by_price_change(self, data):
        """Discretize based on absolute price changes"""
        price_changes = data['Price_Change'].values
        
        # Use standard deviation to define boundaries
        std = np.std(price_changes)
        mean = np.mean(price_changes)
        
        if self.n_states == 3:
            boundaries = [mean - std, mean + std]
        elif self.n_states == 5:
            boundaries = [mean - 2*std, mean - 0.5*std, mean + 0.5*std, mean + 2*std]
        else:
            # Create evenly spaced boundaries
            boundaries = np.linspace(price_changes.min(), price_changes.max(), self.n_states + 1)[1:-1]
        
        self.state_boundaries = np.array(boundaries)
        states = np.digitize(price_changes, boundaries)
        
        self.state_labels = {i: f'Price_State_{i}' for i in range(self.n_states)}
        
        return states
    
    def discretize_by_volatility(self, data):
        """
        Discretize based on volatility regimes
        Combines returns with volatility information
        """
        returns = data['Returns'].values
        volatility = data['Volatility'].values
        
        # Normalize both features
        returns_norm = (returns - np.mean(returns)) / np.std(returns)
        vol_norm = (volatility - np.mean(volatility)) / np.std(volatility)
        
        # Create composite score
        composite = returns_norm + 0.5 * vol_norm  # Weight volatility less
        
        # Create boundaries
        self.state_boundaries = np.percentile(composite, np.linspace(0, 100, self.n_states + 1))
        states = np.digitize(composite, self.state_boundaries[1:-1])
        
        if self.n_states == 5:
            self.state_labels = {
                0: 'High Vol Down',
                1: 'Low Vol Down', 
                2: 'Low Vol Neutral',
                3: 'Low Vol Up',
                4: 'High Vol Up'
            }
        else:
            self.state_labels = {i: f'Vol_State_{i}' for i in range(self.n_states)}
        
        return states
    
    def discretize_by_kmeans(self, data):
        """
        Use K-Means clustering for multi-feature state definition
        More sophisticated approach using multiple features
        """
        # Select features for clustering
        features = []
        feature_names = []
        
        if 'Returns' in data.columns:
            features.append(data['Returns'].values.reshape(-1, 1))
            feature_names.append('Returns')
        
        if 'Volatility' in data.columns:
            features.append(data['Volatility'].values.reshape(-1, 1))
            feature_names.append('Volatility')
        
        if 'RSI' in data.columns:
            # Normalize RSI to 0-1 range
            rsi_norm = (data['RSI'].values - 50) / 50
            features.append(rsi_norm.reshape(-1, 1))
            feature_names.append('RSI')
        
        if 'Volume_Ratio' in data.columns:
            vol_ratio_norm = np.log(data['Volume_Ratio'].values).reshape(-1, 1)
            features.append(vol_ratio_norm)
            feature_names.append('Volume_Ratio')
        
        # Combine features
        X = np.hstack(features)
        
        # Remove any NaN or inf values
        valid_indices = ~(np.isnan(X).any(axis=1) | np.isinf(X).any(axis=1))
        X_clean = X[valid_indices]
        
        # Standardize features
        X_std = (X_clean - np.mean(X_clean, axis=0)) / np.std(X_clean, axis=0)
        
        # Apply K-Means
        kmeans = KMeans(n_clusters=self.n_states, random_state=42, n_init=10)
        states_clean = kmeans.fit_predict(X_std)
        
        # Store cluster centers
        self.state_means = kmeans.cluster_centers_
        
        # Map back to full array
        states = np.full(len(data), -1)
        states[valid_indices] = states_clean
        
        # Create descriptive labels based on cluster centers
        self._create_kmeans_labels(feature_names)
        
        return states
    
    def _create_kmeans_labels(self, feature_names):
        """Create descriptive labels for K-Means clusters"""
        if self.state_means is None:
            self.state_labels = {i: f'Cluster_{i}' for i in range(self.n_states)}
            return
        
        # Analyze cluster centers to create meaningful labels
        returns_idx = 0 if 'Returns' in feature_names else None
        
        labels = {}
        for i in range(self.n_states):
            center = self.state_means[i]
            
            if returns_idx is not None:
                return_val = center[returns_idx]
                if return_val < -0.5:
                    label = f'Cluster_{i}_StrongDown'
                elif return_val < -0.1:
                    label = f'Cluster_{i}_Down'
                elif return_val < 0.1:
                    label = f'Cluster_{i}_Neutral'
                elif return_val < 0.5:
                    label = f'Cluster_{i}_Up'
                else:
                    label = f'Cluster_{i}_StrongUp'
            else:
                label = f'Cluster_{i}'
            
            labels[i] = label
        
        self.state_labels = labels
    
    def discretize_hybrid(self, data):
        """
        Hybrid approach combining returns, volatility, and trend
        Most sophisticated method
        """
        returns = data['Returns'].values
        volatility = data['Volatility'].values
        
        # Get trend information if available
        if 'Trend' in data.columns:
            trend = data['Trend'].values
        else:
            trend = np.zeros_like(returns)
        
        # Create state matrix
        states = np.zeros(len(returns), dtype=int)
        
        # Calculate thresholds
        ret_low = np.percentile(returns, 33)
        ret_high = np.percentile(returns, 67)
        vol_low = np.percentile(volatility, 50)
        
        for i in range(len(returns)):
            r = returns[i]
            v = volatility[i]
            t = trend[i] if i < len(trend) else 0
            
            # State assignment logic
            if v < vol_low:  # Low volatility
                if r < ret_low:
                    states[i] = 0  # Low vol down
                elif r > ret_high:
                    states[i] = 4  # Low vol up
                else:
                    states[i] = 2  # Low vol neutral
            else:  # High volatility
                if r < ret_low:
                    states[i] = 1  # High vol down
                elif r > ret_high:
                    states[i] = 3  # High vol up
                else:
                    states[i] = 2  # High vol neutral
        
        self.state_labels = {
            0: 'Calm Decline',
            1: 'Volatile Decline',
            2: 'Neutral',
            3: 'Volatile Rise',
            4: 'Calm Rise'
        }
        
        return states
    
    def fit_transform(self, data):
        """
        Fit the discretizer and transform the data
        
        Args:
            data (pd.DataFrame): Preprocessed stock data
            
        Returns:
            np.array: Array of state assignments
        """
        if self.method == 'returns':
            states = self.discretize_by_returns(data)
        elif self.method == 'price':
            states = self.discretize_by_price_change(data)
        elif self.method == 'volatility':
            states = self.discretize_by_volatility(data)
        elif self.method == 'kmeans':
            states = self.discretize_by_kmeans(data)
        elif self.method == 'hybrid':
            states = self.discretize_hybrid(data)
        else:
            raise ValueError(f"Unknown discretization method: {self.method}")
        
        return states
    
    def get_state_statistics(self, data, states):
        """Calculate statistics for each state"""
        stats = {}
        
        for state in range(self.n_states):
            state_mask = states == state
            state_data = data[state_mask]
            
            if len(state_data) > 0:
                stats[state] = {
                    'label': self.state_labels.get(state, f'State_{state}'),
                    'count': len(state_data),
                    'frequency': len(state_data) / len(data),
                    'avg_return': state_data['Returns'].mean() if 'Returns' in state_data.columns else None,
                    'avg_volatility': state_data['Volatility'].mean() if 'Volatility' in state_data.columns else None,
                    'avg_price': state_data['Close'].mean() if 'Close' in state_data.columns else None
                }
            else:
                stats[state] = {
                    'label': self.state_labels.get(state, f'State_{state}'),
                    'count': 0,
                    'frequency': 0
                }
        
        return stats
    
    def describe_states(self):
        """Return description of states"""
        if self.state_labels is None:
            return "No states defined yet. Call fit_transform() first."
        
        description = f"State Discretization Method: {self.method}\n"
        description += f"Number of States: {self.n_states}\n\n"
        description += "State Labels:\n"
        for state, label in self.state_labels.items():
            description += f"  State {state}: {label}\n"
        
        return description
