# main.py
import pygame, random, os
from config import *
from agent import Orc, Dwarf

pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()

orc_img = pygame.image.load("assets/orc.png")
dwarf_img = pygame.image.load("assets/dwarf.png")
orc_img = pygame.transform.scale(orc_img, (CELL_SIZE, CELL_SIZE))
dwarf_img = pygame.transform.scale(dwarf_img, (CELL_SIZE, CELL_SIZE))

pygame.mixer.music.load(BACKGROUND_MUSIC)
pygame.mixer.music.play(-1)
attack_sound = pygame.mixer.Sound("assets/attack.wav") if os.path.exists("assets/attack.wav") else None
death_sound = pygame.mixer.Sound("assets/death.wav") if os.path.exists("assets/death.wav") else None

orcs = [Orc(random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1), INITIAL_PREDATOR_ENERGY) for _ in range(NUM_ORCS)]
dwarves = [Dwarf(random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1), INITIAL_PREY_ENERGY) for _ in range(NUM_DWARVES)]
agents = orcs + dwarves

obstacles = [(random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)) for _ in range(OBSTACLE_COUNT)]
heatmap = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
resource_nodes = [(random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)) for _ in range(RESOURCE_NODE_COUNT)]
last_resource_spawn = 0

log_filename = "log.txt"
if os.path.exists(log_filename): os.remove(log_filename)
def log_event(msg): 
    with open(log_filename, "a") as f: 
        f.write(msg+"\n")

turn_history, orc_history, dwarf_history = [], [], []
day = True; turn_counter = 0; paused = False; show_heatmap = SHOW_HEATMAP
weather_state = "clear"
last_weather_change = 0

def switch_roles():
    global day
    day = not day
    for o in orcs:
        o.is_predator = day      # Orcs attack during the day
    for d in dwarves:
        d.is_predator = not day   # Dwarves defend during the day

def update_weather():
    global weather_state, last_weather_change
    if turn_counter - last_weather_change >= WEATHER_CHANGE_INTERVAL:
        weather_state = random.choice(WEATHER_STATES)
        last_weather_change = turn_counter

def count_pack_members(agent):
    count = 0
    for other in agents:
        if other.alive and other.is_predator and other != agent and agent.distance_to(other) <= PACK_RADIUS:
            count += 1
    return count

def find_closest_enemy(agent, agents, enemy_flag):
    enemies = [a for a in agents if a.alive and (a.is_predator == enemy_flag)]
    return min(enemies, key=lambda e: agent.distance_to(e)) if enemies else None

def update_agents():
    for agent in agents:
        if not agent.alive: continue
        old_x, old_y = agent.x, agent.y
        extra_loss = 0
        if weather_state == "rain":
            extra_loss = RAIN_ENERGY_LOSS_INCREASE
        elif weather_state == "storm":
            extra_loss = STORM_ENERGY_LOSS_INCREASE
        if agent.is_predator:
            target = find_closest_enemy(agent, agents, False)
            if target and agent.distance_to(target) <= VISION_RADIUS:
                # In storm, slow movement by sometimes skipping move_random()
                if weather_state == "storm" and random.random() < STORM_MOVEMENT_SLOWDOWN:
                    pass
                else:
                    agent.move_toward(target)
            else:
                agent.move_random()
            agent.energy -= (PREDATOR_ENERGY_LOSS + extra_loss)
        else:
            threat = find_closest_enemy(agent, agents, True)
            if threat and agent.distance_to(threat) <= VISION_RADIUS:
                agent.move_away_from(threat)
            else:
                agent.move_random()
            agent.energy -= (PREY_ENERGY_LOSS + extra_loss)
        if (agent.x, agent.y) in obstacles: 
            agent.x, agent.y = old_x, old_y
        heatmap[agent.x][agent.y] += 1
        if (agent.x, agent.y) in resource_nodes:
            agent.energy += RESOURCE_NODE_ENERGY
            resource_nodes.remove((agent.x, agent.y))
            log_event(f"Turn {turn_counter}: Resource at ({agent.x},{agent.y}).")
        if agent.energy <= 0 and agent.alive:
            agent.alive = False
            if death_sound: death_sound.play()
            log_event(f"Turn {turn_counter}: Agent died at ({agent.x},{agent.y}).")
        agent.update_animation()

def check_interactions():
    global turn_counter
    for predator in [a for a in agents if a.alive and a.is_predator]:
        for prey in [a for a in agents if a.alive and not a.is_predator]:
            if predator.x == prey.x and predator.y == prey.y:
                prey.alive = False
                bonus = 1 + PACK_ENERGY_BONUS_MULTIPLIER * count_pack_members(predator)
                predator.energy += PREDATOR_ENERGY_GAIN * bonus
                if attack_sound: attack_sound.play()
                log_event(f"Turn {turn_counter}: Kill at ({predator.x},{predator.y}), bonus {bonus:.2f}.")
                break

def reproduce_agents():
    new_agents = []
    for agent in agents:
        if not agent.alive: continue
        if isinstance(agent, Dwarf):
            if agent.energy >= DWARF_REPRODUCTION_THRESHOLD:
                offspring_energy = int(agent.energy * (1 - DWARF_REPRODUCTION_COST))
                agent.energy = int(agent.energy * DWARF_REPRODUCTION_COST)
                new_agents.append(Dwarf(agent.x, agent.y, offspring_energy))
                log_event(f"Turn {turn_counter}: Dwarf reproduced at ({agent.x},{agent.y}).")
        else:
            if agent.energy >= REPRODUCTION_THRESHOLD:
                offspring_energy = agent.energy // 2
                agent.energy //= 2
                new_agents.append(Orc(agent.x, agent.y, offspring_energy))
                log_event(f"Turn {turn_counter}: Orc reproduced at ({agent.x},{agent.y}).")
    agents.extend(new_agents)
    global orcs, dwarves
    orcs = [a for a in agents if isinstance(a, Orc)]
    dwarves = [a for a in agents if isinstance(a, Dwarf)]

def reinforcement_event():
    global agents, orcs, dwarves
    for agent in agents:
        if agent.alive:
            agent.energy += REINFORCEMENT_ENERGY_BOOST
    for _ in range(REINFORCEMENT_NEW_ORCS):
        agents.append(Orc(random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1), INITIAL_PREDATOR_ENERGY))
    for _ in range(REINFORCEMENT_NEW_DWARVES):
        agents.append(Dwarf(random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1), INITIAL_PREY_ENERGY))
    orcs = [a for a in agents if isinstance(a, Orc)]
    dwarves = [a for a in agents if isinstance(a, Dwarf)]
    log_event(f"Turn {turn_counter}: Reinforcement.")

def update_resources():
    global last_resource_spawn, resource_nodes
    if turn_counter - last_resource_spawn >= RESOURCE_NODE_RESPAWN_INTERVAL:
        while len(resource_nodes) < RESOURCE_NODE_COUNT:
            resource_nodes.append((random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)))
        last_resource_spawn = turn_counter

def draw_grid():
    bg = DAY_BG_COLOR if day else NIGHT_BG_COLOR
    if weather_state == "storm":
        bg = (20,20,60)
    screen.fill(bg)
    for obs in obstacles:
        pygame.draw.rect(screen, OBSTACLE_COLOR, (obs[0]*CELL_SIZE, obs[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE))
    if show_heatmap:
        max_heat = max(max(row) for row in heatmap) if heatmap else 1
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if heatmap[i][j]:
                    intensity = min(255, int(heatmap[i][j] / max_heat * 255))
                    s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    s.fill((intensity,0,0,100))
                    screen.blit(s, (i*CELL_SIZE, j*CELL_SIZE))
    for rn in resource_nodes:
        pygame.draw.circle(screen, (0,255,0), (rn[0]*CELL_SIZE+CELL_SIZE//2, rn[1]*CELL_SIZE+CELL_SIZE//2), CELL_SIZE//3)
    for agent in agents:
        if not agent.alive: continue
        x_pix = int(agent.pos_x)
        y_pix = int(agent.pos_y)
        if isinstance(agent, Orc):
            screen.blit(orc_img, (x_pix, y_pix))
        else:
            screen.blit(dwarf_img, (x_pix, y_pix))
        if agent.is_predator:
            pygame.draw.rect(screen, PREDATOR_HIGHLIGHT, (x_pix, y_pix, CELL_SIZE, CELL_SIZE), 2)
    draw_ui()

def draw_ui():
    font = pygame.font.SysFont(None, 24)
    alive_orcs = sum(1 for o in orcs if o.alive)
    alive_dwarves = sum(1 for d in dwarves if d.alive)
    status = f"Turn: {turn_counter} | Orcs: {alive_orcs} | Dwarves: {alive_dwarves} | {'Day' if day else 'Night'} | Weather: {weather_state} | {'Paused' if paused else ''} | Heatmap: {'On' if show_heatmap else 'Off'}"
    text = font.render(status, True, UI_FONT_COLOR)
    screen.blit(text, (10, GRID_SIZE*CELL_SIZE+10))
    turn_history.append(turn_counter)
    orc_history.append(alive_orcs)
    dwarf_history.append(alive_dwarves)
    chart_top = GRID_SIZE*CELL_SIZE + UI_HEIGHT
    chart_bottom = chart_top + CHART_HEIGHT
    pygame.draw.line(screen, UI_FONT_COLOR, (10, chart_bottom-10), (WINDOW_SIZE[0]-10, chart_bottom-10), 1)
    pygame.draw.line(screen, UI_FONT_COLOR, (10, chart_top+10), (10, chart_bottom-10), 1)
    if turn_history:
        max_pop = max(max(orc_history), max(dwarf_history), 1)
        points_orc, points_dwarf = [], []
        for i, turn in enumerate(turn_history):
            x = 10 + (turn/turn_history[-1])*(WINDOW_SIZE[0]-20)
            y_orc = chart_bottom-10 - (orc_history[i]/max_pop)*(CHART_HEIGHT-20)
            y_dwarf = chart_bottom-10 - (dwarf_history[i]/max_pop)*(CHART_HEIGHT-20)
            points_orc.append((x, y_orc))
            points_dwarf.append((x, y_dwarf))
        if len(points_orc) > 1:
            pygame.draw.lines(screen, ORC_COLOR, False, points_orc, 2)
        if len(points_dwarf) > 1:
            pygame.draw.lines(screen, DWARF_COLOR, False, points_dwarf, 2)

switch_roles()
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p: paused = not paused
            if event.key == pygame.K_r: reinforcement_event()
            if event.key == pygame.K_h: show_heatmap = not show_heatmap
    if not paused:
        turn_counter += 1
        if turn_counter % DAY_DURATION == 0: switch_roles()
        if turn_counter % REINFORCEMENT_INTERVAL == 0: reinforcement_event()
        update_weather()
        update_agents()
        check_interactions()
        reproduce_agents()
        update_resources()
    draw_grid()
    pygame.display.flip()
pygame.quit()
