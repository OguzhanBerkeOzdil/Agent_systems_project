# agent.py

import random
import pygame
import numpy as np
from collections import defaultdict
from config import *

# Discrete actions for Q-learning
ACTIONS = [
    "move_random",
    "move_toward_food",
    "move_away_from_enemy",
    "wait"
]

class Agent:
    def __init__(self, x, y, energy=10):
        self.x = x
        self.y = y
        self.alive = True
        self.is_predator = False
        self.energy = energy
        # For optional smooth animations; you can ignore these if drawing directly from x,y
        self.pos_x = x * CELL_SIZE
        self.pos_y = y * CELL_SIZE

        # Movement & lifecycle traits
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.age = 0
        self.trail = []
        self.vision_radius = random.randint(MIN_VISION_RADIUS, MAX_VISION_RADIUS)

        # Q-table: maps state tuples to numpy arrays of action‐values
        self.q_table = defaultdict(lambda: np.zeros(len(ACTIONS)))

    def get_state(self, env):
        """
        Returns a discrete state tuple:
          (dx_food, dy_food, dx_enemy, dy_enemy, energy_bucket)
        Each of dx_*, dy_* ∈ {-1, 0, +1}, energy_bucket ∈ [0..4].
        """
        # -- Food
        food = env.find_nearest(self, food=True, radius=self.vision_radius)
        if food is None:
            dx_food = dy_food = 0
        else:
            fx, fy = food if isinstance(food, tuple) else (food.x, food.y)
            dx_food = int(np.sign(fx - self.x))
            dy_food = int(np.sign(fy - self.y))

        # -- Enemy
        species = "Dwarf" if self.is_predator else "Orc"
        enemy = env.find_nearest(self, species=species, radius=self.vision_radius)
        if enemy is None:
            dx_enemy = dy_enemy = 0
        else:
            ex, ey = enemy if isinstance(enemy, tuple) else (enemy.x, enemy.y)
            dx_enemy = int(np.sign(ex - self.x))
            dy_enemy = int(np.sign(ey - self.y))

        # -- Energy bucket (0–4)
        bucket = min(int(self.energy / (MAX_ENERGY / 5)), 4)

        return (dx_food, dy_food, dx_enemy, dy_enemy, bucket)

    def choose_action(self, state):
        """ε-greedy action selection from Q-table."""
        if random.random() < EPSILON:
            return random.randrange(len(ACTIONS))
        return int(np.argmax(self.q_table[state]))

    def update_q(self, state, action_idx, reward, next_state):
        """Standard Q-learning update rule."""
        best_next = np.max(self.q_table[next_state])
        td_target = reward + GAMMA * best_next
        td_error = td_target - self.q_table[state][action_idx]
        self.q_table[state][action_idx] += ALPHA * td_error

    def act(self, env):
        """
        Perform one decision step:
          1) Observe current state
          2) Pick action (ε-greedy)
          3) Execute action
          4) Get reward = Δenergy
          5) Update Q-table
        """
        state = self.get_state(env)
        action_idx = self.choose_action(state)
        prev_energy = self.energy

        action = ACTIONS[action_idx]
        if action == "move_random":
            self.move_random()

        elif action == "move_toward_food":
            targ = env.find_nearest(self, food=True, radius=self.vision_radius)
            if isinstance(targ, tuple):
                pos = targ
            elif targ is None:
                pos = None
            else:
                pos = (targ.x, targ.y)
            self.move_toward(pos)

        elif action == "move_away_from_enemy":
            targ = env.find_nearest(self,
                                    species=("Dwarf" if self.is_predator else "Orc"),
                                    radius=self.vision_radius)
            if isinstance(targ, tuple):
                pos = targ
            elif targ is None:
                pos = None
            else:
                pos = (targ.x, targ.y)
            self.move_away_from(pos)

        # wait = do nothing

        # Energy costs & gains
        self.energy -= ENERGY_LOSS_PER_STEP
        if env.try_eat(self):
            self.energy = min(self.energy + ENERGY_GAIN_PER_EAT, MAX_ENERGY)
        if self.energy >= REPRODUCTION_THRESHOLD:
            env.reproduce(self)

        # Compute reward and learn
        reward = self.energy - prev_energy
        next_state = self.get_state(env)
        self.update_q(state, action_idx, reward, next_state)

    # ─── Movement Helpers ─────────────────────────────────────────────────────

    def move_random(self):
        dx = random.choice([-1, 0, 1]) * self.speed
        dy = random.choice([-1, 0, 1]) * self.speed
        self._move(dx, dy)

    def move_toward(self, target_pos):
        if not target_pos:
            return self.move_random()
        tx, ty = target_pos
        dx = (1 if self.x < tx else -1 if self.x > tx else 0) * self.speed
        dy = (1 if self.y < ty else -1 if self.y > ty else 0) * self.speed
        self._move(dx, dy)

    def move_away_from(self, target_pos):
        if not target_pos:
            return self.move_random()
        tx, ty = target_pos
        dx = (1 if self.x > tx else -1 if self.x < tx else 0) * self.speed
        dy = (1 if self.y > ty else -1 if self.y < ty else 0) * self.speed
        self._move(dx, dy)

    def _move(self, dx, dy):
        """Update grid position; record previous pixel pos for trail."""
        self.x = int(self.x + dx) % GRID_SIZE
        self.y = int(self.y + dy) % GRID_SIZE
        self.trail.append((self.pos_x, self.pos_y))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

    # ─── Optional Animation & Drawing ─────────────────────────────────────────

    def update_animation(self):
        """Smoothly animate pos_x/pos_y toward actual grid coords."""
        target_x = self.x * CELL_SIZE
        target_y = self.y * CELL_SIZE
        self.pos_x += (target_x - self.pos_x) / ANIMATION_STEPS
        self.pos_y += (target_y - self.pos_y) / ANIMATION_STEPS

    def update_age_energy_trail(self):
        """Age agent and kill if beyond MAX_AGE."""
        self.age += 1
        if self.age > MAX_AGE:
            self.alive = False

    def draw_trail(self, screen):
        """Render fading trail behind agent."""
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail))) if self.trail else 0
            surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            color = DWARF_COLOR if not self.is_predator else ORC_COLOR
            surf.fill((*color, alpha))
            screen.blit(surf, (tx, ty))


class Orc(Agent):
    def __init__(self, x, y, energy=10):
        super().__init__(x, y, energy)
        self.speed = random.uniform(ORC_MIN_SPEED, ORC_MAX_SPEED)
        self.vision_radius = random.randint(ORC_MIN_VISION_RADIUS, ORC_MAX_VISION_RADIUS)
        self.is_predator = True


class Dwarf(Agent):
    def __init__(self, x, y, energy=10):
        super().__init__(x, y, energy)
        self.speed = random.uniform(DWARF_MIN_SPEED, DWARF_MAX_SPEED)
        self.vision_radius = random.randint(DWARF_MIN_VISION_RADIUS, DWARF_MAX_VISION_RADIUS)
        self.is_predator = False
