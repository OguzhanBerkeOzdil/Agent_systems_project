import random
from config import GRID_SIZE

class Agent:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True
        self.is_predator = False

    def move_random(self):
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        self.x = (self.x + dx) % GRID_SIZE
        self.y = (self.y + dy) % GRID_SIZE

    def distance_to(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

class Orc(Agent):
    pass  # for now behaves same as base Agent

class Dwarf(Agent):
    pass
