# agent.py

import random
import pygame
from config import *

class Agent:
    def __init__(self, x, y, energy=10):
        self.x = x
        self.y = y
        self.alive = True
        self.is_predator = False
        self.energy = energy
        self.pos_x = x * CELL_SIZE
        self.pos_y = y * CELL_SIZE

        # Fallback traits
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.age = 0
        self.trail = []
        self.vision_radius = random.randint(MIN_VISION_RADIUS, MAX_VISION_RADIUS)

    def move_random(self):
        dx = random.choice([-1, 0, 1]) * self.speed
        dy = random.choice([-1, 0, 1]) * self.speed
        self._move(dx, dy)

    def move_toward(self, target):
        if not target:
            self.move_random()
            return
        dx = (1 if self.x < target.x else -1 if self.x > target.x else 0) * self.speed
        dy = (1 if self.y < target.y else -1 if self.y > target.y else 0) * self.speed
        self._move(dx, dy)

    def move_away_from(self, target):
        if not target:
            self.move_random()
            return
        dx = (1 if self.x > target.x else -1 if self.x < target.x else 0) * self.speed
        dy = (1 if self.y > target.y else -1 if self.y < target.y else 0) * self.speed
        self._move(dx, dy)

    def _move(self, dx, dy):
        old_x, old_y = self.x, self.y
        self.x = int(self.x + dx) % GRID_SIZE
        self.y = int(self.y + dy) % GRID_SIZE
        self.trail.append((self.pos_x, self.pos_y))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

    def distance_to(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def update_animation(self):
        target_x = self.x * CELL_SIZE
        target_y = self.y * CELL_SIZE
        self.pos_x += (target_x - self.pos_x) / ANIMATION_STEPS
        self.pos_y += (target_y - self.pos_y) / ANIMATION_STEPS

    def update_age_energy_trail(self):
        self.age += 1
        if self.age > MAX_AGE:
            self.alive = False

    def draw_trail(self, screen):
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

class Dwarf(Agent):
    def __init__(self, x, y, energy=10):
        super().__init__(x, y, energy)
        self.speed = random.uniform(DWARF_MIN_SPEED, DWARF_MAX_SPEED)
        self.vision_radius = random.randint(DWARF_MIN_VISION_RADIUS, DWARF_MAX_VISION_RADIUS)
