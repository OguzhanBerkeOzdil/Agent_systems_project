# agent.py

import random
import pygame
from config import *


def mutate_trait(value, minimum, maximum):
    """Return a slightly mutated trait value."""
    if random.random() < MUTATION_RATE:
        change = value * MUTATION_AMOUNT * random.choice([-1, 1])
        value = max(minimum, min(maximum, value + change))
    return value

class Agent:
    """Base class for all moving entities."""

    def __init__(self, x, y, energy=10, speed=None, vision_radius=None):
        self.x = x
        self.y = y
        self.alive = True
        self.is_predator = False
        self.energy = energy
        self.pos_x = x * CELL_SIZE
        self.pos_y = y * CELL_SIZE

        # Fallback traits
        self.speed = speed if speed is not None else random.uniform(MIN_SPEED, MAX_SPEED)
        self.age = 0
        self.trail = []
        self.vision_radius = (
            vision_radius
            if vision_radius is not None
            else random.randint(MIN_VISION_RADIUS, MAX_VISION_RADIUS)
        )
        # record actions taken for simple learning mechanism
        self.action_history = []

    def move_random(self, obstacles=None):
        """Move to a random neighbouring cell avoiding obstacles."""
        for _ in range(5):
            dx = random.choice([-1, 0, 1]) * self.speed
            dy = random.choice([-1, 0, 1]) * self.speed
            if not obstacles:
                break
            nx = int(self.x + dx) % GRID_SIZE
            ny = int(self.y + dy) % GRID_SIZE
            if (nx, ny) not in obstacles:
                break
        self._move(dx, dy, obstacles)

    def move_toward(self, target, obstacles=None):
        """Move one step toward a target avoiding obstacles."""
        if not target:
            self.move_random(obstacles)
            return
        dx = (1 if self.x < target.x else -1 if self.x > target.x else 0) * self.speed
        dy = (1 if self.y < target.y else -1 if self.y > target.y else 0) * self.speed
        self._move(dx, dy, obstacles)

    def move_toward_pos(self, x, y, obstacles=None):
        """Move one step toward a coordinate avoiding obstacles."""
        dx = (1 if self.x < x else -1 if self.x > x else 0) * self.speed
        dy = (1 if self.y < y else -1 if self.y > y else 0) * self.speed
        self._move(dx, dy, obstacles)

    def move_away_from(self, target, obstacles=None):
        """Move one step away from a target avoiding obstacles."""
        if not target:
            self.move_random(obstacles)
            return
        dx = (1 if self.x > target.x else -1 if self.x < target.x else 0) * self.speed
        dy = (1 if self.y > target.y else -1 if self.y < target.y else 0) * self.speed
        self._move(dx, dy, obstacles)

    def _move(self, dx, dy, obstacles=None):
        """Apply movement deltas to grid position while respecting obstacles."""
        new_x = int(self.x + dx) % GRID_SIZE
        new_y = int(self.y + dy) % GRID_SIZE
        if obstacles and (new_x, new_y) in obstacles:
            options = []
            for ox, oy in [(-1,0), (1,0), (0,-1), (0,1), (0,0)]:
                tx = int(self.x + ox) % GRID_SIZE
                ty = int(self.y + oy) % GRID_SIZE
                if (tx, ty) not in obstacles:
                    options.append((tx, ty))
            if options:
                new_x, new_y = random.choice(options)
            else:
                new_x, new_y = self.x, self.y
        self.x, self.y = new_x, new_y
        self.trail.append((self.pos_x, self.pos_y))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

    def distance_to(self, other):
        """Manhattan distance to another agent."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def update_animation(self):
        """Smoothly animate toward the grid position."""
        target_x = self.x * CELL_SIZE
        target_y = self.y * CELL_SIZE
        self.pos_x += (target_x - self.pos_x) / ANIMATION_STEPS
        self.pos_y += (target_y - self.pos_y) / ANIMATION_STEPS

    def update_age_energy_trail(self):
        """Update age and check natural death."""
        self.age += 1
        if self.age > MAX_AGE:
            self.alive = False

    def draw_trail(self, screen):
        """Render fading trail behind the agent."""
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail))) if self.trail else 0
            surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            color = DWARF_COLOR if not self.is_predator else ORC_COLOR
            surf.fill((*color, alpha))
            screen.blit(surf, (tx, ty))

class Orc(Agent):
    """Predator unit."""

    def __init__(self, x, y, energy=10, speed=None, vision_radius=None):
        if speed is None:
            speed = random.uniform(ORC_MIN_SPEED, ORC_MAX_SPEED)
        if vision_radius is None:
            vision_radius = random.randint(ORC_MIN_VISION_RADIUS, ORC_MAX_VISION_RADIUS)
        super().__init__(x, y, energy, speed, vision_radius)

class Dwarf(Agent):
    """Prey unit."""

    def __init__(self, x, y, energy=10, speed=None, vision_radius=None):
        if speed is None:
            speed = random.uniform(DWARF_MIN_SPEED, DWARF_MAX_SPEED)
        if vision_radius is None:
            vision_radius = random.randint(DWARF_MIN_VISION_RADIUS, DWARF_MAX_VISION_RADIUS)
        super().__init__(x, y, energy, speed, vision_radius)
