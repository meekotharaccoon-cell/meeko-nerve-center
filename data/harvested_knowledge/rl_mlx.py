#!/usr/bin/env python3
"""
MLX-based PPO (Proximal Policy Optimization) strategy.

Uses Apple's MLX framework for proper automatic differentiation
instead of manual NumPy backprop.

Key optimizations for 15-min binary markets:
- Temporal processing: captures momentum by attending to last N states
- Asymmetric architecture: larger critic (96) for better value estimation
- Lower gamma (0.95): appropriate for short-horizon trading
- Smaller buffer (256): faster adaptation to regime changes
"""
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np
from collections import deque
from typing import List, Dict, Optional
from dataclasses import dataclass
from .base import Strategy, MarketState, Action


@dataclass
class Experience:
    """Single experience tuple with temporal context."""
    state: np.ndarray  # Current state features (18,)
    temporal_state: np.ndarray  # Stacked temporal features (history_len * 18,)
    action: int
    reward: float
    next_state: np.ndarray
    next_temporal_state: np.ndarray
    done: bool
    log_prob: float
    value: float


class TemporalEncoder(nn.Module):
    """Encodes temporal sequence of states into momentum/trend features.

    Takes last N states and compresses them into a fixed-size representation
    that captures velocity, acceleration, and trend direction.

    Architecture: (history_len * 18) → 64 → LayerNorm → tanh → 32
    Output is concatenated with current state features.
    """

    def __init__(self, input_dim: int = 18, history_len: int = 5, output_dim: int = 32):
        super().__init__()
        self.history_len = history_len
        self.temporal_input = input_dim * history_len
        self.fc1 = nn.Linear(self.temporal_input, 64)
        self.ln1 = nn.LayerNorm(64)
        self.fc2 = nn.Linear(64, output_dim)
        self.ln2 = nn.LayerNorm(output_dim)

    def __call__(self, x: mx.array) -> mx.array:
        """Forward pass. x is (batch, history_len * input_dim)."""
        h = mx.tanh(self.ln1(self.fc1(x)))
        h = mx.tanh(self.ln2(self.fc2(h)))
        return h


class Actor(nn.Module):
    """Policy network with temporal awareness.

    Architecture:
        Current state (18) + Temporal features (32) = 50
        → 64 → LayerNorm → tanh → 64 → LayerNorm → tanh → 3 (softmax)

    Temporal encoder captures momentum/trends from state history.
    Smaller network (64) to prevent overfitting on enhanced features.
    """

    def __init__(self, input_dim: int = 18, hidden_size: int = 64, output_dim: int = 3,
                 history_len: int = 5, temporal_dim: int = 32):
        super().__init__()
        self.temporal_encoder = TemporalEncoder(input_dim, history_len, temporal_dim)

        # Combined input: current state + temporal features
        combined_dim = input_dim + temporal_dim
        self.fc1 = nn.Linear(combined_dim, hidden_size)
        self.ln1 = nn.LayerNorm(hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.ln2 = nn.LayerNorm(hidden_size)
        self.fc3 = nn.Linear(hidden_size, output_dim)

    def __call__(self, current_state: mx.array, temporal_state: mx.array) -> mx.array:
        """Forward pass. Returns action probabilities.

        Args:
            current_state: (batch, 18) current features
            temporal_state: (batch, history_len * 18) stacked history
        """
        # Encode temporal context
        temporal_features = self.temporal_encoder(temporal_state)

        # Combine current + temporal
        combined = mx.concatenate([current_state, temporal_features], axis=-1)

        h = mx.tanh(self.ln1(self.fc1(combined)))
        h = mx.tanh(self.ln2(self.fc2(h)))
        logits = self.fc3(h)
        probs = mx.softmax(logits, axis=-1)
        return probs


class Critic(nn.Module):
    """Value network with temporal awareness - ASYMMETRIC (larger than actor).

    Architecture:
        Current state (18) + Temporal features (32) = 50
        → 96 → LayerNorm → tanh → 96 → LayerNorm → tanh → 1

    Larger network (96 vs 64) because:
    - Value estimation is harder than policy
    - Critic doesn't overfit as easily (regresses to scalar)
    - Better value estimates improve advantage computation
    """

    def __init__(self, input_dim: int = 18, hidden_size: int = 96,
                 history_len: int = 5, temporal_dim: int = 32):
        super().__init__()
        self.temporal_encoder = TemporalEncoder(input_dim, history_len, temporal_dim)

        # Combined input: current state + temporal features
        combined_dim = input_dim + temporal_dim
        self.fc1 = nn.Linear(combined_dim, hidden_size)
        self.ln1 = nn.LayerNorm(hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.ln2 = nn.LayerNorm(hidden_size)
        self.fc3 = nn.Linear(hidden_size, 1)

    def __call__(self, current_state: mx.array, temporal_state: mx.array) -> mx.array:
        """Forward pass. Returns value estimate.

        Args:
            current_state: (batch, 18) current features
            temporal_state: (batch, history_len * 18) stacked history
        """
        # Encode temporal context
        temporal_features = self.temporal_encoder(temporal_state)

        # Combine current + temporal
        combined = mx.concatenate([current_state, temporal_features], axis=-1)

        h = mx.tanh(self.ln1(self.fc1(combined)))
        h = mx.tanh(self.ln2(self.fc2(h)))
        value = self.fc3(h)
        return value


class RLStrategy(Strategy):
    """PPO-based strategy with temporal-aware actor-critic architecture using MLX.

    Key features:
    - Temporal processing: maintains history of last N states to capture momentum
    - Asymmetric architecture: larger critic (96) for better value estimation
    - Lower gamma (0.95): appropriate for 15-min trading horizon
    - Smaller buffer (256): faster adaptation to regime changes
    """

    def __init__(
        self,
        input_dim: int = 18,
        hidden_size: int = 64,  # Actor hidden size
        critic_hidden_size: int = 96,  # Larger critic for better value estimation
        history_len: int = 5,  # Number of past states for temporal processing
        temporal_dim: int = 32,  # Temporal encoder output size
        lr_actor: float = 1e-4,
        lr_critic: float = 3e-4,
        gamma: float = 0.95,  # Lower gamma for 15-min horizon (was 0.99)
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        entropy_coef: float = 0.03,  # Lower entropy to allow sparse policy (mostly HOLD)
        value_coef: float = 0.5,
        max_grad_norm: float = 0.5,
        buffer_size: int = 256,  # Smaller buffer for faster adaptation (was 512)
        batch_size: int = 64,
        n_epochs: int = 10,
        target_kl: float = 0.02,
    ):
        super().__init__("rl")
        self.input_dim = input_dim
        self.hidden_size = hidden_size
        self.critic_hidden_size = critic_hidden_size
        self.history_len = history_len
        self.temporal_dim = temporal_dim
        self.output_dim = 3  # BUY, HOLD, SELL (simplified)

        # Hyperparameters
        self.lr_actor = lr_actor
        self.lr_critic = lr_critic
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.max_grad_norm = max_grad_norm
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.n_epochs = n_epochs
        self.target_kl = target_kl

        # Networks with temporal processing
        self.actor = Actor(input_dim, hidden_size, self.output_dim, history_len, temporal_dim)
        self.critic = Critic(input_dim, critic_hidden_size, history_len, temporal_dim)

        # Optimizers
        self.actor_optimizer = optim.Adam(learning_rate=lr_actor)
        self.critic_optimizer = optim.Adam(learning_rate=lr_critic)

        # Experience buffer
        self.experiences: List[Experience] = []

        # Temporal state history (per-market, keyed by asset)
        self._state_history: Dict[str, deque] = {}

        # Running stats for reward normalization
        self.reward_mean = 0.0
        self.reward_std = 1.0
        self.reward_count = 0

        # For storing last action's log prob and value
        self._last_log_prob = 0.0
        self._last_value = 0.0
        self._last_temporal_state: Optional[np.ndarray] = None

        # Eval networks on init
        mx.eval(self.actor.parameters(), self.critic.parameters())

    def _get_temporal_state(self, asset: str, current_features: np.ndarray) -> np.ndarray:
        """Get stacked temporal state for an asset.

        Maintains a history of the last N states per asset.
        Returns flattened array of shape (history_len * input_dim,).
        """
        if asset not in self._state_history:
            self._state_history[asset] = deque(maxlen=self.history_len)

        history = self._state_history[asset]

        # Add current state to history
        history.append(current_features.copy())

        # Pad with zeros if not enough history
        if len(history) < self.history_len:
            padding = [np.zeros(self.input_dim, dtype=np.float32)] * (self.history_len - len(history))
            stacked = np.concatenate(padding + list(history))
        else:
            stacked = np.concatenate(list(history))

        return stacked.astype(np.float32)

    def act(self, state: MarketState) -> Action:
        """Select action using current policy with temporal context."""
        features = state.to_features()

        # Get temporal state (stacked history)
        temporal_state = self._get_temporal_state(state.asset, features)

        # Convert to MLX arrays
        features_mx = mx.array(features.reshape(1, -1))
        temporal_mx = mx.array(temporal_state.reshape(1, -1))

        # Get action probabilities and value with temporal context
        probs = self.actor(features_mx, temporal_mx)
        value = self.critic(features_mx, temporal_mx)

        # Eval to get values
        mx.eval(probs, value)

        probs_np = np.array(probs[0])
        value_np = float(np.array(value[0, 0]))

        if self.training:
            # Sample from distribution
            action_idx = np.random.choice(self.output_dim, p=probs_np)
        else:
            # Greedy
            action_idx = int(np.argmax(probs_np))

        # Store for experience collection
        self._last_log_prob = float(np.log(probs_np[action_idx] + 1e-8))
        self._last_value = value_np
        self._last_temporal_state = temporal_state

        return Action(action_idx)

    def store(self, state: MarketState, action: Action, reward: float,
              next_state: MarketState, done: bool):
        """Store experience for training with temporal context."""
        # Update running reward stats for normalization
        self.reward_count += 1
        delta = reward - self.reward_mean
        self.reward_mean += delta / self.reward_count
        self.reward_std = np.sqrt(
            ((self.reward_count - 1) * self.reward_std**2 + delta * (reward - self.reward_mean))
            / max(1, self.reward_count)
        )

        # Normalize reward
        norm_reward = (reward - self.reward_mean) / (self.reward_std + 1e-8)

        # Get next temporal state (updates history with next_state)
        next_features = next_state.to_features()
        next_temporal_state = self._get_temporal_state(next_state.asset, next_features)

        exp = Experience(
            state=state.to_features(),
            temporal_state=self._last_temporal_state if self._last_temporal_state is not None else np.zeros(self.history_len * self.input_dim, dtype=np.float32),
            action=action.value,
            reward=norm_reward,
            next_state=next_features,
            next_temporal_state=next_temporal_state,
            done=done,
            log_prob=self._last_log_prob,
            value=self._last_value,
        )
        self.experiences.append(exp)

        # Limit buffer size
        if len(self.experiences) > self.buffer_size:
            self.experiences = self.experiences[-self.buffer_size:]

    def _compute_gae(self, rewards: np.ndarray, values: np.ndarray,
                     dones: np.ndarray, next_value: float) -> tuple:
        """Compute Generalized Advantage Estimation."""
        n = len(rewards)
        advantages = np.zeros(n)
        returns = np.zeros(n)

        gae = 0
        for t in reversed(range(n)):
            if t == n - 1:
                next_val = next_value
            else:
                next_val = values[t + 1]

            # TD error
            delta = rewards[t] + self.gamma * next_val * (1 - dones[t]) - values[t]

            # GAE
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages[t] = gae
            returns[t] = advantages[t] + values[t]

        return advantages, returns

    def _clip_grad_norm(self, grads: dict, max_norm: float) -> dict:
        """Clip gradients by global norm (handles arbitrarily nested dicts)."""

        def compute_norm_sq(g):
            """Recursively compute sum of squared gradients."""
            if isinstance(g, dict):
                return sum(compute_norm_sq(v) for v in g.values())
            else:
                return float(mx.sum(g ** 2))

        def scale_grad(g, coef):
            """Recursively scale gradients."""
            if isinstance(g, dict):
                return {k: scale_grad(v, coef) for k, v in g.items()}
            return g * coef

        # Compute global norm
        total_norm_sq = compute_norm_sq(grads)
        total_norm = np.sqrt(total_norm_sq)
        clip_coef = max_norm / (total_norm + 1e-6)

        if clip_coef < 1.0:
            grads = scale_grad(grads, clip_coef)

        return grads

    def update(self) -> Optional[Dict[str, float]]:
        """Update policy using PPO with proper MLX autograd and temporal context."""
        if len(self.experiences) < self.buffer_size:
            return None

        # Convert experiences to arrays (including temporal states)
        states = np.array([e.state for e in self.experiences], dtype=np.float32)
        temporal_states = np.array([e.temporal_state for e in self.experiences], dtype=np.float32)
        actions = np.array([e.action for e in self.experiences], dtype=np.int32)
        rewards = np.array([e.reward for e in self.experiences], dtype=np.float32)
        dones = np.array([e.done for e in self.experiences], dtype=np.float32)
        old_log_probs = np.array([e.log_prob for e in self.experiences], dtype=np.float32)
        old_values = np.array([e.value for e in self.experiences], dtype=np.float32)

        # Compute next value for GAE (with temporal context)
        next_state_mx = mx.array(self.experiences[-1].next_state.reshape(1, -1))
        next_temporal_mx = mx.array(self.experiences[-1].next_temporal_state.reshape(1, -1))
        next_value = float(np.array(self.critic(next_state_mx, next_temporal_mx)[0, 0]))

        # Compute advantages and returns
        advantages, returns = self._compute_gae(rewards, old_values, dones, next_value)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # Convert to MLX arrays (including temporal states)
        states_mx = mx.array(states)
        temporal_states_mx = mx.array(temporal_states)
        actions_mx = mx.array(actions)
        old_log_probs_mx = mx.array(old_log_probs)
        advantages_mx = mx.array(advantages.astype(np.float32))
        returns_mx = mx.array(returns.astype(np.float32))
        old_values_mx = mx.array(old_values)

        n_samples = len(self.experiences)
        all_metrics = {
            "policy_loss": [],
            "value_loss": [],
            "entropy": [],
            "approx_kl": [],
            "clip_fraction": [],
        }

        # Multiple epochs over the data
        for epoch in range(self.n_epochs):
            # Shuffle indices
            indices = np.random.permutation(n_samples)

            epoch_kl = 0.0
            n_batches = 0

            for start in range(0, n_samples, self.batch_size):
                end = min(start + self.batch_size, n_samples)
                batch_idx = mx.array(indices[start:end].astype(np.int32))

                # Get batch using mx.take (MLX doesn't support numpy fancy indexing)
                batch_states = mx.take(states_mx, batch_idx, axis=0)
                batch_temporal = mx.take(temporal_states_mx, batch_idx, axis=0)
                batch_actions = mx.take(actions_mx, batch_idx, axis=0)
                batch_old_log_probs = mx.take(old_log_probs_mx, batch_idx, axis=0)
                batch_advantages = mx.take(advantages_mx, batch_idx, axis=0)
                batch_returns = mx.take(returns_mx, batch_idx, axis=0)
                batch_old_values = mx.take(old_values_mx, batch_idx, axis=0)

                # Define loss function for actor (takes model, not params)
                def actor_loss_fn(model):
                    probs = model(batch_states, batch_temporal)

                    # Get log probs for taken actions
                    batch_size_local = batch_actions.shape[0]
                    action_indices = mx.arange(batch_size_local)
                    selected_probs = probs[action_indices, batch_actions]
                    log_probs = mx.log(selected_probs + 1e-8)

                    # PPO clipped objective
                    ratio = mx.exp(log_probs - batch_old_log_probs)
                    surr1 = ratio * batch_advantages
                    surr2 = mx.clip(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                    policy_loss = -mx.mean(mx.minimum(surr1, surr2))

                    # Entropy bonus (encourages exploration)
                    entropy = -mx.sum(probs * mx.log(probs + 1e-8), axis=-1)
                    entropy_mean = mx.mean(entropy)
                    policy_loss = policy_loss - self.entropy_coef * entropy_mean

                    # Metrics
                    approx_kl = mx.mean(batch_old_log_probs - log_probs)
                    clip_frac = mx.mean(
                        ((ratio < 1 - self.clip_epsilon) | (ratio > 1 + self.clip_epsilon)).astype(mx.float32)
                    )

                    return policy_loss, (entropy_mean, approx_kl, clip_frac)

                # Define loss function for critic (takes model, not params)
                def critic_loss_fn(model):
                    values = model(batch_states, batch_temporal).squeeze()

                    # Value loss with clipping (PPO2 style)
                    values_clipped = batch_old_values + mx.clip(
                        values - batch_old_values, -self.clip_epsilon, self.clip_epsilon
                    )
                    value_loss1 = (batch_returns - values) ** 2
                    value_loss2 = (batch_returns - values_clipped) ** 2
                    value_loss = 0.5 * mx.mean(mx.maximum(value_loss1, value_loss2))

                    return value_loss

                # Compute actor gradients and update
                actor_loss_and_grad = nn.value_and_grad(self.actor, actor_loss_fn)
                (actor_loss, (entropy, approx_kl, clip_frac)), actor_grads = actor_loss_and_grad(self.actor)

                # Clip actor gradients
                actor_grads = self._clip_grad_norm(actor_grads, self.max_grad_norm)

                # Update actor
                self.actor_optimizer.update(self.actor, actor_grads)

                # Compute critic gradients and update
                critic_loss_and_grad = nn.value_and_grad(self.critic, critic_loss_fn)
                critic_loss, critic_grads = critic_loss_and_grad(self.critic)

                # Clip critic gradients
                critic_grads = self._clip_grad_norm(critic_grads, self.max_grad_norm)

                # Update critic
                self.critic_optimizer.update(self.critic, critic_grads)

                # Eval to commit updates (include optimizer state)
                mx.eval(
                    self.actor.parameters(),
                    self.critic.parameters(),
                    self.actor_optimizer.state,
                    self.critic_optimizer.state,
                )

                # Record metrics
                all_metrics["policy_loss"].append(float(np.array(actor_loss)))
                all_metrics["value_loss"].append(float(np.array(critic_loss)))
                all_metrics["entropy"].append(float(np.array(entropy)))
                all_metrics["approx_kl"].append(float(np.array(approx_kl)))
                all_metrics["clip_fraction"].append(float(np.array(clip_frac)))

                epoch_kl += float(np.array(approx_kl))
                n_batches += 1

            # Early stopping on KL divergence
            avg_kl = epoch_kl / max(1, n_batches)
            if avg_kl > self.target_kl:
                print(f"  [RL] Early stop epoch {epoch}, KL={avg_kl:.4f}")
                break

        # Clear buffer after update
        self.experiences.clear()

        # Compute explained variance
        y_pred = old_values
        y_true = returns
        var_y = np.var(y_true)
        explained_var = 1 - np.var(y_true - y_pred) / (var_y + 1e-8) if var_y > 0 else 0.0

        return {
            "policy_loss": np.mean(all_metrics["policy_loss"]),
            "value_loss": np.mean(all_metrics["value_loss"]),
            "entropy": np.mean(all_metrics["entropy"]),
            "approx_kl": np.mean(all_metrics["approx_kl"]),
            "clip_fraction": np.mean(all_metrics["clip_fraction"]),
            "explained_variance": explained_var,
        }

    def reset(self):
        """Clear experience buffer and state history."""
        self.experiences.clear()
        self._state_history.clear()
        self._last_temporal_state = None

    def save(self, path: str):
        """Save model and training state."""
        # Flatten params for saving
        def flatten_params(params, prefix=""):
            result = {}
            for key, val in params.items():
                full_key = f"{prefix}{key}" if prefix else key
                if isinstance(val, dict):
                    result.update(flatten_params(val, f"{full_key}."))
                else:
                    result[full_key] = val
            return result

        actor_flat = flatten_params(self.actor.parameters(), "actor.")
        critic_flat = flatten_params(self.critic.parameters(), "critic.")

        # Save weights using MLX safetensors
        weights = {**actor_flat, **critic_flat}
        weights_path = path.replace(".npz", "") + ".safetensors"
        mx.save_safetensors(weights_path, weights)

        # Save stats and architecture params separately
        stats_path = path.replace(".npz", "") + "_stats.npz"
        np.savez(
            stats_path,
            reward_mean=self.reward_mean,
            reward_std=self.reward_std,
            reward_count=self.reward_count,
            # Architecture params for reconstruction
            input_dim=self.input_dim,
            hidden_size=self.hidden_size,
            critic_hidden_size=self.critic_hidden_size,
            history_len=self.history_len,
            temporal_dim=self.temporal_dim,
            gamma=self.gamma,
            buffer_size=self.buffer_size,
        )

    def load(self, path: str):
        """Load model and training state."""
        # Load weights
        weights_path = path.replace(".npz", "") + ".safetensors"
        weights = mx.load(weights_path)

        # Unflatten and load actor params
        def unflatten_params(flat_dict, prefix, template):
            result = {}
            for key, val in template.items():
                full_key = f"{prefix}{key}"
                if isinstance(val, dict):
                    result[key] = unflatten_params(flat_dict, f"{full_key}.", val)
                else:
                    result[key] = flat_dict[full_key]
            return result

        actor_params = unflatten_params(weights, "actor.", self.actor.parameters())
        critic_params = unflatten_params(weights, "critic.", self.critic.parameters())

        self.actor.update(actor_params)
        self.critic.update(critic_params)

        # Load stats
        stats_path = path.replace(".npz", "") + "_stats.npz"
        stats = np.load(stats_path)
        self.reward_mean = float(stats["reward_mean"])
        self.reward_std = float(stats["reward_std"])
        self.reward_count = int(stats["reward_count"])

        # Eval to commit
        mx.eval(self.actor.parameters(), self.critic.parameters())
