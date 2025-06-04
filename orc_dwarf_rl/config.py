<<<<<<< HEAD
=======
# Configuration for Orc-Dwarf RL environment

>>>>>>> 44018d4f7d167cddd0fc021a73e5e37e0a612004
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
<<<<<<< HEAD

# Training / Evaluation settings
TOTAL_TIMESTEPS = 200_000   # SB3’e iletilecek toplam adım sayısı
EVAL_EPISODES   =   5       # Eğitim sonrası kaç bölüm değerlendirmesi isteniyor
ENV_RENDER      = True      # Değerlendirme sırasında ASCII render yapmak istersek
=======
>>>>>>> 44018d4f7d167cddd0fc021a73e5e37e0a612004
