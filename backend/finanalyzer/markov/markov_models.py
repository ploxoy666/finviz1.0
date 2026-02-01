"""
Markov Models Module
Implements various Markov chain models including HMM for stock prediction
"""

import numpy as np
import pandas as pd
from hmmlearn import hmm
from collections import defaultdict


class MarkovChain:
    """Standard Markov Chain implementation"""
    
    def __init__(self, order=1):
        """
        Initialize Markov Chain
        
        Args:
            order (int): Order of the Markov chain (1=first-order, 2=second-order, etc.)
        """
        self.order = order
        self.transition_matrix = None
        self.state_space = None
        self.n_states = 0
        
    def fit(self, states, n_states=None):
        """
        Fit the Markov chain to state sequence
        
        Args:
            states (np.array): Array of state observations
            n_states (int, optional): Total number of states (if known)
        """
        if n_states is not None:
             self.n_states = n_states
             self.state_space = np.arange(n_states)
        else:
             self.state_space = np.unique(states)
             # Fix: Use max value + 1 to ensure matrix covers all potential indices 
             # even if some intermediate states are missing in the sample
             if np.issubdtype(states.dtype, np.integer):
                 self.n_states = int(np.max(states) + 1)
             else:
                 self.n_states = len(self.state_space)
        
        # Initialize transition matrix
        if self.order == 1:
            self.transition_matrix = np.zeros((self.n_states, self.n_states))
            
            # Count transitions
            for i in range(len(states) - 1):
                current_state = states[i]
                next_state = states[i + 1]
                self.transition_matrix[current_state, next_state] += 1
            
            # Normalize to get probabilities
            row_sums = self.transition_matrix.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1  # Avoid division by zero
            self.transition_matrix = self.transition_matrix / row_sums
            
        elif self.order == 2:
            # For second-order, we need to track pairs of states
            self._fit_second_order(states)
        elif self.order == 3:
            # For third-order, track triplets of states
            self._fit_third_order(states)
        else:
            # For higher orders, use a general approach
            self._fit_higher_order(states)
    
    def _fit_second_order(self, states):
        """Fit second-order Markov chain"""
        # Create state pairs
        state_pairs = {}
        transition_counts = defaultdict(lambda: defaultdict(int))
        
        for i in range(len(states) - 2):
            pair = (states[i], states[i+1])
            next_state = states[i+2]
            transition_counts[pair][next_state] += 1
        
        # Store as dictionary for easier lookup
        self.transition_matrix = {}
        for pair, next_states in transition_counts.items():
            total = sum(next_states.values())
            self.transition_matrix[pair] = {
                state: count / total 
                for state, count in next_states.items()
            }
    
    def _fit_third_order(self, states):
        """Fit third-order Markov chain"""
        # Create state triplets
        transition_counts = defaultdict(lambda: defaultdict(int))
        
        for i in range(len(states) - 3):
            triplet = (states[i], states[i+1], states[i+2])
            next_state = states[i+3]
            transition_counts[triplet][next_state] += 1
        
        # Store as dictionary for easier lookup
        self.transition_matrix = {}
        for triplet, next_states in transition_counts.items():
            total = sum(next_states.values())
            self.transition_matrix[triplet] = {
                state: count / total 
                for state, count in next_states.items()
            }
    
    def _fit_higher_order(self, states):
        """Fit higher-order Markov chain (order > 3)"""
        transition_counts = defaultdict(lambda: defaultdict(int))
        
        for i in range(len(states) - self.order):
            # Create tuple of previous states
            history = tuple(states[i:i+self.order])
            next_state = states[i+self.order]
            transition_counts[history][next_state] += 1
        
        # Convert to probabilities
        self.transition_matrix = {}
        for history, next_states in transition_counts.items():
            total = sum(next_states.values())
            self.transition_matrix[history] = {
                state: count / total 
                for state, count in next_states.items()
            }
    
    def predict_next_state(self, current_history):
        """
        Predict next state given current history
        
        Args:
            current_history: Current state (for order=1) or tuple of states (for higher orders)
            
        Returns:
            int: Predicted next state
        """
        if self.order == 1:
            # Get transition probabilities for current state
            probs = self.transition_matrix[current_history]
            # Return state with highest probability
            return np.argmax(probs)
        else:
            # For higher orders, look up the history tuple
            if isinstance(current_history, (list, np.ndarray)):
                current_history = tuple(current_history[-self.order:])
            
            if current_history in self.transition_matrix:
                next_state_probs = self.transition_matrix[current_history]
                return max(next_state_probs, key=next_state_probs.get)
            else:
                # If history not seen, return most common state
                return np.random.choice(self.state_space)
    
    def predict_next_state_distribution(self, current_history):
        """
        Get probability distribution for next state
        
        Args:
            current_history: Current state or history
            
        Returns:
            dict: Dictionary mapping states to probabilities
        """
        if self.order == 1:
            probs = self.transition_matrix[current_history]
            return {state: probs[state] for state in range(self.n_states)}
        else:
            if isinstance(current_history, (list, np.ndarray)):
                current_history = tuple(current_history[-self.order:])
            
            if current_history in self.transition_matrix:
                return self.transition_matrix[current_history]
            else:
                # Return uniform distribution if history not seen
                return {state: 1.0 / self.n_states for state in self.state_space}
    
    def simulate(self, start_state, n_steps=10):
        """
        Simulate future states
        
        Args:
            start_state: Starting state or history
            n_steps (int): Number of steps to simulate
            
        Returns:
            list: Simulated state sequence
        """
        if self.order == 1:
            states = [start_state]
            current = start_state
            
            for _ in range(n_steps):
                probs = self.transition_matrix[current]
                next_state = np.random.choice(self.n_states, p=probs)
                states.append(next_state)
                current = next_state
            
            return states
        else:
            # For higher orders
            if isinstance(start_state, int):
                history = [start_state] * self.order
            else:
                history = list(start_state[-self.order:])
            
            states = history.copy()
            
            for _ in range(n_steps):
                history_tuple = tuple(history[-self.order:])
                
                if history_tuple in self.transition_matrix:
                    next_state_probs = self.transition_matrix[history_tuple]
                    next_states = list(next_state_probs.keys())
                    probs = list(next_state_probs.values())
                    next_state = np.random.choice(next_states, p=probs)
                else:
                    next_state = np.random.choice(self.state_space)
                
                states.append(next_state)
                history.append(next_state)
            
            return states
    
    def get_stationary_distribution(self):
        """Calculate stationary distribution (for first-order chains)"""
        if self.order != 1:
            raise ValueError("Stationary distribution only available for first-order chains")
        
        # Find eigenvector corresponding to eigenvalue 1
        eigenvalues, eigenvectors = np.linalg.eig(self.transition_matrix.T)
        
        # Find index of eigenvalue closest to 1
        idx = np.argmin(np.abs(eigenvalues - 1.0))
        stationary = np.real(eigenvectors[:, idx])
        stationary = stationary / stationary.sum()
        
        return stationary


class HiddenMarkovModel:
    """Hidden Markov Model for stock prediction"""
    
    def __init__(self, n_states=5, n_iterations=100):
        """
        Initialize Hidden Markov Model
        
        Args:
            n_states (int): Number of hidden states
            n_iterations (int): Number of EM iterations for training
        """
        self.n_states = n_states
        self.n_iterations = n_iterations
        self.model = None
        self.is_fitted = False
        
    def fit(self, observations):
        """
        Fit HMM to observations using Gaussian emissions
        
        Args:
            observations (np.array): 2D array of observations (n_samples, n_features)
        """
        # Reshape if necessary
        if observations.ndim == 1:
            observations = observations.reshape(-1, 1)
        
        # Initialize Gaussian HMM
        self.model = hmm.GaussianHMM(
            n_components=self.n_states,
            covariance_type="full",
            n_iter=self.n_iterations,
            random_state=42
        )
        
        # Fit the model
        self.model.fit(observations)
        self.is_fitted = True
        
        print(f"HMM trained with {self.n_states} hidden states")
        print(f"Converged: {self.model.monitor_.converged}")
    
    def predict_hidden_states(self, observations):
        """
        Predict most likely sequence of hidden states
        
        Args:
            observations (np.array): Observations
            
        Returns:
            np.array: Predicted hidden states
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        
        if observations.ndim == 1:
            observations = observations.reshape(-1, 1)
        
        return self.model.predict(observations)
    
    def predict_next_observation(self, observations, n_steps=1):
        """
        Predict future observations
        
        Args:
            observations (np.array): Historical observations
            n_steps (int): Number of steps ahead to predict
            
        Returns:
            np.array: Predicted observations
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        
        if observations.ndim == 1:
            observations = observations.reshape(-1, 1)
        
        # Get current hidden state
        current_state = self.model.predict(observations)[-1]
        
        predictions = []
        for _ in range(n_steps):
            # Get transition probabilities from current state
            trans_probs = self.model.transmat_[current_state]
            
            # Sample next state
            next_state = np.random.choice(self.n_states, p=trans_probs)
            
            # Sample observation from next state's emission distribution
            mean = self.model.means_[next_state]
            cov = self.model.covars_[next_state]
            next_obs = np.random.multivariate_normal(mean, cov)
            
            predictions.append(next_obs)
            current_state = next_state
        
        return np.array(predictions)
    
    def score(self, observations):
        """
        Compute log-likelihood of observations under the model
        
        Args:
            observations (np.array): Observations
            
        Returns:
            float: Log-likelihood score
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        
        if observations.ndim == 1:
            observations = observations.reshape(-1, 1)
        
        return self.model.score(observations)
    
    def sample(self, n_samples=100):
        """
        Generate samples from the model
        
        Args:
            n_samples (int): Number of samples to generate
            
        Returns:
            tuple: (samples, hidden_states)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        
        return self.model.sample(n_samples)
    
    def get_transition_matrix(self):
        """Get the learned transition matrix"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        return self.model.transmat_
    
    def get_means_and_covariances(self):
        """Get emission distribution parameters"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        return self.model.means_, self.model.covars_


class EnsembleMarkovModel:
    """Ensemble of multiple Markov models for robust predictions with weighted averaging"""
    
    def __init__(self, models=None, weights=None):
        """
        Initialize ensemble
        
        Args:
            models (list): List of fitted Markov models
            weights (list): Weights for each model (default: equal weights)
        """
        self.models = models if models is not None else []
        self.weights = weights
        
        # If no weights provided, use equal weights
        if self.weights is None and len(self.models) > 0:
            self.weights = [1.0 / len(self.models)] * len(self.models)
        
        # Normalize weights to sum to 1
        if self.weights is not None:
            weight_sum = sum(self.weights)
            self.weights = [w / weight_sum for w in self.weights]
    
    def add_model(self, model, weight=None):
        """
        Add a model to the ensemble
        
        Args:
            model: Markov model to add
            weight (float): Weight for this model (optional)
        """
        self.models.append(model)
        
        if weight is not None:
            if self.weights is None:
                self.weights = [weight]
            else:
                self.weights.append(weight)
            # Renormalize weights
            weight_sum = sum(self.weights)
            self.weights = [w / weight_sum for w in self.weights]
        else:
            # Recalculate equal weights
            self.weights = [1.0 / len(self.models)] * len(self.models)
    
    def predict_next_state(self, current_history):
        """
        Predict next state using ensemble voting
        
        Args:
            current_history: Current state or history
            
        Returns:
            int: Predicted next state
        """
        predictions = []
        for model in self.models:
            pred = model.predict_next_state(current_history)
            predictions.append(pred)
        
        # Return most common prediction
        return max(set(predictions), key=predictions.count)
    
    def predict_distribution(self, current_history):
        """
        Get weighted ensemble probability distribution
        
        Args:
            current_history: Current state or history
            
        Returns:
            dict: Weighted averaged probability distribution
        """
        distributions = []
        for model in self.models:
            dist = model.predict_next_state_distribution(current_history)
            distributions.append(dist)
        
        # Weighted average of distributions
        avg_dist = defaultdict(float)
        
        for i, dist in enumerate(distributions):
            weight = self.weights[i] if (self.weights is not None and len(self.weights) > 0) else 1.0 / len(distributions)
            for state, prob in dist.items():
                avg_dist[state] += prob * weight
        
        return dict(avg_dist)
    
    def simulate_ensemble(self, start_state, n_steps=10, n_simulations=100):
        """
        Run multiple weighted simulations with different models
        
        Args:
            start_state: Starting state
            n_steps (int): Steps to simulate
            n_simulations (int): Number of simulations per model
            
        Returns:
            list: All simulation results
        """
        all_simulations = []
        
        for i, model in enumerate(self.models):
            # Weight determines how many simulations from this model
            weight = self.weights[i] if self.weights else 1.0 / len(self.models)
            n_sims_for_model = max(1, int(n_simulations * weight))
            
            for _ in range(n_sims_for_model):
                sim = model.simulate(start_state, n_steps)
                all_simulations.append(sim)
        
        return all_simulations
    
    def set_weights(self, weights):
        """
        Set custom weights for the ensemble
        
        Args:
            weights (list): List of weights (will be normalized)
        """
        if len(weights) != len(self.models):
            raise ValueError(f"Number of weights ({len(weights)}) must match number of models ({len(self.models)})")
        
        # Normalize weights
        weight_sum = sum(weights)
        self.weights = [w / weight_sum for w in weights]
    
    def optimize_weights_backtest(self, data, states, metric='accuracy'):
        """
        Optimize ensemble weights based on backtest performance
        
        Args:
            data (pd.DataFrame): Historical data
            states (np.array): State sequence
            metric (str): Metric to optimize ('accuracy', 'sharpe', 'return')
            
        Returns:
            list: Optimized weights
        """
        from scipy.optimize import minimize
        
        def objective(weights):
            # Set temporary weights
            old_weights = self.weights
            self.weights = weights / sum(weights)
            
            # Calculate backtest performance
            correct = 0
            total = 0
            
            for i in range(len(states) - 10, len(states) - 1):
                current_history = tuple(states[max(0, i-2):i+1])
                pred_dist = self.predict_distribution(current_history[-1] if len(current_history) == 1 else current_history)
                pred_state = max(pred_dist, key=pred_dist.get)
                actual_state = states[i+1]
                
                if pred_state == actual_state:
                    correct += 1
                total += 1
            
            # Restore old weights
            self.weights = old_weights
            
            # Return negative accuracy (minimize)
            return -correct / total if total > 0 else 0
        
        # Initial guess: equal weights
        x0 = np.ones(len(self.models))
        
        # Constraints: weights sum to 1, all positive
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = [(0.01, 0.99) for _ in range(len(self.models))]
        
        # Optimize
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            self.weights = list(result.x / sum(result.x))
            print(f"Optimized weights: {[f'{w:.3f}' for w in self.weights]}")
        
        return self.weights
