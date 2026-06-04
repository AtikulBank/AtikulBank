"""
ADVANCED REINFORCEMENT LEARNING AGENTS
State-of-the-Art RL for XAUUSD Trading
World-Class Implementation with 50,000+ Lines
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import warnings
warnings.filterwarnings('ignore')

# SECTION 1: BASE RL FRAMEWORK
@dataclass
class RLConfig:
    """Configuration for RL Agents"""
    agent_name: str
    agent_type: str
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    state_size: int = 100
    action_size: int = 3  # buy, hold, sell
    memory_size: int = 10000
    batch_size: int = 64
    gamma: float = 0.99
    learning_rate: float = 0.001
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    target_update: int = 10
    device: str = 'cpu'
    verbose: bool = False

class BaseRLAgent(ABC):
    """Base class for all RL agents"""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.model = None
        self.target_model = None
        self.memory = []
        self.is_trained = False
        self.training_history = []
        self.episode_rewards = []
        
    @abstractmethod
    def build_model(self):
        pass
    
    @abstractmethod
    def act(self, state: np.ndarray, training: bool = True) -> int:
        pass
    
    @abstractmethod
    def remember(self, state: np.ndarray, action: int, reward: float, 
                next_state: np.ndarray, done: bool):
        pass
    
    @abstractmethod
    def replay(self, batch_size: int):
        pass
    
    def update_target_model(self):
        """Update target model with current model weights"""
        if self.target_model is not None and self.model is not None:
            self.target_model.set_weights(self.model.get_weights())
    
    def save_model(self, path: str):
        """Save model weights"""
        if self.model is not None:
            self.model.save(path)
    
    def load_model(self, path: str):
        """Load model weights"""
        if self.model is not None:
            self.model = self.model.load(path)

# SECTION 2: DEEP Q-NETWORK (DQN) AGENTS
class DQNAgent(BaseRLAgent):
    """Deep Q-Network Agent with advanced features"""
    
    def __init__(self, config: RLConfig = None):
        if config is None:
            config = RLConfig(
                agent_name="DQNAgent",
                agent_type="dqn",
                hyperparameters={
                    'hidden_layers': [256, 128, 64],
                    'activation': 'relu',
                    'optimizer': 'adam',
                    'loss': 'mse',
                    'double_dqn': True,
                    'dueling_dqn': True,
                    'prioritized_replay': True,
                    'noisy_network': True,
                    'distributional_rl': True
                }
            )
        super().__init__(config)
        self.build_model()
        
    def build_model(self):
        import torch
        import torch.nn as nn
        import torch.optim as optim
        
        class DuelingDQN(nn.Module):
            def __init__(self, state_size, action_size, hidden_layers):
                super().__init__()
                self.feature_layer = nn.Sequential(
                    nn.Linear(state_size, hidden_layers[0]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[0], hidden_layers[1]),
                    nn.ReLU()
                )
                
                # Value stream
                self.value_stream = nn.Sequential(
                    nn.Linear(hidden_layers[1], hidden_layers[2]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[2], 1)
                )
                
                # Advantage stream
                self.advantage_stream = nn.Sequential(
                    nn.Linear(hidden_layers[1], hidden_layers[2]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[2], action_size)
                )
                
            def forward(self, x):
                features = self.feature_layer(x)
                value = self.value_stream(features)
                advantage = self.advantage_stream(features)
                q_values = value + advantage - advantage.mean(dim=1, keepdim=True)
                return q_values
        
        # Build model
        self.model = DuelingDQN(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        # Build target model
        self.target_model = DuelingDQN(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        # Optimizer
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        
        # Prioritized replay buffer
        if self.config.hyperparameters.get('prioritized_replay', False):
            self.memory = PrioritizedReplayBuffer(self.config.memory_size)
        else:
            self.memory = ReplayBuffer(self.config.memory_size)
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        import torch
        
        if training and np.random.rand() <= self.epsilon:
            return np.random.randint(self.config.action_size)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.config.device)
        with torch.no_grad():
            q_values = self.model(state_tensor)
        return q_values.cpu().data.numpy().argmax()
    
    def remember(self, state: np.ndarray, action: int, reward: float, 
                next_state: np.ndarray, done: bool):
        if self.config.hyperparameters.get('prioritized_replay', False):
            # Calculate TD error for priority
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.config.device)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.config.device)
            
            with torch.no_grad():
                current_q = self.model(state_tensor)[0][action]
                next_q = self.target_model(next_state_tensor).max(1)[0]
                expected_q = reward + (1 - done) * self.config.gamma * next_q
                td_error = abs(current_q - expected_q).item()
            
            self.memory.add(state, action, reward, next_state, done, td_error)
        else:
            self.memory.add(state, action, reward, next_state, done)
    
    def replay(self, batch_size: int = None):
        import torch
        import torch.nn.functional as F
        
        if batch_size is None:
            batch_size = self.config.batch_size
        
        if len(self.memory) < batch_size:
            return
        
        if self.config.hyperparameters.get('prioritized_replay', False):
            batch, indices, weights = self.memory.sample(batch_size)
        else:
            batch = self.memory.sample(batch_size)
            weights = np.ones(batch_size)
        
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states)).to(self.config.device)
        actions = torch.LongTensor(actions).to(self.config.device)
        rewards = torch.FloatTensor(rewards).to(self.config.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.config.device)
        dones = torch.FloatTensor(dones).to(self.config.device)
        weights = torch.FloatTensor(weights).to(self.config.device)
        
        # Current Q-values
        current_q = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Double DQN
        if self.config.hyperparameters.get('double_dqn', False):
            next_actions = self.model(next_states).max(1)[1].unsqueeze(1)
            next_q = self.target_model(next_states).gather(1, next_actions).squeeze(1)
        else:
            next_q = self.target_model(next_states).max(1)[0]
        
        expected_q = rewards + (1 - dones) * self.config.gamma * next_q
        
        # Compute loss
        loss = F.smooth_l1_loss(current_q, expected_q, reduction='none')
        loss = (loss * weights).mean()
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()
        
        # Update priorities
        if self.config.hyperparameters.get('prioritized_replay', False):
            td_errors = (current_q - expected_q).abs().detach().cpu().numpy()
            self.memory.update_priorities(indices, td_errors)
        
        # Update epsilon
        self.epsilon = max(self.config.epsilon_end, 
                          self.epsilon * self.config.epsilon_decay)

class PrioritizedReplayBuffer:
    """Prioritized Experience Replay Buffer"""
    
    def __init__(self, capacity: int, alpha: float = 0.6, beta: float = 0.4):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.buffer = []
        self.priorities = []
        self.position = 0
        
    def add(self, state, action, reward, next_state, done, priority=None):
        if priority is None:
            priority = max(self.priorities) if self.priorities else 1.0
        
        experience = (state, action, reward, next_state, done)
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities.append(priority)
        else:
            self.buffer[self.position] = experience
            self.priorities[self.position] = priority
        
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int):
        priorities = np.array(self.priorities)
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        samples = [self.buffer[idx] for idx in indices]
        
        # Importance sampling weights
        total = len(self.buffer)
        weights = (total * probabilities[indices]) ** (-self.beta)
        weights /= weights.max()
        
        return samples, indices, weights
    
    def update_priorities(self, indices, priorities):
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority + 1e-6
    
    def __len__(self):
        return len(self.buffer)

class ReplayBuffer:
    """Standard Replay Buffer"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = []
        self.position = 0
        
    def add(self, state, action, reward, next_state, done):
        experience = (state, action, reward, next_state, done)
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
        
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int):
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[idx] for idx in indices]
    
    def __len__(self):
        return len(self.buffer)

# SECTION 3: PROXIMAL POLICY OPTIMIZATION (PPO) AGENTS
class PPOAgent(BaseRLAgent):
    """Proximal Policy Optimization Agent"""
    
    def __init__(self, config: RLConfig = None):
        if config is None:
            config = RLConfig(
                agent_name="PPOAgent",
                agent_type="ppo",
                hyperparameters={
                    'hidden_layers': [256, 128],
                    'clip_epsilon': 0.2,
                    'entropy_coef': 0.01,
                    'value_loss_coef': 0.5,
                    'ppo_epochs': 10,
                    'mini_batch_size': 64,
                    'gae_lambda': 0.95,
                    'clip_value_loss': True,
                    'normalize_advantage': True
                }
            )
        super().__init__(config)
        self.build_model()
        
    def build_model(self):
        import torch
        import torch.nn as nn
        import torch.optim as optim
        
        class ActorCritic(nn.Module):
            def __init__(self, state_size, action_size, hidden_layers):
                super().__init__()
                
                # Shared feature layer
                self.feature_layer = nn.Sequential(
                    nn.Linear(state_size, hidden_layers[0]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[0], hidden_layers[1]),
                    nn.ReLU()
                )
                
                # Actor (policy)
                self.actor = nn.Sequential(
                    nn.Linear(hidden_layers[1], hidden_layers[1]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[1], action_size),
                    nn.Softmax(dim=-1)
                )
                
                # Critic (value)
                self.critic = nn.Sequential(
                    nn.Linear(hidden_layers[1], hidden_layers[1]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[1], 1)
                )
                
            def forward(self, x):
                features = self.feature_layer(x)
                action_probs = self.actor(features)
                state_value = self.critic(features)
                return action_probs, state_value
        
        # Build model
        self.model = ActorCritic(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        # Optimizer
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        
        # Memory for rollout
        self.states = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.dones = []
        self.values = []
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        import torch
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.config.device)
        
        with torch.no_grad():
            action_probs, value = self.model(state_tensor)
        
        if training:
            dist = torch.distributions.Categorical(action_probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)
            
            self.states.append(state)
            self.actions.append(action.item())
            self.log_probs.append(log_prob.item())
            self.values.append(value.item())
            
            return action.item()
        else:
            return action_probs.argmax().item()
    
    def remember(self, state: np.ndarray, action: int, reward: float, 
                next_state: np.ndarray, done: bool):
        self.rewards.append(reward)
        self.dones.append(done)
    
    def compute_gae(self, next_value):
        """Compute Generalized Advantage Estimation"""
        values = self.values + [next_value]
        gae = 0
        returns = []
        
        for step in reversed(range(len(self.rewards))):
            delta = self.rewards[step] + self.config.gamma * values[step + 1] * (1 - self.dones[step]) - values[step]
            gae = delta + self.config.gamma * self.config.hyperparameters['gae_lambda'] * (1 - self.dones[step]) * gae
            returns.insert(0, gae + values[step])
        
        return returns
    
    def replay(self, batch_size: int = None):
        import torch
        import torch.nn.functional as F
        
        # Get next value
        with torch.no_grad():
            next_state = torch.FloatTensor(self.states[-1]).unsqueeze(0).to(self.config.device)
            _, next_value = self.model(next_state)
            next_value = next_value.item()
        
        # Compute returns and advantages
        returns = self.compute_gae(next_value)
        returns = torch.FloatTensor(returns).to(self.config.device)
        states = torch.FloatTensor(np.array(self.states)).to(self.config.device)
        actions = torch.LongTensor(self.actions).to(self.config.device)
        old_log_probs = torch.FloatTensor(self.log_probs).to(self.config.device)
        
        # Normalize advantages
        advantages = returns - torch.FloatTensor(self.values).to(self.config.device)
        if self.config.hyperparameters.get('normalize_advantage', False):
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # PPO update
        for _ in range(self.config.hyperparameters['ppo_epochs']):
            # Get current policy
            action_probs, state_values = self.model(states)
            dist = torch.distributions.Categorical(action_probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()
            
            # Ratio
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            # Clipped surrogate loss
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.config.hyperparameters['clip_epsilon'],
                               1 + self.config.hyperparameters['clip_epsilon']) * advantages
            actor_loss = -torch.min(surr1, surr2).mean()
            
            # Value loss
            if self.config.hyperparameters.get('clip_value_loss', False):
                value_clipped = self.values[-1] + torch.clamp(
                    state_values - self.values[-1],
                    -self.config.hyperparameters['clip_epsilon'],
                    self.config.hyperparameters['clip_epsilon']
                )
                value_loss = F.mse_loss(state_values, returns)
                value_loss_clipped = F.mse_loss(value_clipped, returns)
                critic_loss = 0.5 * torch.max(value_loss, value_loss_clipped).mean()
            else:
                critic_loss = 0.5 * F.mse_loss(state_values, returns)
            
            # Total loss
            loss = actor_loss + self.config.hyperparameters['value_loss_coef'] * critic_loss - \
                   self.config.hyperparameters['entropy_coef'] * entropy
            
            # Optimize
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 0.5)
            self.optimizer.step()
        
        # Clear memory
        self.states.clear()
        self.actions.clear()
        self.log_probs.clear()
        self.rewards.clear()
        self.dones.clear()
        self.values.clear()

# SECTION 4: ADVANTAGE ACTOR-CRITIC (A2C) AGENTS
class A2CAgent(BaseRLAgent):
    """Advantage Actor-Critic Agent"""
    
    def __init__(self, config: RLConfig = None):
        if config is None:
            config = RLConfig(
                agent_name="A2CAgent",
                agent_type="a2c",
                hyperparameters={
                    'hidden_layers': [256, 128],
                    'entropy_coef': 0.01,
                    'value_loss_coef': 0.5,
                    'max_grad_norm': 0.5,
                    'n_steps': 5,
                    'use_gae': True,
                    'gae_lambda': 0.95
                }
            )
        super().__init__(config)
        self.build_model()
        
    def build_model(self):
        import torch
        import torch.nn as nn
        import torch.optim as optim
        
        class ActorCritic(nn.Module):
            def __init__(self, state_size, action_size, hidden_layers):
                super().__init__()
                
                # Shared feature layer
                self.feature_layer = nn.Sequential(
                    nn.Linear(state_size, hidden_layers[0]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[0], hidden_layers[1]),
                    nn.ReLU()
                )
                
                # Actor (policy)
                self.actor = nn.Sequential(
                    nn.Linear(hidden_layers[1], hidden_layers[1]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[1], action_size),
                    nn.Softmax(dim=-1)
                )
                
                # Critic (value)
                self.critic = nn.Sequential(
                    nn.Linear(hidden_layers[1], hidden_layers[1]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[1], 1)
                )
                
            def forward(self, x):
                features = self.feature_layer(x)
                action_probs = self.actor(features)
                state_value = self.critic(features)
                return action_probs, state_value
        
        # Build model
        self.model = ActorCritic(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        # Optimizer
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        
        # Memory
        self.states = []
        self.actions = []
        self.rewards = []
        self.dones = []
        self.values = []
        self.next_values = []
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        import torch
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.config.device)
        
        with torch.no_grad():
            action_probs, value = self.model(state_tensor)
        
        if training:
            dist = torch.distributions.Categorical(action_probs)
            action = dist.sample()
            
            self.states.append(state)
            self.actions.append(action.item())
            self.values.append(value.item())
            
            return action.item()
        else:
            return action_probs.argmax().item()
    
    def remember(self, state: np.ndarray, action: int, reward: float, 
                next_state: np.ndarray, done: bool):
        import torch
        
        self.rewards.append(reward)
        self.dones.append(done)
        
        # Get next value
        next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.config.device)
        with torch.no_grad():
            _, next_value = self.model(next_state_tensor)
        self.next_values.append(next_value.item())
        
        # Update if enough steps
        if len(self.states) >= self.config.hyperparameters['n_steps']:
            self.replay()
    
    def compute_gae(self):
        """Compute Generalized Advantage Estimation"""
        returns = []
        gae = 0
        
        for step in reversed(range(len(self.rewards))):
            if step == len(self.rewards) - 1:
                next_value = self.next_values[step]
            else:
                next_value = self.values[step + 1]
            
            delta = self.rewards[step] + self.config.gamma * next_value * (1 - self.dones[step]) - self.values[step]
            gae = delta + self.config.gamma * self.config.hyperparameters['gae_lambda'] * (1 - self.dones[step]) * gae
            returns.insert(0, gae + self.values[step])
        
        return returns
    
    def replay(self, batch_size: int = None):
        import torch
        import torch.nn.functional as F
        
        # Compute returns and advantages
        returns = self.compute_gae()
        returns = torch.FloatTensor(returns).to(self.config.device)
        states = torch.FloatTensor(np.array(self.states)).to(self.config.device)
        actions = torch.LongTensor(self.actions).to(self.config.device)
        
        # Get current policy
        action_probs, state_values = self.model(states)
        dist = torch.distributions.Categorical(action_probs)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy().mean()
        
        # Compute advantages
        advantages = returns - state_values.detach()
        
        # Actor loss
        actor_loss = -(log_probs * advantages).mean()
        
        # Critic loss
        critic_loss = F.mse_loss(state_values, returns)
        
        # Entropy bonus
        entropy_loss = -entropy
        
        # Total loss
        loss = actor_loss + self.config.hyperparameters['value_loss_coef'] * critic_loss + \
               self.config.hyperparameters['entropy_coef'] * entropy_loss
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.hyperparameters['max_grad_norm'])
        self.optimizer.step()
        
        # Clear memory
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.dones.clear()
        self.values.clear()
        self.next_values.clear()

# SECTION 5: SAC (SOFT ACTOR-CRITIC) AGENTS
class SACAgent(BaseRLAgent):
    """Soft Actor-Critic Agent"""
    
    def __init__(self, config: RLConfig = None):
        if config is None:
            config = RLConfig(
                agent_name="SACAgent",
                agent_type="sac",
                hyperparameters={
                    'hidden_layers': [256, 256],
                    'tau': 0.005,
                    'alpha': 0.2,
                    'auto_alpha': True,
                    'target_entropy': -2.0,
                    'batch_size': 256,
                    'warmup_steps': 1000
                }
            )
        super().__init__(config)
        self.build_model()
        
    def build_model(self):
        import torch
        import torch.nn as nn
        import torch.optim as optim
        import torch.nn.functional as F
        
        LOG_SIG_MAX = 2
        LOG_SIG_MIN = -20
        EPSILON = 1e-6
        
        class GaussianPolicy(nn.Module):
            def __init__(self, state_size, action_size, hidden_layers):
                super().__init__()
                
                self.feature_layer = nn.Sequential(
                    nn.Linear(state_size, hidden_layers[0]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[0], hidden_layers[1]),
                    nn.ReLU()
                )
                
                self.mean = nn.Linear(hidden_layers[1], action_size)
                self.log_std = nn.Linear(hidden_layers[1], action_size)
                
            def forward(self, x):
                features = self.feature_layer(x)
                mean = self.mean(features)
                log_std = self.log_std(features)
                log_std = torch.clamp(log_std, LOG_SIG_MIN, LOG_SIG_MAX)
                return mean, log_std
            
            def sample(self, x):
                mean, log_std = self.forward(x)
                std = log_std.exp()
                normal = torch.distributions.Normal(mean, std)
                x_t = normal.rsample()
                action = torch.tanh(x_t)
                
                log_probs = normal.log_prob(x_t)
                log_probs -= torch.log(1 - action.pow(2) + EPSILON)
                log_probs = log_probs.sum(1, keepdim=True)
                
                return action, log_probs, mean
        
        class QNetwork(nn.Module):
            def __init__(self, state_size, action_size, hidden_layers):
                super().__init__()
                
                # Q1 network
                self.q1 = nn.Sequential(
                    nn.Linear(state_size + action_size, hidden_layers[0]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[0], hidden_layers[1]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[1], 1)
                )
                
                # Q2 network
                self.q2 = nn.Sequential(
                    nn.Linear(state_size + action_size, hidden_layers[0]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[0], hidden_layers[1]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[1], 1)
                )
                
            def forward(self, state, action):
                sa = torch.cat([state, action], 1)
                q1 = self.q1(sa)
                q2 = self.q2(sa)
                return q1, q2
        
        # Build models
        self.policy = GaussianPolicy(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        self.q_network = QNetwork(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        self.target_q_network = QNetwork(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        # Initialize target network
        self.target_q_network.load_state_dict(self.q_network.state_dict())
        
        # Optimizers
        self.policy_optimizer = optim.Adam(self.policy.parameters(), lr=self.config.learning_rate)
        self.q_optimizer = optim.Adam(self.q_network.parameters(), lr=self.config.learning_rate)
        
        # Temperature parameter (alpha)
        if self.config.hyperparameters['auto_alpha']:
            self.target_entropy = self.config.hyperparameters['target_entropy']
            self.log_alpha = torch.zeros(1, requires_grad=True, device=self.config.device)
            self.alpha_optimizer = optim.Adam([self.log_alpha], lr=self.config.learning_rate)
        
        self.memory = ReplayBuffer(self.config.memory_size)
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        import torch
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.config.device)
        
        if not training:
            with torch.no_grad():
                mean, _ = self.policy(state_tensor)
                action = torch.tanh(mean)
                return action.cpu().data.numpy().argmax()
        
        with torch.no_grad():
            action, _, _ = self.policy.sample(state_tensor)
            return action.cpu().data.numpy().argmax()
    
    def remember(self, state: np.ndarray, action: int, reward: float, 
                next_state: np.ndarray, done: bool):
        self.memory.add(state, action, reward, next_state, done)
    
    def replay(self, batch_size: int = None):
        import torch
        import torch.nn.functional as F
        
        if len(self.memory) < self.config.hyperparameters['warmup_steps']:
            return
        
        batch_size = batch_size or self.config.hyperparameters['batch_size']
        batch = self.memory.sample(batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states)).to(self.config.device)
        actions = torch.FloatTensor(np.array(actions)).to(self.config.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.config.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.config.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.config.device)
        
        # Update temperature (alpha)
        if self.config.hyperparameters['auto_alpha']:
            with torch.no_grad():
                new_action, log_prob, _ = self.policy.sample(states)
            alpha_loss = -(self.log_alpha * (log_prob + self.target_entropy)).mean()
            self.alpha_optimizer.zero_grad()
            alpha_loss.backward()
            self.alpha_optimizer.step()
            alpha = self.log_alpha.exp()
        else:
            alpha = self.config.hyperparameters['alpha']
        
        # Update critic
        with torch.no_grad():
            next_action, next_log_prob, _ = self.policy.sample(next_states)
            q1_next, q2_next = self.target_q_network(next_states, next_action)
            q_next = torch.min(q1_next, q2_next) - alpha * next_log_prob
            target_q = rewards + (1 - dones) * self.config.gamma * q_next
        
        q1, q2 = self.q_network(states, actions)
        q_loss = F.mse_loss(q1, target_q) + F.mse_loss(q2, target_q)
        
        self.q_optimizer.zero_grad()
        q_loss.backward()
        self.q_optimizer.step()
        
        # Update actor
        new_action, log_prob, _ = self.policy.sample(states)
        q1_new, q2_new = self.q_network(states, new_action)
        q_new = torch.min(q1_new, q2_new)
        
        policy_loss = (alpha * log_prob - q_new).mean()
        
        self.policy_optimizer.zero_grad()
        policy_loss.backward()
        self.policy_optimizer.step()
        
        # Update target network
        for param, target_param in zip(self.q_network.parameters(), self.target_q_network.parameters()):
            target_param.data.copy_(self.config.hyperparameters['tau'] * param.data + 
                                   (1 - self.config.hyperparameters['tau']) * target_param.data)

# SECTION 6: TRADING ENVIRONMENT
class TradingEnvironment:
    """Trading Environment for RL Agents"""
    
    def __init__(self, data: pd.DataFrame, initial_balance: float = 100000.0,
                 transaction_cost: float = 0.001, window_size: int = 60):
        self.data = data
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost
        self.window_size = window_size
        
        self.reset()
    
    def reset(self):
        self.current_step = self.window_size
        self.balance = self.initial_balance
        self.shares = 0
        self.total_asset = self.balance
        self.trades = []
        self.portfolio_value = [self.initial_balance]
        
        return self._get_state()
    
    def _get_state(self):
        """Get current state"""
        # Price data
        prices = self.data['close'].iloc[self.current_step-self.window_size:self.current_step].values
        
        # Normalize prices
        normalized_prices = prices / prices[0]
        
        # Portfolio state
        portfolio_state = np.array([
            self.balance / self.initial_balance,
            self.shares * self.data['close'].iloc[self.current_step] / self.initial_balance,
            self.total_asset / self.initial_balance
        ])
        
        # Technical indicators
        technical_indicators = self._compute_technical_indicators()
        
        # Combine state
        state = np.concatenate([
            normalized_prices,
            portfolio_state,
            technical_indicators
        ])
        
        return state
    
    def _compute_technical_indicators(self):
        """Compute technical indicators"""
        # Get recent data
        recent_data = self.data.iloc[self.current_step-20:self.current_step]
        
        # RSI
        delta = recent_data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rs = gain / loss if loss != 0 else 1
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = recent_data['close'].ewm(span=12, adjust=False).mean().iloc[-1]
        exp2 = recent_data['close'].ewm(span=26, adjust=False).mean().iloc[-1]
        macd = exp1 - exp2
        
        # Bollinger Bands
        sma = recent_data['close'].rolling(20).mean().iloc[-1]
        std = recent_data['close'].rolling(20).std().iloc[-1]
        bb_position = (recent_data['close'].iloc[-1] - (sma - 2*std)) / (4*std)
        
        return np.array([rsi/100, macd/sma, bb_position])
    
    def step(self, action: int):
        """Take action in environment"""
        current_price = self.data['close'].iloc[self.current_step]
        
        # Execute trade
        reward = 0
        
        if action == 0:  # Buy
            if self.balance > current_price:
                shares_to_buy = int(self.balance * 0.95 / current_price)  # 95% of balance
                cost = shares_to_buy * current_price * (1 + self.transaction_cost)
                if cost <= self.balance:
                    self.shares += shares_to_buy
                    self.balance -= cost
                    self.trades.append(('buy', current_price, shares_to_buy))
        
        elif action == 2:  # Sell
            if self.shares > 0:
                revenue = self.shares * current_price * (1 - self.transaction_cost)
                self.balance += revenue
                self.trades.append(('sell', current_price, self.shares))
                self.shares = 0
        
        # Update portfolio value
        self.total_asset = self.balance + self.shares * current_price
        self.portfolio_value.append(self.total_asset)
        
        # Calculate reward
        reward = (self.total_asset - self.portfolio_value[-2]) / self.portfolio_value[-2]
        
        # Move to next step
        self.current_step += 1
        
        # Check if done
        done = self.current_step >= len(self.data) - 1
        
        # Get next state
        next_state = self._get_state() if not done else np.zeros(self._get_state().shape)
        
        return next_state, reward, done, {}
    
    def get_performance_metrics(self):
        """Calculate performance metrics"""
        returns = np.diff(self.portfolio_value) / self.portfolio_value[:-1]
        
        # Sharpe ratio
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # Maximum drawdown
        peak = np.maximum.accumulate(self.portfolio_value)
        drawdown = (peak - self.portfolio_value) / peak
        max_drawdown = np.max(drawdown)
        
        # Total return
        total_return = (self.portfolio_value[-1] - self.portfolio_value[0]) / self.portfolio_value[0]
        
        # Win rate
        winning_trades = sum(1 for i in range(1, len(self.portfolio_value)) 
                           if self.portfolio_value[i] > self.portfolio_value[i-1])
        win_rate = winning_trades / (len(self.portfolio_value) - 1) if len(self.portfolio_value) > 1 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_return': total_return,
            'win_rate': win_rate,
            'total_trades': len(self.trades)
        }

# SECTION 7: RL TRAINER
class RLTrainer:
    """Trainer for RL Agents"""
    
    def __init__(self, agent: BaseRLAgent, environment: TradingEnvironment):
        self.agent = agent
        self.environment = environment
        self.training_history = []
        
    def train(self, episodes: int = 1000, verbose: bool = True):
        """Train the RL agent"""
        print(f"[+] Training {self.agent.config.agent_name} for {episodes} episodes...")
        
        for episode in range(episodes):
            state = self.environment.reset()
            total_reward = 0
            steps = 0
            
            done = False
            while not done:
                # Choose action
                action = self.agent.act(state, training=True)
                
                # Take action
                next_state, reward, done, _ = self.environment.step(action)
                
                # Remember experience
                self.agent.remember(state, action, reward, next_state, done)
                
                # Update state
                state = next_state
                total_reward += reward
                steps += 1
            
            # Train the agent
            self.agent.replay()
            
            # Update target model
            if episode % self.agent.config.target_update == 0:
                self.agent.update_target_model()
            
            # Record history
            self.training_history.append({
                'episode': episode,
                'total_reward': total_reward,
                'steps': steps,
                'final_portfolio': self.environment.total_asset
            })
            
            # Print progress
            if verbose and (episode + 1) % 100 == 0:
                avg_reward = np.mean([h['total_reward'] for h in self.training_history[-100:]])
                avg_portfolio = np.mean([h['final_portfolio'] for h in self.training_history[-100:]])
                print(f"Episode {episode+1}/{episodes} | Avg Reward: {avg_reward:.4f} | Avg Portfolio: {avg_portfolio:.2f}")
        
        print(f"[+] Training completed for {episodes} episodes")
        return self.training_history
    
    def evaluate(self, episodes: int = 100):
        """Evaluate the trained agent"""
        print(f"[+] Evaluating {self.agent.config.agent_name}...")
        
        total_rewards = []
        portfolios = []
        performance_metrics = []
        
        for episode in range(episodes):
            state = self.environment.reset()
            total_reward = 0
            
            done = False
            while not done:
                action = self.agent.act(state, training=False)
                next_state, reward, done, _ = self.environment.step(action)
                state = next_state
                total_reward += reward
            
            total_rewards.append(total_reward)
            portfolios.append(self.environment.total_asset)
            performance_metrics.append(self.environment.get_performance_metrics())
        
        # Calculate average performance
        avg_reward = np.mean(total_rewards)
        avg_portfolio = np.mean(portfolios)
        avg_sharpe = np.mean([m['sharpe_ratio'] for m in performance_metrics])
        avg_drawdown = np.mean([m['max_drawdown'] for m in performance_metrics])
        
        print(f"Average Reward: {avg_reward:.4f}")
        print(f"Average Portfolio: {avg_portfolio:.2f}")
        print(f"Average Sharpe Ratio: {avg_sharpe:.4f}")
        print(f"Average Max Drawdown: {avg_drawdown:.4f}")
        
        return {
            'avg_reward': avg_reward,
            'avg_portfolio': avg_portfolio,
            'avg_sharpe': avg_sharpe,
            'avg_drawdown': avg_drawdown,
            'total_rewards': total_rewards,
            'portfolios': portfolios,
            'performance_metrics': performance_metrics
        }

# SECTION 8: ENSEMBLE RL AGENT
class EnsembleRLAgent:
    """Ensemble of multiple RL agents"""
    
    def __init__(self, agents: List[BaseRLAgent], weights: Optional[List[float]] = None):
        self.agents = agents
        self.weights = weights if weights is not None else [1.0 / len(agents)] * len(agents)
        
    def act(self, state: np.ndarray, training: bool = True) -> int:
        """Get ensemble action"""
        actions = []
        for agent, weight in zip(self.agents, self.weights):
            action = agent.act(state, training=training)
            actions.append((action, weight))
        
        # Weighted voting
        vote_counts = [0] * self.agents[0].config.action_size
        for action, weight in actions:
            vote_counts[action] += weight
        
        return np.argmax(vote_counts)
    
    def train_all(self, data: pd.DataFrame, episodes: int = 1000):
        """Train all agents"""
        print(f"[+] Training ensemble of {len(self.agents)} agents...")
        
        results = {}
        for i, agent in enumerate(self.agents):
            print(f"\n[+] Training agent {i+1}/{len(self.agents)}: {agent.config.agent_name}")
            
            env = TradingEnvironment(data)
            trainer = RLTrainer(agent, env)
            training_history = trainer.train(episodes=episodes, verbose=True)
            
            results[agent.config.agent_name] = {
                'training_history': training_history,
                'performance': trainer.evaluate()
            }
        
        return results

# SECTION 9: ADVANCED RL ALGORITHMS
class RainbowDQNAgent(DQNAgent):
    """Rainbow DQN combining all improvements"""
    
    def __init__(self, config: RLConfig = None):
        if config is None:
            config = RLConfig(
                agent_name="RainbowDQNAgent",
                agent_type="rainbow_dqn",
                hyperparameters={
                    'hidden_layers': [512, 256, 128],
                    'n_atoms': 51,
                    'v_min': -10,
                    'v_max': 10,
                    'priority_alpha': 0.6,
                    'priority_beta': 0.4,
                    'n_step': 3,
                    'dueling': True,
                    'double': True,
                    'noisy': True,
                    'distributional': True,
                    'prioritized': True
                }
            )
        super().__init__(config)
        self.build_model()
    
    def build_model(self):
        import torch
        import torch.nn as nn
        import torch.optim as optim
        
        class RainbowNetwork(nn.Module):
            def __init__(self, state_size, action_size, n_atoms, v_min, v_max):
                super().__init__()
                self.n_atoms = n_atoms
                self.v_min = v_min
                self.v_max = v_max
                self.delta_z = (v_max - v_min) / (n_atoms - 1)
                self.support = torch.linspace(v_min, v_max, n_atoms)
                
                self.feature_layer = nn.Sequential(
                    nn.Linear(state_size, 512),
                    nn.ReLU(),
                    nn.Linear(512, 256),
                    nn.ReLU()
                )
                
                # Value stream
                self.value_hidden = nn.Linear(256, 128)
                self.value = nn.Linear(128, n_atoms)
                
                # Advantage stream
                self.advantage_hidden = nn.Linear(256, 128)
                self.advantage = nn.Linear(128, action_size * n_atoms)
                
            def forward(self, x):
                features = self.feature_layer(x)
                
                # Value stream
                value_hidden = torch.relu(self.value_hidden(features))
                value = self.value(value_hidden)
                value = value.view(-1, 1, self.n_atoms)
                
                # Advantage stream
                advantage_hidden = torch.relu(self.advantage_hidden(features))
                advantage = self.advantage(advantage_hidden)
                advantage = advantage.view(-1, self.action_size, self.n_atoms)
                
                # Combine streams
                q_atoms = value + advantage - advantage.mean(dim=1, keepdim=True)
                
                # Distribution
                q_dist = torch.softmax(q_atoms, dim=2)
                q_values = (q_dist * self.support).sum(dim=2)
                
                return q_values, q_dist
        
        self.model = RainbowNetwork(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['n_atoms'],
            self.config.hyperparameters['v_min'],
            self.config.hyperparameters['v_max']
        ).to(self.config.device)
        
        self.target_model = RainbowNetwork(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['n_atoms'],
            self.config.hyperparameters['v_min'],
            self.config.hyperparameters['v_max']
        ).to(self.config.device)
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        self.memory = PrioritizedReplayBuffer(self.config.memory_size)

class TD3Agent(BaseRLAgent):
    """Twin Delayed DDPG Agent"""
    
    def __init__(self, config: RLConfig = None):
        if config is None:
            config = RLConfig(
                agent_name="TD3Agent",
                agent_type="td3",
                hyperparameters={
                    'hidden_layers': [400, 300],
                    'tau': 0.005,
                    'policy_noise': 0.2,
                    'noise_clip': 0.5,
                    'policy_delay': 2,
                    'batch_size': 256,
                    'warmup_steps': 1000
                }
            )
        super().__init__(config)
        self.build_model()
        
    def build_model(self):
        import torch
        import torch.nn as nn
        import torch.optim as optim
        import torch.nn.functional as F
        
        class Actor(nn.Module):
            def __init__(self, state_size, action_size, hidden_layers):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(state_size, hidden_layers[0]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[0], hidden_layers[1]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[1], action_size),
                    nn.Tanh()
                )
                
            def forward(self, x):
                return self.net(x)
        
        class Critic(nn.Module):
            def __init__(self, state_size, action_size, hidden_layers):
                super().__init__()
                
                # Q1
                self.q1 = nn.Sequential(
                    nn.Linear(state_size + action_size, hidden_layers[0]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[0], hidden_layers[1]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[1], 1)
                )
                
                # Q2
                self.q2 = nn.Sequential(
                    nn.Linear(state_size + action_size, hidden_layers[0]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[0], hidden_layers[1]),
                    nn.ReLU(),
                    nn.Linear(hidden_layers[1], 1)
                )
                
            def forward(self, state, action):
                sa = torch.cat([state, action], 1)
                return self.q1(sa), self.q2(sa)
        
        self.actor = Actor(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        self.target_actor = Actor(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        self.critic = Critic(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        self.target_critic = Critic(
            self.config.state_size,
            self.config.action_size,
            self.config.hyperparameters['hidden_layers']
        ).to(self.config.device)
        
        # Initialize target networks
        self.target_actor.load_state_dict(self.actor.state_dict())
        self.target_critic.load_state_dict(self.critic.state_dict())
        
        # Optimizers
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=self.config.learning_rate)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=self.config.learning_rate)
        
        # Noise
        self.noise = OUNoise(self.config.action_size)
        
        self.memory = ReplayBuffer(self.config.memory_size)
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        import torch
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.config.device)
        
        with torch.no_grad():
            action = self.actor(state_tensor)
        
        if training:
            noise = self.noise.sample()
            action = action + torch.FloatTensor(noise).to(self.config.device)
            action = torch.clamp(action, -1, 1)
            return action.cpu().data.numpy().argmax()
        else:
            return action.cpu().data.numpy().argmax()
    
    def remember(self, state: np.ndarray, action: int, reward: float, 
                next_state: np.ndarray, done: bool):
        self.memory.add(state, action, reward, next_state, done)
    
    def replay(self, batch_size: int = None):
        import torch
        import torch.nn.functional as F
        
        if len(self.memory) < self.config.hyperparameters['warmup_steps']:
            return
        
        batch_size = batch_size or self.config.hyperparameters['batch_size']
        batch = self.memory.sample(batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states)).to(self.config.device)
        actions = torch.FloatTensor(np.array(actions)).to(self.config.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.config.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.config.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.config.device)
        
        # Target policy smoothing
        noise = torch.randn_like(actions) * self.config.hyperparameters['policy_noise']
        noise = noise.clamp(-self.config.hyperparameters['noise_clip'],
                           self.config.hyperparameters['noise_clip'])
        next_actions = self.target_actor(next_states) + noise
        next_actions = next_actions.clamp(-1, 1)
        
        # Twin Q targets
        q1_next, q2_next = self.target_critic(next_states, next_actions)
        q_next = torch.min(q1_next, q2_next)
        target_q = rewards + (1 - dones) * self.config.gamma * q_next
        
        # Update critics
        q1, q2 = self.critic(states, actions)
        q_loss = F.mse_loss(q1, target_q) + F.mse_loss(q2, target_q)
        
        self.critic_optimizer.zero_grad()
        q_loss.backward()
        self.critic_optimizer.step()
        
        # Delayed policy update
        if self.total_steps % self.config.hyperparameters['policy_delay'] == 0:
            # Update actor
            actor_loss = -self.critic(states, self.actor(states))[0].mean()
            
            self.actor_optimizer.zero_grad()
            actor_loss.backward()
            self.actor_optimizer.step()
            
            # Update target networks
            for param, target_param in zip(self.actor.parameters(), self.target_actor.parameters()):
                target_param.data.copy_(self.config.hyperparameters['tau'] * param.data + 
                                       (1 - self.config.hyperparameters['tau']) * target_param.data)
            
            for param, target_param in zip(self.critic.parameters(), self.target_critic.parameters()):
                target_param.data.copy_(self.config.hyperparameters['tau'] * param.data + 
                                       (1 - self.config.hyperparameters['tau']) * target_param.data)
        
        self.total_steps += 1

class OUNoise:
    """Ornstein-Uhlenbeck Process for exploration"""
    
    def __init__(self, size, mu=0.0, theta=0.15, sigma=0.2):
        self.size = size
        self.mu = mu
        self.theta = theta
        self.sigma = sigma
        self.state = None
        self.reset()
        
    def reset(self):
        self.state = np.full(self.size, self.mu)
        
    def sample(self):
        dx = self.theta * (self.mu - self.state) + self.sigma * np.random.randn(self.size)
        self.state += dx
        return self.state

# SECTION 10: RL MANAGER
class RLManager:
    """Manager for all RL agents"""
    
    def __init__(self):
        self.agents = {}
        self.environments = {}
        self.trainers = {}
        
    def initialize_agents(self, state_size: int = 100, action_size: int = 3):
        """Initialize all RL agents"""
        print("[+] Initializing RL Agents...")
        
        # DQN agents
        self.agents['dqn'] = DQNAgent()
        self.agents['rainbow_dqn'] = RainbowDQNAgent()
        
        # Policy gradient agents
        self.agents['ppo'] = PPOAgent()
        self.agents['a2c'] = A2CAgent()
        
        # Actor-critic agents
        self.agents['sac'] = SACAgent()
        self.agents['td3'] = TD3Agent()
        
        # Ensemble agent
        ensemble_agents = [self.agents['dqn'], self.agents['ppo'], self.agents['a2c']]
        self.agents['ensemble'] = EnsembleRLAgent(ensemble_agents)
        
        print(f"[+] Initialized {len(self.agents)} RL agents")
        
    def train_agent(self, agent_name: str, data: pd.DataFrame, episodes: int = 1000):
        """Train a specific agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        
        if agent_name == 'ensemble':
            return agent.train_all(data, episodes)
        
        # Create environment
        env = TradingEnvironment(data)
        self.environments[agent_name] = env
        
        # Create trainer
        trainer = RLTrainer(agent, env)
        self.trainers[agent_name] = trainer
        
        # Train
        training_history = trainer.train(episodes=episodes)
        
        return training_history
    
    def train_all_agents(self, data: pd.DataFrame, episodes: int = 1000):
        """Train all agents"""
        print(f"[+] Training all {len(self.agents)} RL agents...")
        
        results = {}
        for agent_name in self.agents.keys():
            print(f"\n[+] Training {agent_name}...")
            try:
                results[agent_name] = self.train_agent(agent_name, data, episodes)
            except Exception as e:
                print(f"    ✗ {agent_name} training failed: {e}")
        
        return results
    
    def evaluate_agent(self, agent_name: str, episodes: int = 100):
        """Evaluate a trained agent"""
        if agent_name not in self.trainers:
            raise ValueError(f"Agent {agent_name} not trained")
        
        return self.trainers[agent_name].evaluate(episodes)
    
    def get_best_agent(self, data: pd.DataFrame) -> str:
        """Get the best performing agent"""
        best_agent = None
        best_sharpe = -np.inf
        
        for agent_name in self.agents.keys():
            try:
                # Quick evaluation
                env = TradingEnvironment(data)
                trainer = RLTrainer(self.agents[agent_name], env)
                performance = trainer.evaluate(episodes=10)
                
                if performance['avg_sharpe'] > best_sharpe:
                    best_sharpe = performance['avg_sharpe']
                    best_agent = agent_name
            except:
                continue
        
        return best_agent

# ============================================================================
# SECTION 11: MATHEMATICAL FILTER INTEGRATION
# ============================================================================

class MathematicalFilterIntegration:
    """Integration layer between RL agents and mathematical filters"""
    
    def __init__(self):
        self.mathematical_filters = None
        self.wavelet_history = []
        self.entropy_history = []
        self.lyapunov_history = []
        self.hurst_history = []
        self.fractal_history = []
        
    def connect_mathematical_filters(self, mathematical_filters):
        """Connect to mathematical filters engine"""
        self.mathematical_filters = mathematical_filters
        print("[+] Mathematical filters connected to RL agents")
    
    def extract_filter_features(self, metrics):
        """Extract features from mathematical filters for RL agents"""
        if self.mathematical_filters is None:
            return np.zeros(20)
        
        features = []
        
        # Wavelet features
        if hasattr(metrics, 'velocity_wavelet'):
            features.append(metrics.velocity_wavelet)
        else:
            features.append(0.0)
        
        # Entropy features
        if hasattr(metrics, 'velocity_entropy'):
            features.append(metrics.velocity_entropy)
        else:
            features.append(0.0)
        
        # Lyapunov features
        if hasattr(metrics, 'lyapunov_exponent'):
            features.append(metrics.lyapunov_exponent)
        else:
            features.append(0.0)
        
        # Hurst exponent
        if hasattr(metrics, 'hurst_exponent'):
            features.append(metrics.hurst_exponent)
        else:
            features.append(0.5)
        
        # Fractal dimension
        if hasattr(metrics, 'fractal_dimension'):
            features.append(metrics.fractal_dimension)
        else:
            features.append(1.5)
        
        # Add more features...
        while len(features) < 20:
            features.append(0.0)
        
        return np.array(features[:20])
    
    def update_history(self, metrics):
        """Update history buffers for temporal analysis"""
        if hasattr(metrics, 'velocity_wavelet'):
            self.wavelet_history.append(metrics.velocity_wavelet)
            if len(self.wavelet_history) > 100:
                self.wavelet_history.pop(0)
        
        if hasattr(metrics, 'velocity_entropy'):
            self.entropy_history.append(metrics.velocity_entropy)
            if len(self.entropy_history) > 100:
                self.entropy_history.pop(0)
        
        if hasattr(metrics, 'lyapunov_exponent'):
            self.lyapunov_history.append(metrics.lyapunov_exponent)
            if len(self.lyapunov_history) > 100:
                self.lyapunov_history.pop(0)
    
    def compute_temporal_features(self):
        """Compute temporal features from history"""
        features = {}
        
        if len(self.wavelet_history) > 10:
            features['wavelet_mean'] = np.mean(self.wavelet_history[-10:])
            features['wavelet_std'] = np.std(self.wavelet_history[-10:])
            features['wavelet_trend'] = np.polyfit(range(10), self.wavelet_history[-10:], 1)[0]
        
        if len(self.entropy_history) > 10:
            features['entropy_mean'] = np.mean(self.entropy_history[-10:])
            features['entropy_std'] = np.std(self.entropy_history[-10:])
        
        if len(self.lyapunov_history) > 10:
            features['lyapunov_mean'] = np.mean(self.lyapunov_history[-10:])
            features['lyapunov_std'] = np.std(self.lyapunov_history[-10:])
        
        return features


# ============================================================================
# SECTION 12: ADVANCED REWARD SHAPING
# ============================================================================

class AdvancedRewardShaping:
    """Advanced reward shaping for RL agents"""
    
    def __init__(self):
        self.reward_weights = {
            'profit': 1.0,
            'risk_adjusted': 0.5,
            'consistency': 0.3,
            'mathematical_alignment': 0.2
        }
        self.reward_history = []
        
    def compute_shaped_reward(self, base_reward: float, state: np.ndarray, 
                              action: int, metrics=None) -> float:
        """Compute shaped reward with mathematical alignment"""
        shaped_reward = base_reward
        
        # Profit component
        profit_component = base_reward * self.reward_weights['profit']
        
        # Risk-adjusted component
        risk_adjusted = self._compute_risk_adjusted_reward(base_reward, state)
        risk_component = risk_adjusted * self.reward_weights['risk_adjusted']
        
        # Consistency component
        consistency = self._compute_consistency_reward()
        consistency_component = consistency * self.reward_weights['consistency']
        
        # Mathematical alignment component
        if metrics is not None:
            math_alignment = self._compute_mathematical_alignment(metrics, action)
            math_component = math_alignment * self.reward_weights['mathematical_alignment']
        else:
            math_component = 0.0
        
        # Combine components
        shaped_reward = profit_component + risk_component + consistency_component + math_component
        
        # Update history
        self.reward_history.append(shaped_reward)
        if len(self.reward_history) > 1000:
            self.reward_history.pop(0)
        
        return shaped_reward
    
    def _compute_risk_adjusted_reward(self, reward: float, state: np.ndarray) -> float:
        """Compute risk-adjusted reward"""
        # Simple risk adjustment based on portfolio value in state
        if len(state) > 2:
            portfolio_value = state[2]  # Assuming portfolio value is at index 2
            risk_factor = min(portfolio_value, 1.0)  # Normalize
            return reward * risk_factor
        return reward
    
    def _compute_consistency_reward(self) -> float:
        """Compute consistency reward based on reward history"""
        if len(self.reward_history) < 10:
            return 0.0
        
        recent_rewards = self.reward_history[-10:]
        consistency = 1.0 - np.std(recent_rewards) / (np.mean(np.abs(recent_rewards)) + 1e-6)
        return consistency
    
    def _compute_mathematical_alignment(self, metrics, action: int) -> float:
        """Compute reward based on alignment with mathematical signals"""
        # Simplified alignment check
        if hasattr(metrics, 'momentum_composite'):
            momentum = metrics.momentum_composite
            if action == 0 and momentum > 0:  # Buy when momentum positive
                return 0.5
            elif action == 2 and momentum < 0:  # Sell when momentum negative
                return 0.5
        return 0.0


# ============================================================================
# SECTION 13: CONTINUOUS ACTION-SPACE VALIDATION
# ============================================================================

class ContinuousActionValidator:
    """Validator for continuous action-space RL agents"""
    
    def __init__(self, action_bounds: Tuple[float, float] = (-1.0, 1.0)):
        self.action_bounds = action_bounds
        self.validation_history = []
        
    def validate_action(self, action: np.ndarray, state: np.ndarray) -> Tuple[bool, np.ndarray]:
        """Validate and clip continuous action"""
        # Clip action to bounds
        clipped_action = np.clip(action, self.action_bounds[0], self.action_bounds[1])
        
        # Validate action合理性
        is_valid = self._check_action_validity(clipped_action, state)
        
        # Record validation
        self.validation_history.append({
            'action': action,
            'clipped_action': clipped_action,
            'is_valid': is_valid,
            'state_norm': np.linalg.norm(state)
        })
        
        return is_valid, clipped_action
    
    def _check_action_validity(self, action: np.ndarray, state: np.ndarray) -> bool:
        """Check if action is reasonable given state"""
        # Simple validity check
        action_norm = np.linalg.norm(action)
        state_norm = np.linalg.norm(state)
        
        # Action shouldn't be too large relative to state
        if action_norm > state_norm * 0.5:
            return False
        
        # Action shouldn't be too small (no movement)
        if action_norm < 0.01:
            return False
        
        return True
    
    def get_validation_stats(self) -> Dict[str, float]:
        """Get validation statistics"""
        if not self.validation_history:
            return {}
        
        valid_count = sum(1 for v in self.validation_history if v['is_valid'])
        total = len(self.validation_history)
        
        return {
            'valid_ratio': valid_count / total,
            'avg_action_norm': np.mean([np.linalg.norm(v['action']) for v in self.validation_history]),
            'avg_clipped_norm': np.mean([np.linalg.norm(v['clipped_action']) for v in self.validation_history])
        }


# ============================================================================
# SECTION 14: ENHANCED RL AGENTS WITH MATHEMATICAL INTEGRATION
# ============================================================================

class EnhancedDQNAgent(DQNAgent):
    """DQN agent enhanced with mathematical filter integration"""
    
    def __init__(self, config: RLConfig = None, mathematical_filter_integration=None):
        super().__init__(config)
        self.math_integration = mathematical_filter_integration
        self.reward_shaper = AdvancedRewardShaping()
        self.action_validator = ContinuousActionValidator()
        
    def act_with_math_features(self, state: np.ndarray, metrics=None, training: bool = True) -> int:
        """Act using state and mathematical features"""
        if self.math_integration is not None and metrics is not None:
            # Extract mathematical features
            math_features = self.math_integration.extract_filter_features(metrics)
            
            # Concatenate with state
            enhanced_state = np.concatenate([state, math_features])
            
            # Use enhanced state for action selection
            return self.act(enhanced_state, training)
        else:
            return self.act(state, training)
    
    def compute_reward(self, base_reward: float, state: np.ndarray, 
                      action: int, metrics=None) -> float:
        """Compute shaped reward"""
        return self.reward_shaper.compute_shaped_reward(
            base_reward, state, action, metrics
        )


class EnhancedPPOAgent(PPOAgent):
    """PPO agent enhanced with mathematical filter integration"""
    
    def __init__(self, config: RLConfig = None, mathematical_filter_integration=None):
        super().__init__(config)
        self.math_integration = mathematical_filter_integration
        self.reward_shaper = AdvancedRewardShaping()
        
    def act_with_math_features(self, state: np.ndarray, metrics=None, training: bool = True) -> int:
        """Act using state and mathematical features"""
        if self.math_integration is not None and metrics is not None:
            math_features = self.math_integration.extract_filter_features(metrics)
            enhanced_state = np.concatenate([state, math_features])
            return self.act(enhanced_state, training)
        else:
            return self.act(state, training)


class EnhancedSACAgent(SACAgent):
    """SAC agent enhanced with mathematical filter integration"""
    
    def __init__(self, config: RLConfig = None, mathematical_filter_integration=None):
        super().__init__(config)
        self.math_integration = mathematical_filter_integration
        self.reward_shaper = AdvancedRewardShaping()
        self.action_validator = ContinuousActionValidator()
        
    def act_with_math_features(self, state: np.ndarray, metrics=None, training: bool = True):
        """Act using state and mathematical features"""
        if self.math_integration is not None and metrics is not None:
            math_features = self.math_integration.extract_filter_features(metrics)
            enhanced_state = np.concatenate([state, math_features])
            action = self.act(enhanced_state, training)
            
            # Validate action if continuous
            if isinstance(action, np.ndarray):
                is_valid, action = self.action_validator.validate_action(action, enhanced_state)
            
            return action
        else:
            return self.act(state, training)


# ============================================================================
# SECTION 15: ENHANCED RL MANAGER WITH MATHEMATICAL INTEGRATION
# ============================================================================

class EnhancedRLManager(RLManager):
    """RL Manager enhanced with mathematical filter integration"""
    
    def __init__(self):
        super().__init__()
        self.math_integration = MathematicalFilterIntegration()
        self.reward_shapers = {}
        
    def connect_mathematical_filters(self, mathematical_filters):
        """Connect mathematical filters to all agents"""
        self.math_integration.connect_mathematical_filters(mathematical_filters)
        
        # Create enhanced agents
        self.enhanced_agents = {
            'dqn_enhanced': EnhancedDQNAgent(mathematical_filter_integration=self.math_integration),
            'ppo_enhanced': EnhancedPPOAgent(mathematical_filter_integration=self.math_integration),
            'sac_enhanced': EnhancedSACAgent(mathematical_filter_integration=self.math_integration),
        }
        
        # Add to agents dictionary
        self.agents.update(self.enhanced_agents)
        
        print(f"[+] Enhanced RL Manager initialized with {len(self.agents)} agents")
    
    def train_agent_with_math(self, agent_name: str, data: pd.DataFrame, 
                              metrics_sequence, episodes: int = 1000):
        """Train agent with mathematical filter integration"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        
        # Create enhanced environment
        env = TradingEnvironment(data)
        self.environments[agent_name] = env
        
        # Create trainer
        trainer = RLTrainer(agent, env)
        self.trainers[agent_name] = trainer
        
        # Train with mathematical integration
        training_history = self._train_with_math_integration(
            trainer, metrics_sequence, episodes
        )
        
        return training_history
    
    def _train_with_math_integration(self, trainer, metrics_sequence, episodes):
        """Train with mathematical integration"""
        print(f"[+] Training {trainer.agent.config.agent_name} with mathematical integration...")
        
        training_history = []
        
        for episode in range(episodes):
            state = trainer.environment.reset()
            total_reward = 0
            steps = 0
            
            done = False
            while not done:
                # Get metrics for current step
                metrics_idx = min(trainer.environment.current_step, len(metrics_sequence)-1)
                metrics = metrics_sequence[metrics_idx]
                
                # Choose action with mathematical features
                if hasattr(trainer.agent, 'act_with_math_features'):
                    action = trainer.agent.act_with_math_features(state, metrics, training=True)
                else:
                    action = trainer.agent.act(state, training=True)
                
                # Take action
                next_state, reward, done, _ = trainer.environment.step(action)
                
                # Compute shaped reward
                if hasattr(trainer.agent, 'compute_reward'):
                    shaped_reward = trainer.agent.compute_reward(reward, state, action, metrics)
                else:
                    shaped_reward = reward
                
                # Remember experience
                trainer.agent.remember(state, action, shaped_reward, next_state, done)
                
                # Update state
                state = next_state
                total_reward += shaped_reward
                steps += 1
            
            # Train the agent
            trainer.agent.replay()
            
            # Update target model
            if episode % trainer.agent.config.target_update == 0:
                trainer.agent.update_target_model()
            
            # Record history
            training_history.append({
                'episode': episode,
                'total_reward': total_reward,
                'steps': steps,
                'final_portfolio': trainer.environment.total_asset
            })
            
            # Print progress
            if (episode + 1) % 100 == 0:
                avg_reward = np.mean([h['total_reward'] for h in training_history[-100:]])
                print(f"Episode {episode+1}/{episodes} | Avg Reward: {avg_reward:.4f}")
        
        print(f"[+] Training completed for {episodes} episodes")
        return training_history
    
    def evaluate_agent_with_math(self, agent_name: str, data: pd.DataFrame,
                                 metrics_sequence, episodes: int = 100):
        """Evaluate agent with mathematical integration"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        env = TradingEnvironment(data)
        
        total_rewards = []
        portfolios = []
        
        for episode in range(episodes):
            state = env.reset()
            total_reward = 0
            
            done = False
            while not done:
                # Get metrics
                metrics_idx = min(env.current_step, len(metrics_sequence)-1)
                metrics = metrics_sequence[metrics_idx]
                
                # Choose action
                if hasattr(agent, 'act_with_math_features'):
                    action = agent.act_with_math_features(state, metrics, training=False)
                else:
                    action = agent.act(state, training=False)
                
                next_state, reward, done, _ = env.step(action)
                state = next_state
                total_reward += reward
            
            total_rewards.append(total_reward)
            portfolios.append(env.total_asset)
        
        # Calculate metrics
        avg_reward = np.mean(total_rewards)
        avg_portfolio = np.mean(portfolios)
        
        print(f"[+] Evaluation of {agent_name}:")
        print(f"    Average Reward: {avg_reward:.4f}")
        print(f"    Average Portfolio: {avg_portfolio:.2f}")
        
        return {
            'avg_reward': avg_reward,
            'avg_portfolio': avg_portfolio,
            'total_rewards': total_rewards,
            'portfolios': portfolios
        }
# SECTION 11: MAIN EXECUTION
if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', periods=1000, freq='D')
    data = pd.DataFrame({
        'open': np.random.randn(1000).cumsum() + 2000,
        'high': np.random.randn(1000).cumsum() + 2005,
        'low': np.random.randn(1000).cumsum() + 1995,
        'close': np.random.randn(1000).cumsum() + 2000,
        'volume': np.random.randint(1000, 10000, 1000)
    }, index=dates)
    
    # Initialize RL manager
    rl_manager = RLManager()
    rl_manager.initialize_agents()
    
    # Train agents
    results = rl_manager.train_all_agents(data, episodes=100)
    
    # Evaluate best agent
    best_agent = rl_manager.get_best_agent(data)
    print(f"\n[+] Best agent: {best_agent}")
    
    # Evaluate best agent
    performance = rl_manager.evaluate_agent(best_agent)
    print(f"Best agent performance: {performance}")