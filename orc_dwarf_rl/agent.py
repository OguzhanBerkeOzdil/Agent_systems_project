# orc_dwarf_rl/agent.py

import numpy as np
from typing import Optional


class RLAgent:
    """Wrapper around a trained RL policy."""

    def __init__(self, model):
        self.model = model

    def act(self, observation: np.ndarray) -> int:
        """Return action from the underlying policy."""
        action, _ = self.model.predict(observation, deterministic=True)
        return int(action)

    @classmethod
    def load(cls, path: str):
        from stable_baselines3.common.base_class import BaseAlgorithm
        model: BaseAlgorithm = BaseAlgorithm.load(path)
        return cls(model)

    def save(self, path: str):
        self.model.save(path)
