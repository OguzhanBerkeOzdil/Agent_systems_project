# main.py

import os
import random
import pygame
from pygame import mixer
from config import *
from agent import Orc, Dwarf, mutate_trait

pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()

# Load images
orc_img = pygame.image.load("assets/orc.png")
orc_img = pygame.transform.scale(orc_img, (CELL_SIZE, CELL_SIZE))
dwarf_img = pygame.image.load("assets/dwarf.png")
dwarf_img = pygame.transform.scale(dwarf_img, (CELL_SIZE, CELL_SIZE))

# Load audio
mixer.music.load(BACKGROUND_MUSIC)
mixer.music.play(-1)
attack_sound = mixer.Sound("assets/attack.wav") if os.path.exists("assets/attack.wav") else None
death_sound  = mixer.Sound("assets/death.wav")  if os.path.exists("assets/death.wav")  else None
repro_sound  = mixer.Sound(REPRODUCTION_SOUND) if os.path.exists(REPRODUCTION_SOUND) else None

# Persistent high score
try:
    with open(HIGH_SCORE_FILE) as f:
        high_score = int(f.read().strip())
except:
    high_score = 0

def save_high_score(score):
    """Persist high score to file."""
    global high_score
    if score > high_score:
        high_score = score
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(high_score))

# Toggle music
music_on = True

# Initialize world
orcs     = [Orc(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE), INITIAL_PREDATOR_ENERGY)
            for _ in range(NUM_ORCS)]
dwarves  = [Dwarf(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE), INITIAL_PREY_ENERGY)
            for _ in range(NUM_DWARVES)]
agents   = orcs + dwarves

obstacles = [(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE))
             for _ in range(OBSTACLE_COUNT)]
heatmap   = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
resource_nodes = [(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE))
                  for _ in range(RESOURCE_NODE_COUNT)]
last_resource_spawn = 0

# Event log
event_log = []
log_filename = "log.txt"
if os.path.exists(log_filename):
    os.remove(log_filename)
def log_event(msg):
    """Append a message to the log overlay and file."""
    with open(log_filename, "a") as f:
        f.write(msg + "\n")
    event_log.append(msg)
    if len(event_log) > LOG_OVERLAY_MAX:
        event_log.pop(0)

# Death counters
orc_deaths   = 0
dwarf_deaths = 0

turn_history, orc_history, dwarf_history = [], [], []
day = True
turn_counter = 0
paused = False
fast_mode = False  # when True simulation runs at FAST_FPS
show_heatmap = SHOW_HEATMAP
weather_state = "clear"
last_weather_change = 0

# Game-over state
game_over = False
game_over_message = ""

# --- Core functions ---

def switch_roles():
    """Swap predator/prey roles for day/night."""
    global day
    day = not day
    for a in agents:
        a.is_predator = day if isinstance(a, Orc) else not day

def update_weather():
    """Randomly change weather after an interval."""
    global weather_state, last_weather_change
    if turn_counter - last_weather_change >= WEATHER_CHANGE_INTERVAL:
        weather_state = random.choice(WEATHER_STATES)
        last_weather_change = turn_counter

def count_pack_members(agent):
    """Number of allied predators near the agent."""
    return sum(
        1
        for other in agents
        if other.alive and other.is_predator and other != agent and agent.distance_to(other) <= PACK_RADIUS
    )

def find_closest_enemy(agent, lst, enemy_flag):
    """Return nearest opposing agent from a list."""
    cands = [a for a in lst if a.alive and a.is_predator == enemy_flag]
    return min(cands, key=lambda e: agent.distance_to(e)) if cands else None

def reinforcement_event():
    """Give energy boost and spawn new agents."""
    global orcs, dwarves
    for a in agents:
        if a.alive:
            a.energy += REINFORCEMENT_ENERGY_BOOST
    for _ in range(REINFORCEMENT_NEW_ORCS):
        agents.append(Orc(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE), INITIAL_PREDATOR_ENERGY))
    for _ in range(REINFORCEMENT_NEW_DWARVES):
        agents.append(Dwarf(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE), INITIAL_PREY_ENERGY))
    log_event(f"Turn {turn_counter}: Reinforcement")
    orcs    = [x for x in agents if isinstance(x, Orc)]
    dwarves = [x for x in agents if isinstance(x, Dwarf)]

def update_agents():
    """Move agents and handle energy/aging."""
    global heatmap, orc_deaths, dwarf_deaths
    heatmap = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
    for a in agents:
        if not a.alive:
            continue
        old_x, old_y = a.x, a.y

        a.update_age_energy_trail()
        extra_loss = 0
        if weather_state == "rain":
            extra_loss = RAIN_ENERGY_LOSS_INCREASE
        elif weather_state == "storm":
            extra_loss = STORM_ENERGY_LOSS_INCREASE
        loss_mult = DAY_TEMP_MULTIPLIER if day else NIGHT_TEMP_MULTIPLIER

        if a.is_predator:
            tgt = find_closest_enemy(a, agents, False)
            if tgt and a.distance_to(tgt) <= a.vision_radius:
                if not (weather_state=="storm" and random.random()<STORM_MOVEMENT_SLOWDOWN):
                    a.move_toward(tgt)
            else:
                a.move_random()
            a.energy -= (PREDATOR_ENERGY_LOSS + extra_loss) * loss_mult
        else:
            thr = find_closest_enemy(a, agents, True)
            if thr and a.distance_to(thr) <= a.vision_radius:
                a.move_away_from(thr)
            else:
                a.move_random()
            a.energy -= (PREY_ENERGY_LOSS + extra_loss) * loss_mult

        if (a.x, a.y) in obstacles:
            a.x, a.y = old_x, old_y

        heatmap[a.x][a.y] += 1

        if (a.x, a.y) in resource_nodes:
            gain = RESOURCE_NODE_ENERGY * (1.5 if isinstance(a, Dwarf) else 1.0)
            a.energy += gain
            resource_nodes.remove((a.x, a.y))
            log_event(f"Turn {turn_counter}: Resource @({a.x},{a.y}) +{gain:.1f}")

        if a.alive and a.energy <= 0:
            a.alive = False
            if isinstance(a, Orc):
                orc_deaths += 1
            else:
                dwarf_deaths += 1
            if death_sound:
                death_sound.play()
            log_event(f"Turn {turn_counter}: {'Orc' if isinstance(a,Orc) else 'Dwarf'} died @({a.x},{a.y})")

        a.update_animation()

kill_particles = []
def spawn_kill_particles(cx, cy):
    """Create particle effects at a location."""
    for _ in range(KILL_PARTICLE_COUNT):
        kill_particles.append({
            "x": cx*CELL_SIZE + CELL_SIZE//2,
            "y": cy*CELL_SIZE + CELL_SIZE//2,
            "dx": random.uniform(-1,1)*CELL_SIZE/10,
            "dy": random.uniform(-1,1)*CELL_SIZE/10,
            "life": KILL_PARTICLE_LIFETIME
        })

def update_kill_particles(dt):
    """Advance particle animations."""
    for p in kill_particles[:]:
        p["x"] += p["dx"]
        p["y"] += p["dy"]
        p["life"] -= dt
        if p["life"] <= 0:
            kill_particles.remove(p)

def draw_kill_particles():
    """Render active kill particles."""
    for p in kill_particles:
        alpha = int(255 * (p["life"]/KILL_PARTICLE_LIFETIME))
        surf = pygame.Surface((4,4), pygame.SRCALPHA)
        surf.fill((255,255,0,alpha))
        screen.blit(surf, (p["x"], p["y"]))

def check_interactions():
    """Resolve predator-prey collisions."""
    global orc_deaths, dwarf_deaths
    for predator in [a for a in agents if a.alive and a.is_predator]:
        for prey in [a for a in agents if a.alive and not a.is_predator]:
            if predator.x == prey.x and predator.y == prey.y:
                prob = predator.energy / (predator.energy + prey.energy + 1e-6)
                if random.random() < prob:
                    prey.alive = False
                    dwarf_deaths += 1
                    bonus = 1 + PACK_ENERGY_BONUS_MULTIPLIER * count_pack_members(predator)
                    predator.energy += PREDATOR_ENERGY_GAIN * bonus
                    if attack_sound: attack_sound.play()
                    log_event(f"Turn {turn_counter}: Kill @({predator.x},{predator.y}) bonus {bonus:.2f}")
                    spawn_kill_particles(predator.x, predator.y)
                else:
                    predator.alive = False
                    orc_deaths += 1
                    if death_sound: death_sound.play()
                    log_event(f"Turn {turn_counter}: Predator fell @({predator.x},{predator.y})")
                break

def reproduce_agents():
    """Handle reproduction with trait mutation."""
    global orcs, dwarves
    new_agents = []
    for a in agents:
        if not a.alive:
            continue
        if isinstance(a, Dwarf) and a.energy >= DWARF_REPRODUCTION_THRESHOLD:
            off = int(a.energy * (1 - DWARF_REPRODUCTION_COST))
            a.energy = int(a.energy * DWARF_REPRODUCTION_COST)
            child_speed = mutate_trait(a.speed, DWARF_MIN_SPEED, DWARF_MAX_SPEED)
            child_vis   = mutate_trait(a.vision_radius, DWARF_MIN_VISION_RADIUS, DWARF_MAX_VISION_RADIUS)
            new_agents.append(Dwarf(a.x, a.y, off, child_speed, child_vis))
            if repro_sound: repro_sound.play()
            log_event(f"Turn {turn_counter}: Dwarf reproduced @({a.x},{a.y})")
        elif isinstance(a, Orc) and a.energy >= REPRODUCTION_THRESHOLD:
            off = a.energy // 2
            a.energy //= 2
            child_speed = mutate_trait(a.speed, ORC_MIN_SPEED, ORC_MAX_SPEED)
            child_vis   = mutate_trait(a.vision_radius, ORC_MIN_VISION_RADIUS, ORC_MAX_VISION_RADIUS)
            new_agents.append(Orc(a.x, a.y, off, child_speed, child_vis))
            if repro_sound: repro_sound.play()
            log_event(f"Turn {turn_counter}: Orc reproduced @({a.x},{a.y})")
    agents.extend(new_agents)
    orcs    = [x for x in agents if isinstance(x, Orc)]
    dwarves = [x for x in agents if isinstance(x, Dwarf)]

def update_resources():
    """Respawn resource nodes periodically."""
    global last_resource_spawn
    if turn_counter - last_resource_spawn >= RESOURCE_NODE_RESPAWN_INTERVAL:
        while len(resource_nodes) < RESOURCE_NODE_COUNT:
            resource_nodes.append((random.randrange(GRID_SIZE), random.randrange(GRID_SIZE)))
        last_resource_spawn = turn_counter

def draw_minimap():
    """Render small map showing agent positions."""
    size = int(GRID_SIZE * CELL_SIZE * MINIMAP_SCALE)
    m = pygame.Surface((size, size))
    m.fill((0,0,0))
    scale = MINIMAP_SCALE * CELL_SIZE
    for ox, oy in obstacles:
        pygame.draw.rect(m, OBSTACLE_COLOR, (int(ox*scale), int(oy*scale), int(scale), int(scale)))
    for a in agents:
        if not a.alive: continue
        col = ORC_COLOR if isinstance(a, Orc) else DWARF_COLOR
        pygame.draw.rect(m, col, (int(a.x*scale), int(a.y*scale), 2, 2))
    screen.blit(m, (WINDOW_WIDTH - size - MINIMAP_PADDING, MINIMAP_PADDING))

def draw_event_log():
    """Display recent events in the corner."""
    font = pygame.font.SysFont(None, 18)
    ow = WINDOW_WIDTH // 3
    oh = LOG_OVERLAY_MAX * 18 + 8
    surf = pygame.Surface((ow, oh), pygame.SRCALPHA)
    surf.fill((0,0,0,150))
    for i, msg in enumerate(event_log):
        line = font.render(msg[-30:], True, UI_FONT_COLOR)
        surf.blit(line, (4, 4 + i*18))
    screen.blit(surf, (10, 10))

def draw_grid():
    """Draw world tiles, effects and agents."""
    bg = DAY_BG_COLOR if day else NIGHT_BG_COLOR
    if weather_state == "storm":
        bg = (20,20,60)
    screen.fill(bg)

    if weather_state == "rain":
        for _ in range(50):
            x = random.randrange(WINDOW_WIDTH)
            y = random.randrange(WINDOW_HEIGHT)
            pygame.draw.line(screen, (180,180,255), (x,y), (x,y+5))

    if show_heatmap:
        m_h = max(max(row) for row in heatmap) or 1
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if heatmap[i][j]:
                    inten = min(255, int(heatmap[i][j]/m_h*255))
                    s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    s.fill((inten, 0, 0, 100))
                    screen.blit(s, (i*CELL_SIZE, j*CELL_SIZE))

    for rx, ry in resource_nodes:
        pygame.draw.circle(screen, (0,255,0),
                           (rx*CELL_SIZE + CELL_SIZE//2, ry*CELL_SIZE + CELL_SIZE//2),
                           CELL_SIZE//3)

    for ox, oy in obstacles:
        pygame.draw.rect(screen, OBSTACLE_COLOR,
                         (ox*CELL_SIZE, oy*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for a in agents:
        if not a.alive: continue
        a.draw_trail(screen)
        xpix, ypix = int(a.pos_x), int(a.pos_y)
        img = orc_img if isinstance(a, Orc) else dwarf_img
        screen.blit(img, (xpix, ypix))
        if a.is_predator:
            pygame.draw.rect(screen, PREDATOR_HIGHLIGHT,
                             (xpix, ypix, CELL_SIZE, CELL_SIZE), 2)

        bar_y = ypix - HEALTH_BAR_HEIGHT - 2
        max_e = REPRODUCTION_THRESHOLD if isinstance(a, Orc) else DWARF_REPRODUCTION_THRESHOLD
        ratio = max(0.0, min(a.energy / max_e, 1.0))
        bg_rect = pygame.Rect(xpix, bar_y, CELL_SIZE, HEALTH_BAR_HEIGHT)
        fg_rect = pygame.Rect(xpix, bar_y, int(CELL_SIZE * ratio), HEALTH_BAR_HEIGHT)
        pygame.draw.rect(screen, (50,50,50), bg_rect)
        color = (int(255*(1-ratio)), int(255*ratio), 0)
        pygame.draw.rect(screen, color, fg_rect)

    draw_kill_particles()
    draw_minimap()
    draw_event_log()

def draw_ui():
    """Render status bars and history graph."""
    font = pygame.font.SysFont(None, 24)
    oa = sum(1 for a in agents if isinstance(a, Orc) and a.alive)
    da = sum(1 for a in agents if isinstance(a, Dwarf) and a.alive)
    save_high_score(oa + da)
    rin = max(0, RESOURCE_RESPAWN_TIMER - (turn_counter - last_resource_spawn))
    status = (f"Turn:{turn_counter} "
              f"OrcsAlive:{oa} OrcsDead:{orc_deaths} "
              f"DwarvesAlive:{da} DwarvesDead:{dwarf_deaths} "
              f"Day:{day} Weather:{weather_state} "
              f"Paused:{paused} Fast:{fast_mode} Heatmap:{show_heatmap} "
              f"NextRes:{rin} HighScore:{high_score}")
    screen.blit(font.render(status, True, UI_FONT_COLOR),
                (10, GRID_SIZE*CELL_SIZE + 10))
    fps_text = font.render(f"FPS:{int(clock.get_fps())}", True, UI_FONT_COLOR)
    screen.blit(fps_text, (WINDOW_WIDTH - 100, GRID_SIZE*CELL_SIZE + 50))

    # History chart
    turn_history.append(turn_counter)
    orc_history.append(oa)
    dwarf_history.append(da)
    top = GRID_SIZE*CELL_SIZE + UI_HEIGHT
    bot = top + CHART_HEIGHT
    pygame.draw.line(screen, UI_FONT_COLOR, (10, bot-10), (WINDOW_WIDTH-10, bot-10), 1)
    pygame.draw.line(screen, UI_FONT_COLOR, (10, top+10), (10, bot-10), 1)
    if turn_history:
        m = max(max(orc_history), max(dwarf_history), 1)
        pts_o, pts_d = [], []
        for i, t in enumerate(turn_history):
            x = 10 + (t/turn_history[-1])*(WINDOW_WIDTH-20)
            y_o = bot-10 - (orc_history[i]/m)*(CHART_HEIGHT-20)
            y_d = bot-10 - (dwarf_history[i]/m)*(CHART_HEIGHT-20)
            pts_o.append((x,y_o))
            pts_d.append((x,y_d))
        if len(pts_o) > 1:
            pygame.draw.lines(screen, ORC_COLOR, False, pts_o, 2)
            pygame.draw.lines(screen, DWARF_COLOR, False, pts_d, 2)

def draw_game_over():
    """Overlay game-over message."""
    font = pygame.font.SysFont(None, 48)
    text = font.render(game_over_message, True, (255,255,255))
    rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
    overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
    overlay.fill((0,0,0,180))
    screen.blit(overlay, (0,0))
    screen.blit(text, rect)

# Start
switch_roles()

running = True
while running:
    clock.tick(FAST_FPS if fast_mode else FPS)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                paused = not paused
            if e.key == pygame.K_h:
                show_heatmap = not show_heatmap
            if e.key == pygame.K_m:
                music_on = not music_on
                vol = 1.0 if music_on else 0.0
                mixer.music.set_volume(vol)
                for s in (attack_sound, death_sound, repro_sound):
                    if s: s.set_volume(vol)
            if e.key == pygame.K_f:
                fast_mode = not fast_mode
            if e.key == pygame.K_r:
                # Anında reinforcement
                reinforcement_event()

    if not paused:
        turn_counter += 1

        # Dynamic reinforcement: slows every 500 turns
        phase    = turn_counter // 500
        interval = REINFORCEMENT_INTERVAL * (1 + phase)
        if turn_counter % interval == 0:
            reinforcement_event()

        if turn_counter % DAY_DURATION == 0:
            switch_roles()
        update_weather()
        update_agents()
        check_interactions()
        reproduce_agents()
        update_resources()
        update_kill_particles(clock.get_time()/1000.0)

        # Game-over check
        oa = sum(1 for a in agents if isinstance(a, Orc)   and a.alive)
        da = sum(1 for a in agents if isinstance(a, Dwarf) and a.alive)
        if not game_over and (oa == 0 or da == 0 or turn_counter >= MAX_TURNS):
            game_over = True
            paused = True
            if oa == 0 and da == 0:
                game_over_message = "Draw — all perished!"
            elif oa == 0:
                game_over_message = "Dwarves Win!"
            elif da == 0:
                game_over_message = "Orcs Win!"
            else:
                game_over_message = f"Draw — reached {MAX_TURNS} turns!"
            log_event(f"Game Over: {game_over_message}")

    draw_grid()
    draw_ui()
    if game_over:
        draw_game_over()
    pygame.display.flip()

pygame.quit()
