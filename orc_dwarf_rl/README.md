# Orc-Dwarf Reinforcement Learning

This folder contains a simplified multi-agent RL setup using [PettingZoo](https://pettingzoo.farama.org/) and `sb3_contrib`.

## Installation
```bash
pip install -r requirements.txt
```

## Training
Run `python -m orc_dwarf_rl.main` to train agents in the environment. The script will save a model named `orc_dwarf_model`.

## Evaluation
After training, the script automatically runs a short evaluation showing a simple ASCII rendering of the grid.

You can also call `orc_dwarf_rl.main.evaluate("orc_dwarf_model", episodes=3)` in Python to evaluate separately.
