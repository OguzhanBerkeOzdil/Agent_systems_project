import random
from config import GRID_SIZE, CELL_SIZE, ANIMATION_STEPS

class Agent:
    def __init__(self, x, y, energy=10):
        self.x = x
        self.y = y
        self.alive = True
        self.is_predator = False
        self.energy = energy
        self.pos_x = self.x * CELL_SIZE
        self.pos_y = self.y * CELL_SIZE

    def move_random(self):
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        self.x = (self.x + dx) % GRID_SIZE
        self.y = (self.y + dy) % GRID_SIZE

    def distance_to(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)
        
    def move_toward(self, target):
        if not target:
            self.move_random()
            return
        dx = 1 if self.x < target.x else -1 if self.x > target.x else 0
        dy = 1 if self.y < target.y else -1 if self.y > target.y else 0
        self.x = (self.x + dx) % GRID_SIZE
        self.y = (self.y + dy) % GRID_SIZE

    def move_away_from(self, target):
        if not target:
            self.move_random()
            return
        dx = 1 if self.x > target.x else -1 if self.x < target.x else 0
        dy = 1 if self.y > target.y else -1 if self.y < target.y else 0
        self.x = (self.x + dx) % GRID_SIZE
        self.y = (self.y + dy) % GRID_SIZE

    def update_animation(self):
        target_x = self.x * CELL_SIZE
        target_y = self.y * CELL_SIZE
        self.pos_x += (target_x - self.pos_x) / ANIMATION_STEPS
        self.pos_y += (target_y - self.pos_y) / ANIMATION_STEPS

class Orc(Agent):
    def __init__(self, x, y, energy=10):
        super().__init__(x, y, energy)

class Dwarf(Agent):
    def __init__(self, x, y, energy=10):
        super().__init__(x, y, energy)
