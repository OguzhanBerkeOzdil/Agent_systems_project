"""Configuration for Orc-Dwarf RL environment."""

# Map dimensions
GRID_SIZE = 10

# Agent counts
NUM_ORCS = 5
NUM_DWARFS = 5

# Agent attributes
MAX_ENERGY = 20
INITIAL_ENERGY = 10
DEFAULT_SIGHT = 5
DEFAULT_SPEED = 1
ATTACK_RANGE = 1

# Resources
RESOURCE_NODE_COUNT = 5
RESOURCE_ENERGY = 5

# Episode settings
MAX_STEPS = 500

# Reinforcement learning hyperparameters
LEARNING_RATE = 3e-4
GAMMA = 0.99
BATCH_SIZE = 64

# Training / Evaluation settings
TOTAL_TIMESTEPS = 200_000   # Number of steps for SB3 training
EVAL_EPISODES = 5           # Episodes for evaluation after training
ENV_RENDER = True           # Render ASCII grid during evaluation
