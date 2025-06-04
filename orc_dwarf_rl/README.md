# Orc-Dwarf Reinforcement Learning

This folder contains a simplified multi-agent RL setup using [PettingZoo](https://pettingzoo.farama.org/) and `sb3_contrib`.
The environment is built on top of PettingZoo's `ParallelEnv` API.  Older
releases of this repository relied on the deprecated `parallel_base_env`
interface, so make sure you have an up to date copy of the code if you see
import errors regarding `parallel_base_env`.

## Installation
```bash
pip install -r requirements.txt
```

## Training
Run `python -m orc_dwarf_rl.main` from the project root to train agents in the environment. The script will save a model named `orc_dwarf_model`.

If you want to interact with the environment directly, run `python -m orc_dwarf_rl.orc_dwarf_env`. Executing the modules in this way ensures Python treats `orc_dwarf_rl` as a package and avoids `ModuleNotFoundError` issues.

## Evaluation
After training, the script automatically runs a short evaluation showing a simple ASCII rendering of the grid.

You can also call `orc_dwarf_rl.main.evaluate("orc_dwarf_model", episodes=3)` in Python to evaluate separately.
