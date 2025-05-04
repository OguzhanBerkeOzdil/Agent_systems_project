# Agent Simulation

## Version 1

* **Grid-Based Predator–Prey**: Orcs (predators) and Dwarves (prey) move on a fixed 30×30 grid with simple chase/flee logic.
* **Uniform Vision**: All agents share a single global sight radius; no per-agent variation.
* **Fixed Reinforcement**: Every 50 turns all living agents gain energy and new agents spawn.
* **Resource Nodes & Weather**: Static energy pickups; three weather states (Clear/Rain/Storm) that modify energy loss and movement.
* **Pack Bonus & Reproduction**: Predators earn extra energy based on nearby pack members and reproduce when energy thresholds are reached.
* **Day/Night Role Swap**: Predator/prey roles switch after each day cycle.
* **Core Simulation Only**: No UI overlays, visual effects, or camera controls.

## Version 2 (Enhancements)

### New Gameplay Features

* **Per-Agent Vision Radius**: Each Orc and Dwarf now has an individual, randomized sight distance for varied behaviors.
* **Maximum Age & Natural Death**: Agents age each turn and die upon exceeding a configurable `MAX_AGE`.
* **Dynamic Reinforcement Rate**: Initial reinforcement every 50 turns, then slows by +50-turn phases every 500 turns (50→100→150…).
* **Resource Respawn**: Collected nodes respawn at set intervals to keep the world replenished.
* **Pack Energy Bonus**: Predators earn extra energy proportional to pack size on kills.
* **Agent Trails**: Fading trails show recent movement paths for each agent.

### UI & Visual Enhancements

* **Health Bars**: Energy bars above sprites indicate current health (red→green).
* **Event Log Overlay**: Top-left panel lists recent kills, deaths, resource pickups, and reinforcements.
* **Population History Chart**: Bottom UI line graph tracks live counts of Orcs and Dwarves over time.
* **Minimap**: Corner map displays all agents and obstacles at a glance.
* **Kill Particle Effects**: Brief yellow burst on agent death adds visual flair.
* **Heatmap Toggle**: Press `H` to overlay movement frequency heatmap across the grid.
* **FPS Counter**: Real-time frame-rate display in the UI.

### Sound & Controls

* **Mute/Unmute (M)**: Toggle all music and sound effects instantly.
* **Manual Reinforcement (R)**: Trigger a reinforcement event on demand.
* **Pause/Resume (P)**: Freeze or continue the simulation.
* **Heatmap Toggle (H)**: Show/hide activity heatmap overlay.
* **Key Bindings Summary**:

  * `P` – Pause/Resume
  * `H` – Toggle Heatmap
  * `M` – Mute/Unmute Audio
  * `R` – Instant Reinforcement

---

*This README outlines the base features (Version 1) and all enhancements added in Version 2.*
