from sb3_contrib import MaskablePPO
import supersuit as ss

# Absolute imports allow running this script directly with ``python main.py``
# while still functioning when used as a module via ``python -m orc_dwarf_rl.main``.
from orc_dwarf_rl.orc_dwarf_env import OrcDwarfEnv
from orc_dwarf_rl.config import LEARNING_RATE, NUM_ORCS, NUM_DWARFS


def train(total_timesteps=200000):
    env = OrcDwarfEnv(num_orcs=NUM_ORCS, num_dwarfs=NUM_DWARFS)
    env = ss.pad_observations_v0(env)
    env = ss.pad_action_space_v0(env)
    model = MaskablePPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=LEARNING_RATE,
        verbose=1,
    )
    model.learn(total_timesteps=total_timesteps)
    model.save("orc_dwarf_model")
    return model


def evaluate(model_path="orc_dwarf_model", episodes=5):
    model = MaskablePPO.load(model_path)
    env = OrcDwarfEnv()
    env = ss.pad_observations_v0(env)
    env = ss.pad_action_space_v0(env)
    for ep in range(episodes):
        observations = env.reset()
        terminated = {a: False for a in env.agents}
        truncated = {a: False for a in env.agents}
        while env.agents:
            actions = {a: model.predict(observations[a], deterministic=True)[0] for a in env.agents}
            observations, rewards, terminations, truncations, infos = env.step(actions)
            terminated.update(terminations)
            truncated.update(truncations)
            env.render()
            if all(terminated.get(a, False) or truncated.get(a, False) for a in terminated):
                break
        print(f"Episode {ep+1} finished")
    env.close()


if __name__ == "__main__":
    model = train()
    evaluate()
