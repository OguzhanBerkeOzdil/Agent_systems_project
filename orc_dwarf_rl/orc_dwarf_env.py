"""Parallel environment for the Orc-Dwarf RL example."""

import random
import numpy as np

try:
    from pettingzoo.utils.env import ParallelEnv
except ImportError:  # pragma: no cover - fallback for very old PettingZoo
    from pettingzoo.utils import parallel_base_env as _old
    ParallelEnv = _old.ParallelEnv

from gymnasium import spaces
from orc_dwarf_rl.config import (
    GRID_SIZE,
    NUM_ORCS,
    NUM_DWARFS,
    MAX_ENERGY,
    INITIAL_ENERGY,
    DEFAULT_SIGHT,
    DEFAULT_SPEED,
    ATTACK_RANGE,
    RESOURCE_NODE_COUNT,
    RESOURCE_ENERGY,
    MAX_STEPS,
)


class OrcDwarfEnv(ParallelEnv):
    """Simple grid-based predator/prey environment using PettingZoo's parallel API."""

    metadata = {"name": "orc_dwarf_v0"}

    def __init__(self, num_orcs=NUM_ORCS, num_dwarfs=NUM_DWARFS):
        super().__init__()
        self.num_orcs = num_orcs
        self.num_dwarfs = num_dwarfs
        self.grid_size = GRID_SIZE
        self.pos = {}
        self.energy = {}
        self.alive = {}
        self.steps = 0
        self.resource_nodes = []

        self.agents = [f"orc_{i}" for i in range(self.num_orcs)] + [f"dwarf_{i}" for i in range(self.num_dwarfs)]
        self.possible_agents = list(self.agents)

        obs_dim = 9  # [x,y,energy,res_x,res_y,enemy_x,enemy_y,sight,speed]
        self.observation_spaces = {
            a: spaces.Box(low=-1.0, high=1.0, shape=(obs_dim,), dtype=np.float32) for a in self.agents
        }
        self.action_spaces = {a: spaces.Discrete(9) for a in self.agents}

    # ------------------------------------------------------------------
    def _random_pos(self):
        return (random.randrange(self.grid_size), random.randrange(self.grid_size))

    def _spawn_resources(self):
        self.resource_nodes = [self._random_pos() for _ in range(RESOURCE_NODE_COUNT)]

    # ------------------------------------------------------------------
    def reset(self, seed=None, options=None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        self.steps = 0
        # Ensure all agents are present at the start of each episode.
        self.agents = list(self.possible_agents)
        self._spawn_resources()
        self.pos = {a: self._random_pos() for a in self.agents}
        self.energy = {a: INITIAL_ENERGY for a in self.agents}
        self.alive = {a: True for a in self.agents}
        observations = {a: self.observe(a) for a in self.agents}
        return observations

    # ------------------------------------------------------------------
    def step(self, actions):
        rewards = {a: 0.0 for a in self.agents}
        terminations = {a: False for a in self.agents}
        truncations = {a: False for a in self.agents}
        infos = {a: {} for a in self.agents}
        self.steps += 1

        # movement
        for agent, action in actions.items():
            if not self.alive.get(agent, False):
                continue
            x, y = self.pos[agent]
            dx, dy = 0, 0
            if action == 0:
                dy = -DEFAULT_SPEED
            elif action == 1:
                dy = DEFAULT_SPEED
            elif action == 2:
                dx = DEFAULT_SPEED
            elif action == 3:
                dx = -DEFAULT_SPEED
            elif action == 5:  # toward resource
                target = self._nearest_resource(x, y)
                if target:
                    dx, dy = self._direction_toward((x, y), target)
            elif action == 6:  # toward enemy
                target = self._nearest_enemy(agent)
                if target:
                    dx, dy = self._direction_toward((x, y), self.pos[target])
            elif action == 7:  # flee enemy
                target = self._nearest_enemy(agent)
                if target:
                    dx, dy = self._direction_away((x, y), self.pos[target])
            # action 4 = stay still
            self.pos[agent] = self._clamp_pos(x + dx, y + dy)

        # attacks after movement
        for agent, action in actions.items():
            if not self.alive.get(agent, False):
                continue
            if action == 8:
                enemy = self._nearest_enemy(agent)
                if enemy and self._manhattan(self.pos[agent], self.pos[enemy]) <= ATTACK_RANGE:
                    self.alive[enemy] = False
                    rewards[agent] += 2.0
                    rewards[enemy] -= 2.0

        # resource collection and energy updates
        for agent in list(self.agents):
            if not self.alive.get(agent, False):
                continue
            rewards[agent] += 0.01  # living bonus
            self.energy[agent] -= 1
            x, y = self.pos[agent]
            if (x, y) in self.resource_nodes:
                rewards[agent] += 1.0
                self.energy[agent] = min(MAX_ENERGY, self.energy[agent] + RESOURCE_ENERGY)
                self.resource_nodes.remove((x, y))
                self.resource_nodes.append(self._random_pos())
            if self.energy[agent] <= 0 or not self.alive[agent]:
                terminations[agent] = True
                self.alive[agent] = False
                rewards[agent] -= 5.0

        if self.steps >= MAX_STEPS:
            for agent in self.agents:
                if not terminations[agent]:
                    truncations[agent] = True

        # remove dead agents from list
        for agent in self.agents:
            if terminations[agent] or truncations[agent]:
                pass
        self.agents = [a for a in self.agents if self.alive.get(a, False)]
        observations = {a: self.observe(a) for a in self.agents}
        return observations, rewards, terminations, truncations, infos

    # ------------------------------------------------------------------
    def _direction_toward(self, pos, target):
        x, y = pos
        tx, ty = target
        dx = 1 if tx > x else -1 if tx < x else 0
        dy = 1 if ty > y else -1 if ty < y else 0
        return dx, dy

    def _direction_away(self, pos, target):
        dx, dy = self._direction_toward(pos, target)
        return -dx, -dy

    def _clamp_pos(self, x, y):
        x = max(0, min(self.grid_size - 1, int(x)))
        y = max(0, min(self.grid_size - 1, int(y)))
        return (x, y)

    def _manhattan(self, p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def _nearest_resource(self, x, y):
        if not self.resource_nodes:
            return None
        return min(self.resource_nodes, key=lambda p: self._manhattan((x, y), p))

    def _nearest_enemy(self, agent):
        species = "orc" if agent.startswith("dwarf") else "dwarf"
        enemies = [a for a in self.agents if a.startswith(species) and self.alive.get(a, False)]
        if not enemies:
            return None
        x, y = self.pos[agent]
        return min(enemies, key=lambda e: self._manhattan((x, y), self.pos[e]))

    # ------------------------------------------------------------------
    def observe(self, agent):
        x, y = self.pos[agent]
        norm_x = x / (self.grid_size - 1)
        norm_y = y / (self.grid_size - 1)
        energy = self.energy[agent] / MAX_ENERGY

        res = self._nearest_resource(x, y)
        if res:
            res_dx = (res[0] - x) / self.grid_size
            res_dy = (res[1] - y) / self.grid_size
        else:
            res_dx = res_dy = 0.0

        enemy = self._nearest_enemy(agent)
        if enemy:
            ex, ey = self.pos[enemy]
            enemy_dx = (ex - x) / self.grid_size
            enemy_dy = (ey - y) / self.grid_size
        else:
            enemy_dx = enemy_dy = 0.0

        sight = DEFAULT_SIGHT / self.grid_size
        speed = DEFAULT_SPEED
        obs = np.array(
            [
                norm_x,
                norm_y,
                energy,
                res_dx,
                res_dy,
                enemy_dx,
                enemy_dy,
                sight,
                speed,
            ],
            dtype=np.float32,
        )
        return obs

    # ------------------------------------------------------------------
    def render(self):
        grid = [["." for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for rx, ry in self.resource_nodes:
            grid[ry][rx] = "R"
        for a in self.agents:
            x, y = self.pos[a]
            grid[y][x] = "O" if a.startswith("orc") else "D"
        print("\n".join("".join(row) for row in grid))
        print()
