# main.py

import os
import random
import math
import pygame
from pygame import mixer
from config import *
from agent import Orc, Dwarf

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
    global high_score
    if score > high_score:
        high_score = score
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(high_score))

# Initialize world
orcs    = [Orc(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE), INITIAL_PREDATOR_ENERGY)
           for _ in range(NUM_ORCS)]
dwarves = [Dwarf(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE), INITIAL_PREY_ENERGY)
           for _ in range(NUM_DWARVES)]
agents  = orcs + dwarves

obstacles = [(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE))
             for _ in range(OBSTACLE_COUNT)]
heatmap = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
resource_nodes = [(random.randrange(GRID_SIZE), random.randrange(GRID_SIZE))
                  for _ in range(RESOURCE_NODE_COUNT)]
last_resource_spawn = 0
kill_particles = []

# RL environment wrapper
class RLEnv:
    def __init__(self, agents, resource_nodes):
        self.agents = agents
        self.resource_nodes = resource_nodes

    def find_nearest(self, agent, food=False, species=None, radius=None):
        if food:
            if not self.resource_nodes: return None
            return min(self.resource_nodes,
                       key=lambda pos: abs(pos[0]-agent.x)+abs(pos[1]-agent.y))
        if species:
            candidates = [a2 for a2 in self.agents
                          if a2.alive and ((species=="Orc" and isinstance(a2,Orc))
                                           or (species=="Dwarf" and isinstance(a2,Dwarf)))]
            if not candidates: return None
            best = min(candidates, key=lambda a2: abs(a2.x-agent.x)+abs(a2.y-agent.y))
            return (best.x, best.y)
        return None

    def try_eat(self, agent):
        pos = (agent.x, agent.y)
        if pos in self.resource_nodes:
            self.resource_nodes.remove(pos)
            return True
        return False

    def reproduce(self, agent):
        if isinstance(agent, Orc):
            child = Orc(agent.x, agent.y, agent.energy//2)
            agent.energy //= 2
        else:
            cost = int(agent.energy * DWARF_REPRODUCTION_COST)
            child_energy = agent.energy - cost
            agent.energy = cost
            child = Dwarf(agent.x, agent.y, child_energy)
        self.agents.append(child)
        if repro_sound:
            repro_sound.play()

# Event log
event_log = []
log_filename = "log.txt"
if os.path.exists(log_filename):
    os.remove(log_filename)

def log_event(msg):
    with open(log_filename, "a") as f:
        f.write(msg + "\n")
    event_log.append(msg)
    if len(event_log) > LOG_OVERLAY_MAX:
        event_log.pop(0)

# Counters & state
orc_deaths = 0
dwarf_deaths = 0
turn_history, orc_history, dwarf_history = [], [], []
day = True
turn_counter = 0
paused = False
show_heatmap = SHOW_HEATMAP
weather_state = "clear"
last_weather_change = 0
game_over = False
game_over_message = ""

# Utility functions
def switch_roles():
    global day
    day = not day
    for a in agents:
        a.is_predator = day if isinstance(a, Orc) else not day

def update_weather():
    global weather_state, last_weather_change
    if turn_counter - last_weather_change >= WEATHER_CHANGE_INTERVAL:
        weather_state = random.choice(WEATHER_STATES)
        last_weather_change = turn_counter

def check_interactions():
    global orc_deaths, dwarf_deaths
    for pred in [a for a in agents if a.alive and a.is_predator]:
        for prey in [a for a in agents if a.alive and not a.is_predator]:
            if pred.x==prey.x and pred.y==prey.y:
                prob = pred.energy/(pred.energy+prey.energy+1e-6)
                if random.random()<prob:
                    prey.alive=False
                    dwarf_deaths+=1
                    bonus = 1 + PACK_ENERGY_BONUS_MULTIPLIER * sum(
                        1 for a in agents if a.is_predator and a.x==pred.x and a.y==pred.y
                    )
                    pred.energy+=PREDATOR_ENERGY_GAIN*bonus
                    if attack_sound: attack_sound.play()
                    log_event(f"Turn {turn_counter}: Kill at {pred.x},{pred.y} bonus {bonus:.2f}")
                    spawn_kill_particles(pred.x, pred.y)
                else:
                    pred.alive=False
                    orc_deaths+=1
                    if death_sound: death_sound.play()
                    log_event(f"Turn {turn_counter}: Predator fell at {pred.x},{pred.y}")
                break

def spawn_kill_particles(x, y):
    for _ in range(KILL_PARTICLE_COUNT):
        ang = random.uniform(0,2*math.pi)
        spd = random.uniform(0.5,1.5)
        kill_particles.append({
            "x": x*CELL_SIZE, "y": y*CELL_SIZE,
            "dx": math.cos(ang)*spd, "dy": math.sin(ang)*spd,
            "life": KILL_PARTICLE_LIFETIME
        })

def update_resources():
    global last_resource_spawn
    if turn_counter - last_resource_spawn >= RESOURCE_NODE_RESPAWN_INTERVAL:
        while len(resource_nodes)<RESOURCE_NODE_COUNT:
            resource_nodes.append((random.randrange(GRID_SIZE), random.randrange(GRID_SIZE)))
        last_resource_spawn = turn_counter

def update_kill_particles(dt):
    for p in kill_particles[:]:
        p["x"]+=p["dx"]
        p["y"]+=p["dy"]
        p["life"]-=dt
        if p["life"]<=0:
            kill_particles.remove(p)

def draw_grid():
    bg = DAY_BG_COLOR if day else NIGHT_BG_COLOR
    if weather_state=="storm":
        bg=(20,20,60)
    screen.fill(bg)
    if weather_state=="rain":
        for _ in range(50):
            x,y = random.randrange(WINDOW_WIDTH), random.randrange(WINDOW_HEIGHT)
            pygame.draw.line(screen,(180,180,255),(x,y),(x,y+5))
    if show_heatmap:
        m = max(max(row) for row in heatmap) or 1
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if heatmap[i][j]:
                    inten = min(255,int(heatmap[i][j]/m*255))
                    s=pygame.Surface((CELL_SIZE,CELL_SIZE),pygame.SRCALPHA)
                    s.fill((inten,0,0,100))
                    screen.blit(s,(i*CELL_SIZE,j*CELL_SIZE))
    for rx,ry in resource_nodes:
        pygame.draw.circle(screen,(0,255,0),
                           (rx*CELL_SIZE+CELL_SIZE//2,ry*CELL_SIZE+CELL_SIZE//2),
                           CELL_SIZE//3)
    for ox,oy in obstacles:
        pygame.draw.rect(screen,OBSTACLE_COLOR,
                         (ox*CELL_SIZE,oy*CELL_SIZE,CELL_SIZE,CELL_SIZE))
    for a in agents:
        if not a.alive: continue
        a.draw_trail(screen)
        # draw at actual grid coords
        xpix, ypix = a.x*CELL_SIZE, a.y*CELL_SIZE
        img = orc_img if isinstance(a,Orc) else dwarf_img
        screen.blit(img,(xpix,ypix))
        if a.is_predator:
            pygame.draw.rect(screen,PREDATOR_HIGHLIGHT,
                             (xpix,ypix,CELL_SIZE,CELL_SIZE),2)
        # health bar
        bar_y = ypix - HEALTH_BAR_HEIGHT - 2
        max_e = REPRODUCTION_THRESHOLD if isinstance(a,Orc) else DWARF_REPRODUCTION_THRESHOLD
        ratio = max(0.0, min(a.energy/max_e,1.0))
        bg_r = pygame.Rect(xpix,bar_y,CELL_SIZE,HEALTH_BAR_HEIGHT)
        fg_r = pygame.Rect(xpix,bar_y,int(CELL_SIZE*ratio),HEALTH_BAR_HEIGHT)
        pygame.draw.rect(screen,(50,50,50),bg_r)
        color=(int(255*(1-ratio)),int(255*ratio),0)
        pygame.draw.rect(screen,color,fg_r)

def draw_ui():
    font = pygame.font.SysFont(None,24)
    oa = sum(1 for a in agents if isinstance(a,Orc) and a.alive)
    da = sum(1 for a in agents if isinstance(a,Dwarf) and a.alive)
    save_high_score(oa+da)
    rin = max(0, RESOURCE_RESPAWN_TIMER - (turn_counter - last_resource_spawn))
    status = (f"Turn:{turn_counter} Orcs:{oa}/{orc_deaths} "
              f"Dwarves:{da}/{dwarf_deaths} Day:{day} "
              f"Weather:{weather_state} Heatmap:{show_heatmap} "
              f"NextRes:{rin} HighScore:{high_score}")
    screen.blit(font.render(status,True,UI_FONT_COLOR),
                (10,GRID_SIZE*CELL_SIZE+10))
    fps_t = font.render(f"FPS:{int(clock.get_fps())}",True,UI_FONT_COLOR)
    screen.blit(fps_t,(WINDOW_WIDTH-100,GRID_SIZE*CELL_SIZE+50))
    # bottom chart
    top = GRID_SIZE*CELL_SIZE+UI_HEIGHT
    bot = top+CHART_HEIGHT
    pygame.draw.line(screen,UI_FONT_COLOR,(10,bot-10),(WINDOW_WIDTH-10,bot-10),1)
    pygame.draw.line(screen,UI_FONT_COLOR,(10,top+10),(10,bot-10),1)
    if turn_history:
        m = max(max(orc_history),max(dwarf_history),1)
        pts_o=[]; pts_d=[]
        for i,t in enumerate(turn_history):
            x = 10 + (t/turn_history[-1])*(WINDOW_WIDTH-20)
            y_o = bot-10 - (orc_history[i]/m)*(CHART_HEIGHT-20)
            y_d = bot-10 - (dwarf_history[i]/m)*(CHART_HEIGHT-20)
            pts_o.append((x,y_o)); pts_d.append((x,y_d))
        if len(pts_o)>1:
            pygame.draw.lines(screen,ORC_COLOR,False,pts_o,2)
            pygame.draw.lines(screen,DWARF_COLOR,False,pts_d,2)

def draw_game_over():
    font = pygame.font.SysFont(None,48)
    text = font.render(game_over_message,True,(255,255,255))
    rect = text.get_rect(center=(WINDOW_WIDTH//2,WINDOW_HEIGHT//2))
    overlay = pygame.Surface(WINDOW_SIZE,pygame.SRCALPHA)
    overlay.fill((0,0,0,180))
    screen.blit(overlay,(0,0))
    screen.blit(text,rect)

# start
switch_roles()

running = True
while running:
    clock.tick(FPS)
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False
        elif e.type==pygame.KEYDOWN:
            if e.key==pygame.K_p:
                paused=not paused
            elif e.key==pygame.K_h:
                show_heatmap=not show_heatmap
            elif e.key==pygame.K_m:
                if mixer.music.get_busy():
                    mixer.music.pause()
                else:
                    mixer.music.unpause()

    if not paused and not game_over:
        turn_counter+=1
        if turn_counter % DAY_DURATION==0:
            switch_roles()
        update_weather()

        # Q-learning step
        env = RLEnv(agents, resource_nodes)
        for a in agents:
            if a.alive:
                a.act(env)
                # optional smooth animation:
                a.update_animation()

        check_interactions()
        update_resources()
        update_kill_particles(clock.get_time()/1000.0)

        # check end
        if all(not a.alive for a in orcs) or all(not a.alive for a in dwarves):
            game_over=True
            winner = "Dwarves" if any(a.alive for a in dwarves) else "Orcs"
            game_over_message = f"{winner} win in {turn_counter} turns"

        turn_history.append(turn_counter)
        orc_history.append(sum(1 for a in agents if isinstance(a,Orc) and a.alive))
        dwarf_history.append(sum(1 for a in agents if isinstance(a,Dwarf) and a.alive))

    draw_grid()
    draw_ui()
    if game_over:
        draw_game_over()
    pygame.display.flip()

pygame.quit()
