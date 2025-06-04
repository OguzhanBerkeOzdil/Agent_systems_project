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
    evaluate()
