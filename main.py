import pygame
import random
from config import *
from agent import Orc, Dwarf

# En üste ekle:
orc_img = pygame.image.load("assets/orc.png")
dwarf_img = pygame.image.load("assets/dwarf.png")

# Boyutu hücreye göre ayarla:
orc_img = pygame.transform.scale(orc_img, (CELL_SIZE, CELL_SIZE))
dwarf_img = pygame.transform.scale(dwarf_img, (CELL_SIZE, CELL_SIZE))

pygame.init()
screen = pygame.display.set_mode((WINDOW_SIZE[0], WINDOW_SIZE[1]))
clock = pygame.time.Clock()

# Initialize agents
orcs = [Orc(random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)) for _ in range(NUM_ORCS)]
dwarves = [Dwarf(random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)) for _ in range(NUM_DWARVES)]

agents = orcs + dwarves
day = True
turn_counter = 0

def switch_roles():
    global day
    day = not day
    for orc in orcs:
        orc.is_predator = not day  # orcs hunt at night
    for dwarf in dwarves:
        dwarf.is_predator = day  # dwarves hunt at day

def draw_grid():
    screen.fill(DAY_BG_COLOR if day else NIGHT_BG_COLOR)

    for agent in agents:
        if not agent.alive:
            continue
        x_pix = agent.x * CELL_SIZE
        y_pix = agent.y * CELL_SIZE

        if isinstance(agent, Orc):
            screen.blit(orc_img, (x_pix, y_pix))
        elif isinstance(agent, Dwarf):
            screen.blit(dwarf_img, (x_pix, y_pix))

        if agent.is_predator:
            pygame.draw.rect(screen, PREDATOR_HIGHLIGHT, (x_pix, y_pix, CELL_SIZE, CELL_SIZE), 2)

    draw_ui()

def draw_ui():
    font = pygame.font.SysFont(None, 24)
    alive_orcs = sum(1 for o in orcs if o.alive)
    alive_dwarves = sum(1 for d in dwarves if d.alive)

    status_text = f"Orcs: {alive_orcs}   Dwarves: {alive_dwarves}   {'Day' if day else 'Night'}"
    text_surf = font.render(status_text, True, UI_FONT_COLOR)

    screen.blit(text_surf, (10, GRID_SIZE * CELL_SIZE + 10))



def update_agents():
    for agent in agents:
        if not agent.alive:
            continue
        agent.move_random()

def check_interactions():
    for predator in [a for a in agents if a.is_predator and a.alive]:
        for prey in [a for a in agents if not a.is_predator and a.alive]:
            if predator.x == prey.x and predator.y == prey.y:
                prey.alive = False  # predator kills prey
                break

# Start with day
switch_roles()

# Main loop
running = True
while running:
    clock.tick(FPS)
    turn_counter += 1

    if turn_counter % DAY_DURATION == 0:
        switch_roles()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    update_agents()
    check_interactions()
    draw_grid()
    pygame.display.flip()

pygame.quit()
