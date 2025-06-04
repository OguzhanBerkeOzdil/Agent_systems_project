<<<<<<< HEAD
# orc_dwarf_rl/main.py

import os
from stable_baselines3 import PPO
import supersuit as ss
import torch

from config import (
    NUM_ORCS,
    NUM_DWARFS,
    LEARNING_RATE,
    TOTAL_TIMESTEPS,
    EVAL_EPISODES,
    ENV_RENDER,
)

from orc_dwarf_env import OrcDwarfEnv


def make_vec_env():
    """
    1) PettingZoo ParallelEnv oluşturur.
    2) Supersuit ile gözlem ve aksiyon alanlarını pad eder.
    3) Ölüm (agent death) durumunu sabitlemek için black_death_v3 uygular.
    4) PettingZoo → VecEnv (Gym) dönüşümü yapar.
    5) VecEnv’leri birleştirip PPO’nun beklentisine uygun hale getirir.
    """
    env = OrcDwarfEnv(num_orcs=NUM_ORCS, num_dwarfs=NUM_DWARFS)
    env = ss.pad_observations_v0(env)
    env = ss.pad_action_space_v0(env)

    # Ölüm sonrası agent’ı “neredeyse var, ama ölü” göstermek için:
    env = ss.black_death_v3(env)

    env = ss.pettingzoo_env_to_vec_env_v1(env)
    env = ss.concat_vec_envs_v1(env, 1, 1, base_class="stable_baselines3")
    return env


def train():
    """
    PPO kullanarak eğitimi başlatır ve modeli kaydeder.
    """
    vec_env = make_vec_env()

    model = PPO(
        policy="MlpPolicy",
        env=vec_env,
        learning_rate=LEARNING_RATE,
        verbose=1,
        device="cuda",  # CPU veya GPU otomatik seçer
    )

    model.learn(total_timesteps=TOTAL_TIMESTEPS)

    save_path = os.path.join(os.getcwd(), "orc_dwarf_model")
    model.save(save_path)
    print(f"[INFO] Model kaydedildi: {save_path}.zip")
    return model


def evaluate(model_path=None):
    """
    Eğitilmiş PPO modelini yükler, aynı VecEnv’i yeniden oluşturur
    ve belirtilen sayıda bölüm (episode) “deterministic” olarak oynatıp render eder.
    """
    if model_path is None:
        model_path = os.path.join(os.getcwd(), "orc_dwarf_model.zip")

    model = PPO.load(model_path, device="cpu")
    vec_env = make_vec_env()

    for ep in range(1, EVAL_EPISODES + 1):
        # reset()'in döndürdüğü değeri kontrol edip sadece gözlemi (obs) alıyoruz
        reset_out = vec_env.reset()
        if isinstance(reset_out, tuple):
            obs = reset_out[0]
        else:
            obs = reset_out

        done = False

        print(f"[EVALUATE] Bölüm {ep} başlıyor...")
        while not done:
            action_array, _ = model.predict(obs, deterministic=True)

            step_out = vec_env.step(action_array)
            # step_out uzunluğunu kontrol edip uygun şekilde işliyoruz:
            if len(step_out) == 5:
                obs, rewards, terminations, truncations, infos = step_out
                # Tüm ajanlar terminate ya da truncate oldu mu kontrolü:
                term_dict = terminations[0]
                trunc_dict = truncations[0]
                done = all(term_dict.values()) or all(trunc_dict.values())
            else:
                # 4 değer dönerse: (obs, rewards, dones, infos)
                obs, rewards, done_arr, infos = step_out
                done = bool(done_arr[0])

            if ENV_RENDER:
                vec_env.render()

        print(f"[EVALUATE] Bölüm {ep} tamamlandı.\n")

    vec_env.close()


if __name__ == "__main__":
    _ = train()
=======
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
>>>>>>> 44018d4f7d167cddd0fc021a73e5e37e0a612004
    evaluate()
