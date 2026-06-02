import ast
import json
import re
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "v6.5_multiseed_albation.ipynb"
OUT = ROOT / "v6.6.ipynb"


def as_source(text):
    text = textwrap.dedent(text).strip("\n") + "\n"
    return text.splitlines(keepends=True)


def cell_text(nb, index):
    return "".join(nb["cells"][index].get("source", []))


def set_cell(nb, index, text):
    nb["cells"][index]["source"] = as_source(text)


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Missing replacement target: {label}")
    return text.replace(old, new, 1)


def regex_replace(text, pattern, repl, label, flags=re.S):
    new_text, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"Regex replacement failed for {label}; count={count}")
    return new_text


def update_runtime_cell(nb):
    src = cell_text(nb, 3)
    src = replace_once(
        src,
        'CACHE_VERSION = "v65_multiseed_ablation_2026_05_21"',
        'CACHE_VERSION = "v66_rebalanced_fed_ddqn_2026_05_22"',
        "cache version",
    )
    insert = """

# v6.6 proposed Fed-DDQN controls.
# The core research model remains Federated DDQN; these flags rebalance how it learns.
PROPOSED_USE_ACTION_AWARE_ENV = False
PROPOSED_USE_PRIORITIZED_REPLAY = False
PROPOSED_MU_PROXIMAL = 0.003
PROPOSED_TARGET_TAU = 0.012
PROPOSED_FEDPROX_INTERVAL = 4
PROPOSED_FEDPROX_MAX_DRIFT = 1.0e4
PROPOSED_EDGE_OVERUSE_SOFT_CAP = 78.0
PROPOSED_HEAVY_TASK_EDGE_PENALTY = True
EVALUATE_FULL_TEST_SPLIT = True
"""
    src = replace_once(
        src,
        'CACHE_VERSION = "v66_rebalanced_fed_ddqn_2026_05_22"\n',
        'CACHE_VERSION = "v66_rebalanced_fed_ddqn_2026_05_22"\n' + textwrap.dedent(insert),
        "v6.6 controls",
    )
    src = src.replace("v6.5 experiment-suite controls.", "v6.6 experiment-suite controls.")
    set_cell(nb, 3, src)


OFFLOAD_ENV = r'''
class OffloadEnv:
    """
    Array-backed offline RL environment for edge/cloud offloading.

    v6.6 changes the proposed Fed-DDQN training target from edge-first behavior
    to evaluation-aligned adaptive offloading. Runtime pressure can still be
    enabled for ablations, but the proposed model defaults to static CSV latency
    because final comparison is also computed on static precomputed test rows.
    """

    HEAVY_TASK_TYPES = {"ai", "video", "image", "firmware_update"}
    URGENT_TASK_TYPES = {"emergency", "voice", "sensor", "telemetry"}

    def __init__(self, task_df: pd.DataFrame, feature_matrix: np.ndarray,
                 action_aware=None, heavy_task_penalty=None):
        self.df = task_df.reset_index(drop=True)
        self.X = np.asarray(feature_matrix, dtype=np.float32)
        self.n = len(self.df)
        self.ptr = 0

        self.action_aware = bool(PROPOSED_USE_ACTION_AWARE_ENV if action_aware is None else action_aware)
        self.heavy_task_penalty = bool(
            PROPOSED_HEAVY_TASK_EDGE_PENALTY if heavy_task_penalty is None else heavy_task_penalty
        )

        self.edge_lat = self.df["edge_latency"].to_numpy(dtype=np.float32)
        self.cloud_lat = self.df["cloud_latency"].to_numpy(dtype=np.float32)
        self.energy_req = self.df["energy_required"].to_numpy(dtype=np.float32)
        self.task_size = self.df["task_size_mb"].to_numpy(dtype=np.float32)
        self.cpu_cycles = self.df["cpu_cycles"].to_numpy(dtype=np.float32)
        self.priority = self.df["priority_level"].to_numpy(dtype=np.float32)
        self.low_battery = self.df.get("is_low_battery", pd.Series(0, index=self.df.index)).to_numpy(dtype=np.float32)
        self.impossible = self.df.get("impossible_deadline", pd.Series(0, index=self.df.index)).to_numpy(dtype=np.float32)
        self.task_type = self.df["task_type"].astype(str).to_numpy()
        self.sla = self.df["task_type"].map(SLA_MS).fillna(9999).to_numpy(dtype=np.float32)

        self.edge_pressure = 0.0
        self.cloud_pressure = 0.0
        self.network_pressure = 0.0
        self.energy_debt = 0.0

    def __len__(self):
        return self.n

    def _base_state(self, idx: int) -> np.ndarray:
        return self.X[idx].copy()

    def _state(self, idx: int) -> torch.Tensor:
        obs = self._base_state(idx)
        if self.action_aware:
            obs[_F_E_QUEUE] += min(self.edge_pressure, 6.0) * 0.20
            obs[_F_E_ENERGY] -= min(self.energy_debt, 6.0) * 0.12
            obs[_F_EFF_BW] -= min(self.network_pressure, 6.0) * 0.18
            obs[_F_N_LOSS] += min(self.network_pressure, 6.0) * 0.08
            obs[_F_C_OVER] += min(self.cloud_pressure, 6.0) * 0.18
        return torch.from_numpy(np.clip(obs, -10.0, 10.0).astype(np.float32, copy=False))

    def reset(self) -> torch.Tensor:
        self.ptr = 0
        self.edge_pressure = 0.0
        self.cloud_pressure = 0.0
        self.network_pressure = 0.0
        self.energy_debt = 0.0
        return self._state(0)

    def _dynamic_latencies(self, idx: int):
        edge_lat = float(self.edge_lat[idx])
        cloud_lat = float(self.cloud_lat[idx])
        if self.action_aware:
            edge_lat = min(edge_lat * (1.0 + 0.055 * self.edge_pressure) + 2.5 * self.energy_debt, EDGE_LAT_CAP)
            cloud_lat = min(cloud_lat * (1.0 + 0.045 * self.cloud_pressure + 0.060 * self.network_pressure), CLOUD_LAT_CAP)
        return edge_lat, cloud_lat

    def _apply_action_pressure(self, idx: int, action: int):
        if not self.action_aware:
            self.edge_pressure = 0.0
            self.cloud_pressure = 0.0
            self.network_pressure = 0.0
            self.energy_debt = 0.0
            return

        size_norm = min(float(self.task_size[idx]) / 80.0, 3.0)
        prio_norm = min(float(self.priority[idx]) / 5.0, 1.0)
        urgent = 1.0 if self.task_type[idx] in self.URGENT_TASK_TYPES else 0.0

        self.edge_pressure *= 0.965
        self.cloud_pressure *= 0.970
        self.network_pressure *= 0.972
        self.energy_debt *= 0.975

        if action == 0:
            self.edge_pressure += 0.10 + 0.09 * size_norm + 0.06 * prio_norm + 0.06 * urgent
            self.energy_debt += 0.04 + 0.06 * min(float(self.energy_req[idx]) / 150.0, 2.0)
            if self.low_battery[idx] > 0.5:
                self.energy_debt += 0.08
        else:
            self.cloud_pressure += 0.10 + 0.10 * size_norm + 0.04 * prio_norm
            self.network_pressure += 0.09 + 0.12 * size_norm + 0.03 * urgent

        self.edge_pressure = float(np.clip(self.edge_pressure, 0.0, 8.0))
        self.cloud_pressure = float(np.clip(self.cloud_pressure, 0.0, 8.0))
        self.network_pressure = float(np.clip(self.network_pressure, 0.0, 8.0))
        self.energy_debt = float(np.clip(self.energy_debt, 0.0, 8.0))

    def step(self, action: int):
        idx = self.ptr
        lat_e, lat_c = self._dynamic_latencies(idx)
        lat = lat_e if action == 0 else lat_c
        sla = float(self.sla[idx])
        task_type = self.task_type[idx]

        best = min(lat_e, lat_c)
        worst = max(lat_e, lat_c)
        regret = (lat - best) / max(best, 1.0)
        lat_r = 1.25 * (1.0 - 2.0 * ((lat - best) / (worst - best + 1e-6)))
        regret_r = -0.75 * float(np.clip(regret, 0.0, 2.0))

        sla_margin = float(np.clip((sla - lat) / max(sla, 1.0), -1.5, 1.0))
        sla_r = 1.05 * sla_margin if sla_margin >= 0.0 else 2.10 * sla_margin
        selected_reject = int(lat >= sla or self.impossible[idx] > 0.5)
        reject_r = -2.25 * selected_reject

        size_norm = min(float(self.task_size[idx]) / 120.0, 2.0)
        cpu_norm = min(float(self.cpu_cycles[idx]) / 900.0, 2.0)
        edge_worse_pct = max(lat_e - lat_c, 0.0) / max(lat_c, 1.0)
        cloud_worse_pct = max(lat_c - lat_e, 0.0) / max(lat_e, 1.0)

        routing_r = 0.0
        if action == 0:
            if lat_e > lat_c:
                routing_r -= min(1.35, 0.30 + 0.85 * edge_worse_pct)
            if self.heavy_task_penalty and task_type in self.HEAVY_TASK_TYPES and lat_e >= lat_c * 0.98:
                routing_r -= 0.30 + 0.16 * size_norm + 0.12 * cpu_norm
            routing_r -= 0.08 * float(self.energy_req[idx] / (self.energy_req[idx] + 100.0))
            if self.low_battery[idx] > 0.5 and task_type not in self.URGENT_TASK_TYPES:
                routing_r -= 0.05
            if self.action_aware:
                routing_r -= 0.035 * self.edge_pressure
        else:
            if task_type in self.URGENT_TASK_TYPES and lat_e < lat_c and lat_e < sla:
                routing_r -= min(0.70, 0.16 + 0.35 * cloud_worse_pct)
            if self.action_aware:
                routing_r -= 0.030 * (self.cloud_pressure + self.network_pressure)

        urgent_r = 0.0
        if task_type == "emergency":
            if action == 0 and lat_e <= lat_c and lat < sla:
                urgent_r = 0.35
            elif action == 1 and lat_e < lat_c and lat_e < sla:
                urgent_r = -0.35

        reward = float(np.clip(lat_r + regret_r + sla_r + reject_r + routing_r + urgent_r, -5.0, 5.0))
        self._apply_action_pressure(idx, action)

        done = self.ptr >= self.n - 2
        self.ptr = min(self.ptr + 1, self.n - 1)
        next_obs = self._state(self.ptr)
        info = {
            "latency": lat,
            "sla_met": int(lat < sla),
            "selected_reject": selected_reject,
            "edge_pressure": self.edge_pressure,
            "cloud_pressure": self.cloud_pressure,
            "network_pressure": self.network_pressure,
            "task_type": task_type,
        }
        return next_obs, reward, done, info


print("OffloadEnv v6.6 ready: evaluation-aligned reward, optional action-aware pressure.")
print(f"  action_aware_default={PROPOSED_USE_ACTION_AWARE_ENV} heavy_task_penalty={PROPOSED_HEAVY_TASK_EDGE_PENALTY}")
'''


ZONE_CELL = r'''
# Collect training tasks and their scaled features.
train_df = tasks[train_mask].reset_index(drop=True)
train_X_sc = X_train_sc

zone_names = sorted(zone_edge_ids.keys())
zone_envs = {}

for zone in zone_names:
    zmask = train_df["zone"] == zone
    z_idx = zmask.values.nonzero()[0]

    if len(z_idx) == 0:
        print(f"  Zone {zone}: 0 tasks - skipping")
        continue

    z_df = train_df.iloc[z_idx].reset_index(drop=True)
    z_X = train_X_sc[z_idx]

    zone_envs[zone] = OffloadEnv(
        z_df,
        z_X,
        action_aware=PROPOSED_USE_ACTION_AWARE_ENV,
        heavy_task_penalty=PROPOSED_HEAVY_TASK_EDGE_PENALTY,
    )
    print(f"  Zone {zone:12s}: {len(z_df):,} training tasks")

    tt_dist = z_df["task_type"].value_counts(normalize=True)
    print(f"    Top task types: {dict(tt_dist.head(3).round(2))}")

zone_names = list(zone_envs.keys())
print(f"\nFederated clients: {len(zone_names)} zones = {zone_names}")
print("[v6.6] Non-IID split: each federated client trains on its own zone.")
print("[v6.6] Proposed Fed-DDQN env is evaluation-aligned by default.")
'''


FED_TRAIN_CELL = r'''
GAMMA = 0.95
EPSILON_START = 1.0
EPSILON_MIN = 0.05
EPSILON_DECAY = 0.92
BATCH_SIZE = 512
ROUNDS = 20
MAX_STEPS = 8000
TARGET_UPDATE = 200
TARGET_TAU = PROPOSED_TARGET_TAU
MU_PROXIMAL = PROPOSED_MU_PROXIMAL
PRIORITY_BETA_START = 0.40
PRIORITY_BETA_FRAMES = max(ROUNDS - 1, 1)
PATIENCE = 6


def _state_dict_cpu(model):
    return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}


def evaluate_q_model_on_split(q_model, X_np, split_df):
    q_model.eval()
    with torch.inference_mode():
        if X_np is X_val_sc:
            xb = X_val_dev
        elif X_np is X_test_sc:
            xb = X_test_dev
        else:
            xb = torch.tensor(X_np, dtype=torch.float32, device=device)
        actions = torch.argmax(q_model(xb), dim=1).cpu().numpy().astype(np.int64)

    lat_e_all = split_df["edge_latency"].to_numpy(dtype=np.float32)
    lat_c_all = split_df["cloud_latency"].to_numpy(dtype=np.float32)
    valid = (lat_e_all < EDGE_LAT_CAP) | (lat_c_all < CLOUD_LAT_CAP)
    actions_v = actions[valid]
    lat_e = lat_e_all[valid]
    lat_c = lat_c_all[valid]
    lat = np.where(actions_v == 0, lat_e, lat_c)
    split_v = split_df.loc[valid].reset_index(drop=True)
    sla = split_v["task_type"].map(SLA_MS).fillna(9999).to_numpy(dtype=np.float32)
    impossible = split_v.get("impossible_deadline", pd.Series(0, index=split_v.index)).to_numpy(dtype=np.float32)
    selected_reject = (lat >= sla) | (impossible > 0.5)
    heavy_mask = split_v["task_type"].astype(str).isin(list(OffloadEnv.HEAVY_TASK_TYPES)).to_numpy()
    heavy_edge_bad = heavy_mask & (actions_v == 0) & (lat_e > lat_c * 1.02)

    return {
        "Avg Latency": float(lat.mean()) if len(lat) else 0.0,
        "SLA Miss %": float((lat >= sla).mean() * 100.0) if len(lat) else 0.0,
        "Rejection %": float(selected_reject.mean() * 100.0) if len(lat) else 0.0,
        "SLA %": float((lat < sla).mean() * 100.0) if len(lat) else 0.0,
        "Edge Usage %": float((actions_v == 0).mean() * 100.0) if len(actions_v) else 0.0,
        "Heavy Edge Bad %": float(heavy_edge_bad.mean() * 100.0) if len(actions_v) else 0.0,
        "N Eval": int(len(lat)),
    }


def fed_validation_score(metrics):
    edge_overuse = max(metrics["Edge Usage %"] - PROPOSED_EDGE_OVERUSE_SOFT_CAP, 0.0)
    return (
        metrics["Avg Latency"]
        + 5.0 * metrics["SLA Miss %"]
        + 2.5 * metrics["Rejection %"]
        + 0.8 * edge_overuse
        + 1.2 * metrics.get("Heavy Edge Bad %", 0.0)
    )


global_q = QNetwork(X_train.shape[1]).to(device)
target_q = deepcopy(global_q).to(device)
fed_ddqn_loaded_from_cache = False
federated_losses = []
federated_rewards = []
validation_scores = []
federated_zone_rewards = {zone: [] for zone in zone_names}
best_val_score = float("inf")
best_round = 0
rounds_ran = 0

if (not FORCE_RETRAIN_FED_DDQN) and os.path.exists(fed_model_path):
    try:
        payload = torch.load(fed_model_path, map_location=device)
        global_q.load_state_dict(payload["global_state_dict"])
        target_q.load_state_dict(payload.get("target_state_dict", payload["global_state_dict"]))
        federated_losses = list(payload.get("federated_losses", []))
        federated_rewards = list(payload.get("federated_rewards", []))
        validation_scores = list(payload.get("validation_scores", []))
        federated_zone_rewards = payload.get("federated_zone_rewards", federated_zone_rewards)
        best_val_score = float(payload.get("best_val_score", float("inf")))
        best_round = int(payload.get("best_round", len(federated_losses)))
        rounds_ran = int(payload.get("rounds_ran", len(federated_losses)))
        fed_ddqn_loaded_from_cache = True
        print(f"Loaded cached Fed-DDQN v6.6 checkpoint: {fed_model_path}")
        print(f"  best_round={best_round}  best_val_score={best_val_score:.4f}  rounds_ran={rounds_ran}")
    except Exception as exc:
        print(f"Fed-DDQN cache ignored and retrained: {exc}")

if not fed_ddqn_loaded_from_cache:
    print("Training proposed Federated DDQN v6.6 ...")
    print("Focus: non-IID zone clients + dueling DDQN + weighted FedAvg + soft target updates")
    print(f"Replay prioritized={PROPOSED_USE_PRIORITIZED_REPLAY} | FedProx mu={MU_PROXIMAL} | tau={TARGET_TAU}")
    print(f"Validation cap: edge overuse above {PROPOSED_EDGE_OVERUSE_SOFT_CAP:.1f}% is penalized")

    zone_models = {zone: deepcopy(global_q).to(device) for zone in zone_names}
    zone_targets = {zone: deepcopy(global_q).to(device) for zone in zone_names}
    zone_opts = {zone: optim.AdamW(zone_models[zone].parameters(), lr=5e-4, weight_decay=1e-4) for zone in zone_names}
    zone_buffers = {zone: ReplayBuffer(30000) for zone in zone_names}
    zone_eps = {zone: EPSILON_START for zone in zone_names}
    huber_none = nn.SmoothL1Loss(reduction="none")
    best_global_state = _state_dict_cpu(global_q)
    best_target_state = _state_dict_cpu(target_q)
    bad_rounds = 0

    for rnd in range(ROUNDS):
        beta = min(1.0, PRIORITY_BETA_START + (1.0 - PRIORITY_BETA_START) * rnd / PRIORITY_BETA_FRAMES)
        local_models = []
        agg_weights = []
        rnd_loss = 0.0
        rnd_reward = 0.0
        rnd_batches = 0
        rnd_steps = 0

        for zone in zone_names:
            env = zone_envs[zone]
            lm = zone_models[zone]
            tgt = zone_targets[zone]
            opt = zone_opts[zone]
            buf = zone_buffers[zone]
            lm.load_state_dict(global_q.state_dict())
            tgt.load_state_dict(target_q.state_dict())
            fedprox_anchors = (
                [param.detach().clone() for param in global_q.parameters()]
                if MU_PROXIMAL > 0.0 else []
            )
            lm.train()
            state = env.reset().to(device)
            zone_reward = 0.0
            steps_this_zone = 0

            while steps_this_zone < MAX_STEPS:
                eps = zone_eps[zone]
                if np.random.rand() < eps:
                    action = int(np.random.randint(0, 2))
                else:
                    with torch.no_grad():
                        action = int(torch.argmax(lm(state.unsqueeze(0))).item())

                next_state, reward, done, _ = env.step(action)
                buf.push(state.detach().cpu(), action, reward, next_state.detach().cpu())
                rnd_reward += reward
                zone_reward += reward
                rnd_steps += 1
                steps_this_zone += 1

                if len(buf) > BATCH_SIZE:
                    if PROPOSED_USE_PRIORITIZED_REPLAY:
                        sb, ab, rb, nsb, idxs, isw = buf.sample_prioritized(BATCH_SIZE, beta=beta)
                        isw = isw.to(device)
                    else:
                        sb, ab, rb, nsb = buf.sample(BATCH_SIZE)
                        idxs = None
                        isw = torch.ones(BATCH_SIZE, dtype=torch.float32, device=device)

                    sb = sb.to(device)
                    nsb = nsb.to(device)
                    ab = ab.to(device)
                    rb = rb.to(device)
                    current_q = lm(sb).gather(1, ab.unsqueeze(1)).squeeze(1)
                    with torch.no_grad():
                        next_actions = torch.argmax(lm(nsb), dim=1)
                        next_q = tgt(nsb).gather(1, next_actions.unsqueeze(1)).squeeze(1)
                        target_values = rb + GAMMA * next_q

                    td_errors = current_q - target_values
                    loss_td = (isw * huber_none(current_q, target_values)).mean()
                    if MU_PROXIMAL > 0.0 and (rnd_batches % PROPOSED_FEDPROX_INTERVAL == 0):
                        drift = torch.zeros((), dtype=torch.float32, device=device)
                        for param, anchor in zip(lm.parameters(), fedprox_anchors):
                            drift = drift + torch.sum((param - anchor) ** 2)
                        drift = torch.nan_to_num(
                            torch.clamp(drift, max=PROPOSED_FEDPROX_MAX_DRIFT),
                            nan=0.0,
                            posinf=PROPOSED_FEDPROX_MAX_DRIFT,
                            neginf=0.0,
                        )
                        loss = loss_td + (MU_PROXIMAL / 2.0) * drift
                    else:
                        loss = loss_td
                    if not torch.isfinite(loss):
                        opt.zero_grad(set_to_none=True)
                        continue
                    opt.zero_grad(set_to_none=True)
                    loss.backward()
                    nn.utils.clip_grad_norm_(lm.parameters(), 1.0)
                    opt.step()
                    soft_update(tgt, lm, tau=TARGET_TAU)
                    if PROPOSED_USE_PRIORITIZED_REPLAY and idxs is not None:
                        buf.update_priorities(idxs, td_errors.detach().abs().cpu())
                    rnd_loss += float(loss_td.item())
                    rnd_batches += 1

                state = next_state.to(device)
                if done:
                    state = env.reset().to(device)

            zone_avg_reward = zone_reward / max(steps_this_zone, 1)
            federated_zone_rewards[zone].append(zone_avg_reward)
            zone_eps[zone] = max(zone_eps[zone] * EPSILON_DECAY, EPSILON_MIN)
            perf_factor = float(np.clip(1.0 + 0.05 * zone_avg_reward, 0.75, 1.25))
            agg_weights.append(len(env.df) * perf_factor)
            local_models.append(deepcopy(lm).cpu())

        averaged_q = federated_average(local_models, weights=agg_weights).to(device)
        global_q.load_state_dict(averaged_q.state_dict())
        soft_update(target_q, global_q, tau=0.25)

        avg_loss = rnd_loss / max(rnd_batches, 1)
        avg_reward = rnd_reward / max(rnd_steps, 1)
        federated_losses.append(avg_loss)
        federated_rewards.append(avg_reward)
        val_metrics = evaluate_q_model_on_split(global_q, X_val_sc, val_df)
        val_score = fed_validation_score(val_metrics)
        validation_scores.append(val_score)
        rounds_ran = rnd + 1
        eps_report = float(np.mean(list(zone_eps.values()))) if zone_eps else EPSILON_MIN
        improved = val_score < best_val_score

        if improved:
            best_val_score = val_score
            best_round = rnd + 1
            best_global_state = _state_dict_cpu(global_q)
            best_target_state = _state_dict_cpu(target_q)
            bad_rounds = 0
        else:
            bad_rounds += 1

        print(
            f"Round {rnd + 1:2d}/{ROUNDS}  loss={avg_loss:.4f}  reward={avg_reward:.4f}  "
            f"val_score={val_score:.3f}  val_lat={val_metrics['Avg Latency']:.2f}  "
            f"val_edge={val_metrics['Edge Usage %']:.2f}%  heavy_bad={val_metrics['Heavy Edge Bad %']:.2f}%  "
            f"eps(avg)={eps_report:.3f}  best={best_round}"
        )

        if bad_rounds >= PATIENCE:
            print(f"Early stopping: validation did not improve for {PATIENCE} rounds.")
            break

    global_q.load_state_dict(best_global_state)
    target_q.load_state_dict(best_target_state)
    torch.save({
        "global_state_dict": best_global_state,
        "target_state_dict": best_target_state,
        "federated_losses": federated_losses,
        "federated_rewards": federated_rewards,
        "validation_scores": validation_scores,
        "federated_zone_rewards": federated_zone_rewards,
        "best_val_score": best_val_score,
        "best_round": best_round,
        "rounds_ran": rounds_ran,
        "MAX_STEPS": MAX_STEPS,
        "ROUNDS": ROUNDS,
        "proposed_config": {
            "action_aware_env": PROPOSED_USE_ACTION_AWARE_ENV,
            "prioritized_replay": PROPOSED_USE_PRIORITIZED_REPLAY,
            "mu_proximal": MU_PROXIMAL,
            "target_tau": TARGET_TAU,
            "edge_overuse_soft_cap": PROPOSED_EDGE_OVERUSE_SOFT_CAP,
            "heavy_task_edge_penalty": PROPOSED_HEAVY_TASK_EDGE_PENALTY,
        },
    }, fed_model_path)
    print(f"Saved Fed-DDQN v6.6 best checkpoint: {fed_model_path}")

EPSILON = EPSILON_MIN
print("\nProposed Federated DDQN v6.6 ready.")
print(f"Zones used: {zone_names}")
print(f"Fed-DDQN cache loaded: {fed_ddqn_loaded_from_cache}")
print(f"Best validation round: {best_round} | best_val_score={best_val_score:.4f} | rounds_ran={rounds_ran}")
print("Applied: evaluation-aligned reward | non-IID FedAvg | dueling DDQN | soft targets | light FedProx | validation penalties")
'''


MAIN_EVAL_CELL = r'''
def _model_actions(q_model, X_np):
    q_model.eval()
    with torch.inference_mode():
        if X_np is X_test_sc:
            xb = X_test_dev
        elif X_np is X_val_sc:
            xb = X_val_dev
        else:
            xb = torch.tensor(X_np, dtype=torch.float32, device=device)
        return torch.argmax(q_model(xb), dim=1).cpu().numpy().astype(np.int64)


def get_policy_actions(method, X_np, raw_np, eval_df):
    edge_possible = raw_np[:, _F_E_FAIL] < 0.5
    if method == "DDQN":
        return _model_actions(cent_q, X_np)
    if method == "FL-DDPG":
        return _model_actions(feddpg_q, X_np)
    if method == "Fed-DDQN (Proposed)":
        return _model_actions(global_q, X_np)
    if method == "Oracle":
        return (eval_df["cloud_latency"].to_numpy(dtype=np.float32) < eval_df["edge_latency"].to_numpy(dtype=np.float32)).astype(np.int64)
    if method == "MTOSA":
        return np.where((raw_np[:, _F_E_QUEUE] < 25.0) & (raw_np[:, _F_EFF_BW] > 100.0) & edge_possible, 0, 1)
    if method == "GTPSO":
        return np.where((raw_np[:, _F_E_ENERGY] > 80.0) & (raw_np[:, _F_C_OVER] > 0.25) & edge_possible, 0, 1)
    if method == "PTS-RA":
        return np.where((raw_np[:, _F_PRIORITY] >= 3.0) & (raw_np[:, _F_E_QUEUE] < 40.0) & edge_possible, 0, 1)
    if method == "JTOS":
        return np.where((raw_np[:, _F_DEADLINE] <= 800.0) & (raw_np[:, _F_E_QUEUE] < 35.0) & edge_possible, 0, 1)
    raise ValueError(f"Unknown policy method: {method}")


def evaluate_actions(method, actions, eval_df, raw_np):
    lat_e = eval_df["edge_latency"].to_numpy(dtype=np.float32)
    lat_c = eval_df["cloud_latency"].to_numpy(dtype=np.float32)
    valid = (lat_e < EDGE_LAT_CAP) | (lat_c < CLOUD_LAT_CAP)
    actions = np.asarray(actions, dtype=np.int64)
    lat_e = lat_e[valid]
    lat_c = lat_c[valid]
    actions_v = actions[valid]
    raw_v = raw_np[valid]
    df_v = eval_df.loc[valid].reset_index(drop=True)
    lat = np.where(actions_v == 0, lat_e, lat_c)
    sla = df_v["task_type"].map(SLA_MS).fillna(9999).to_numpy(dtype=np.float32)
    impossible = df_v.get("impossible_deadline", pd.Series(0, index=df_v.index)).to_numpy(dtype=np.float32)
    sla_ok = lat < sla
    selected_reject = (~sla_ok) | (impossible > 0.5)

    eff_bw = np.maximum(raw_v[:, _F_EFF_BW], 1.0)
    cloud_comm = raw_v[:, _F_N_DELAY] + raw_v[:, _F_TASK_SIZE] / eff_bw
    edge_comm = np.clip(raw_v[:, _F_E_QUEUE] * 0.5, 0.0, EDGE_LAT_CAP)
    comm_delay = np.where(actions_v == 1, cloud_comm, edge_comm)
    cloud_bw = np.clip(raw_v[:, _F_TASK_SIZE] / eff_bw, 0.0, 1.0) * 100.0
    edge_bw = np.zeros_like(cloud_bw)
    bw_cons = np.where(actions_v == 1, cloud_bw, edge_bw)
    n = len(lat)
    return {
        "Method": method,
        "Avg Latency": round(float(lat.mean()), 3) if n else 0.0,
        "SLA %": round(float(sla_ok.mean()) * 100.0, 2) if n else 0.0,
        "SLA Miss %": round(float((~sla_ok).mean()) * 100.0, 2) if n else 0.0,
        "Rejection %": round(float(selected_reject.mean()) * 100.0, 2) if n else 0.0,
        "Edge Usage %": round(float((actions_v == 0).mean()) * 100.0, 2) if n else 0.0,
        "Comm Delay (ms)": round(float(comm_delay.mean()), 3) if n else 0.0,
        "BW Consump %": round(float(bw_cons.mean()), 2) if n else 0.0,
        "N Eval": n,
    }


def evaluate_method(method, X_np, raw_np, eval_df):
    actions = get_policy_actions(method, X_np, raw_np, eval_df)
    return evaluate_actions(method, actions, eval_df, raw_np), actions


print("Evaluating 8 policies on the untouched test split with batched inference ...")
if EVALUATE_FULL_TEST_SPLIT:
    eval_positions = np.arange(len(test_tasks_all))
else:
    rng_eval2 = np.random.default_rng(99)
    eval_n = min(3000, int(test_mask.sum()))
    eval_positions = rng_eval2.choice(len(test_tasks_all), size=eval_n, replace=False)

eval_sample = test_tasks_all.iloc[eval_positions].reset_index(drop=True)
eval_X = test_X_all[eval_positions]
eval_raw = test_raw_all[eval_positions]
print(f"  Eval sample: {len(eval_sample):,} tasks | full_test={EVALUATE_FULL_TEST_SPLIT}")

POLICY_METHODS = [
    "DDQN", "MTOSA", "FL-DDPG", "GTPSO", "PTS-RA", "JTOS",
    "Fed-DDQN (Proposed)", "Oracle",
]

actions_by_method = {}
all_results = []
for method in POLICY_METHODS:
    res, actions = evaluate_method(method, eval_X, eval_raw, eval_sample)
    actions_by_method[method] = actions
    all_results.append(res)
    print(f"  {method:22s}  Lat={res['Avg Latency']:7.2f}ms  SLA={res['SLA %']:5.1f}%  "
          f"Miss={res['SLA Miss %']:5.1f}%  Rej={res['Rejection %']:5.1f}%  "
          f"Edge={res['Edge Usage %']:5.1f}%  N={res['N Eval']:,}")

df_compare = pd.DataFrame(all_results).set_index("Method")

print("\n-- Validation checks --")
for method, row in df_compare.iterrows():
    assert 0.0 <= row["SLA Miss %"] <= 100.0
    assert 0.0 <= row["Rejection %"] <= 100.0
    assert 0.0 <= row["Edge Usage %"] <= 100.0
    assert abs(row["SLA %"] + row["SLA Miss %"] - 100.0) < 0.05, f"SLA complement fail: {method}"
print("  Bounds and complement checks OK")

oracle_lat = df_compare.loc["Oracle", "Avg Latency"]
fed_lat = df_compare.loc["Fed-DDQN (Proposed)", "Avg Latency"]
if oracle_lat <= fed_lat + 1e-6:
    print(f"  Oracle ({oracle_lat:.2f} ms) <= Fed-DDQN ({fed_lat:.2f} ms) OK")
else:
    print(f"  Check: Oracle ({oracle_lat:.2f} ms) is above Fed-DDQN ({fed_lat:.2f} ms) on this sample")

print("\n" + "=" * 96)
print("LITERATURE COMPARISON TABLE - v6.6 proposed Federated DDQN")
print("=" * 96)
cols = ["Avg Latency", "SLA %", "SLA Miss %", "Rejection %", "Edge Usage %", "Comm Delay (ms)", "BW Consump %"]
print(df_compare[cols].to_string())
print("=" * 96)
print("\n-- Fed-DDQN latency improvement over each baseline --")
prop_lat = df_compare.loc["Fed-DDQN (Proposed)", "Avg Latency"]
for method in ["DDQN", "MTOSA", "FL-DDPG", "GTPSO", "PTS-RA", "JTOS"]:
    baseline_lat = df_compare.loc[method, "Avg Latency"]
    pct = (baseline_lat - prop_lat) / max(baseline_lat, 1e-3) * 100.0
    print(f"  vs {method:10s}: {pct:+.1f}% latency reduction")
'''


FINAL_SUMMARY_CELL = r'''
model.eval()
with torch.no_grad():
    lg2 = model(X_test.to(device))
    pr2 = torch.argmax(lg2, dim=1).cpu().numpy()
    pb2 = torch.softmax(lg2, dim=1)[:, 1].cpu().numpy()

acc_net = accuracy_score(y_test_t.numpy(), pr2)
f1_net = f1_score(y_test_t.numpy(), pr2, average="weighted")
fpr2, tpr2, _ = roc_curve(y_test_t.numpy(), pb2)
auc_net = auc(fpr2, tpr2)

allocator.eval()
with torch.no_grad():
    ap = allocator(X_alloc.to(device)).cpu()
    mae_a = torch.mean(torch.abs(ap - y_alloc)).item()

emerg_edge = float((tasks[tasks["task_type"] == "emergency"]["offload_label"] == 0).mean()) * 100
n_rej_flag = tasks["rejection_flag"].sum()
fed_cmp = df_compare.loc["Fed-DDQN (Proposed)"]
ddqn_cmp = df_compare.loc["DDQN"]
flddpg_cmp = df_compare.loc["FL-DDPG"]
oracle_cmp = df_compare.loc["Oracle"]

print("=" * 76)
print(f"  {'METRIC':<49} {'VALUE':>22}")
print("=" * 76)
print(f"  {'[OffloadNet] Accuracy':<49} {acc_net * 100:>21.2f}%")
print(f"  {'[OffloadNet] Weighted F1':<49} {f1_net:>22.4f}")
print(f"  {'[OffloadNet] ROC-AUC':<49} {auc_net:>22.4f}")
print("-" * 76)
print(f"  {'[Fed-DDQN v6.6] Avg Latency (ms)':<49} {fed_cmp['Avg Latency']:>22.4f}")
print(f"  {'[Fed-DDQN v6.6] SLA Compliance':<49} {fed_cmp['SLA %']:>21.2f}%")
print(f"  {'[Fed-DDQN v6.6] Rejection %':<49} {fed_cmp['Rejection %']:>21.2f}%")
print(f"  {'[Fed-DDQN v6.6] Edge Usage':<49} {fed_cmp['Edge Usage %']:>21.2f}%")
print(f"  {'[Fed-DDQN v6.6] Best Validation Round':<49} {best_round:>22}")
print(f"  {'[Fed-DDQN v6.6] Best Validation Score':<49} {best_val_score:>22.4f}")
print(f"  {'[Fed-DDQN v6.6] Rounds Actually Run':<49} {rounds_ran:>22}")
print("-" * 76)
print(f"  {'[Compare] DDQN Avg Latency':<49} {ddqn_cmp['Avg Latency']:>22.3f} ms")
print(f"  {'[Compare] FL-DDPG Avg Latency':<49} {flddpg_cmp['Avg Latency']:>22.3f} ms")
print(f"  {'[Compare] Oracle Avg Latency':<49} {oracle_cmp['Avg Latency']:>22.3f} ms")
print(f"  {'[Compare] Fed vs DDQN Improvement':<49} "
      f"{((ddqn_cmp['Avg Latency'] - fed_cmp['Avg Latency']) / max(ddqn_cmp['Avg Latency'], 1e-6) * 100.0):>21.2f}%")
print(f"  {'[Compare] Fed vs FL-DDPG Improvement':<49} "
      f"{((flddpg_cmp['Avg Latency'] - fed_cmp['Avg Latency']) / max(flddpg_cmp['Avg Latency'], 1e-6) * 100.0):>21.2f}%")
print("-" * 76)
print(f"  {'[Allocator] CPU MAE':<49} {errors[:, 0].mean():>22.4f}")
print(f"  {'[Allocator] Memory MAE':<49} {errors[:, 1].mean():>22.4f}")
print(f"  {'[Allocator] Bandwidth MAE':<49} {errors[:, 2].mean():>22.4f}")
print(f"  {'[Allocator] Overall MAE':<49} {mae_a:>22.4f}")
print("-" * 76)
print(f"  {'[System] Rejection Flag Count':<49} {n_rej_flag:>22,}")
print(f"  {'[System] Rejection Rate':<49} {tasks['rejection_flag'].mean():>22.4f}")
print(f"  {'[System] SLA Violation Rate':<49} {tasks['sla_violated'].mean():>22.4f}")
print(f"  {'[System] Emergency->Edge Label Rate':<49} {emerg_edge:>21.2f}%")
print(f"  {'[System] Federated Zones':<49} {str(zone_names):>22}")
print("=" * 76)
print("\nImprovements applied:")
print("  [v6.6] Proposed model remains Federated DDQN for edge-cloud process scheduling/offloading")
print("  [v6.6] Reward rebalanced against edge overuse and heavy-task edge misrouting")
print("  [v6.6] Proposed training uses evaluation-aligned environment by default")
print("  [v6.6] Validation score includes latency, SLA, rejection, edge overuse, and heavy-task routing")
print("  [v6.6] Main comparison uses the untouched test split when EVALUATE_FULL_TEST_SPLIT=True")
if "df_ablation_summary" in globals() and len(df_ablation_summary):
    print(f"  [v6.6] Multi-seed ablation variants: {len(df_ablation_summary)} | seeds: {EXPERIMENT_SEEDS}")
if "df_scenario_final" in globals() and len(df_scenario_final):
    print(f"  [v6.6] Scenario-wise rows: {len(df_scenario_final)}")
if "results_loaded_from_cache" in globals():
    print(f"  [v6.6] Result-table cache loaded: {results_loaded_from_cache}")
print(f"  [cache] labels={labels_cache_loaded} features={feature_cache_loaded} fed_ddqn={fed_ddqn_loaded_from_cache} baselines={baseline_models_loaded_from_cache} allocator_targets={alloc_targets_loaded_from_cache} allocator={allocator_loaded_from_cache}")
print("\nSanity checks:")
print(f"  max edge_lat  = {tasks['edge_latency'].max():.2f} (cap={EDGE_LAT_CAP})")
print(f"  max cloud_lat = {tasks['cloud_latency'].max():.2f} (cap={CLOUD_LAT_CAP})")
print(f"  DDQN eval lat range = {model_lat.min():.2f} to {model_lat.max():.2f} ms")
assert np.isnan(errors).sum() == 0, "NaN in allocator errors"
assert alloc_targets.shape[1] == 3, "Allocator must have 3 outputs"
print("  Static sanity checks passed for v6.6.")
'''


def update_multiseed_cell(nb):
    src = cell_text(nb, 41)
    src = regex_replace(
        src,
        r"class AblationOffloadEnv\(OffloadEnv\):.*?\n\n\nABLATION_CONFIGS = \[",
        '''class AblationOffloadEnv(OffloadEnv):
    """OffloadEnv variant for v6.6 ablation controls."""
    def __init__(self, task_df, feature_matrix, action_aware=None, heavy_task_penalty=None):
        super().__init__(
            task_df,
            feature_matrix,
            action_aware=action_aware,
            heavy_task_penalty=heavy_task_penalty,
        )


ABLATION_CONFIGS = [''',
        "AblationOffloadEnv block",
    )
    src = regex_replace(
        src,
        r"ABLATION_CONFIGS = \[.*?\]\n\n\n",
        '''ABLATION_CONFIGS = [
    {
        "name": "Fed-DDQN Proposed v6.6",
        "use_prioritized": PROPOSED_USE_PRIORITIZED_REPLAY,
        "mu_proximal": PROPOSED_MU_PROXIMAL,
        "soft_tau": PROPOSED_TARGET_TAU,
        "action_aware_env": PROPOSED_USE_ACTION_AWARE_ENV,
        "heavy_task_penalty": PROPOSED_HEAVY_TASK_EDGE_PENALTY,
        "validation_checkpoint": True,
    },
    {
        "name": "+ Prioritized Replay",
        "use_prioritized": True,
        "mu_proximal": PROPOSED_MU_PROXIMAL,
        "soft_tau": PROPOSED_TARGET_TAU,
        "action_aware_env": PROPOSED_USE_ACTION_AWARE_ENV,
        "heavy_task_penalty": PROPOSED_HEAVY_TASK_EDGE_PENALTY,
        "validation_checkpoint": True,
    },
    {
        "name": "+ Action-Aware Pressure",
        "use_prioritized": PROPOSED_USE_PRIORITIZED_REPLAY,
        "mu_proximal": PROPOSED_MU_PROXIMAL,
        "soft_tau": PROPOSED_TARGET_TAU,
        "action_aware_env": True,
        "heavy_task_penalty": PROPOSED_HEAVY_TASK_EDGE_PENALTY,
        "validation_checkpoint": True,
    },
    {
        "name": "No FedProx",
        "use_prioritized": PROPOSED_USE_PRIORITIZED_REPLAY,
        "mu_proximal": 0.0,
        "soft_tau": PROPOSED_TARGET_TAU,
        "action_aware_env": PROPOSED_USE_ACTION_AWARE_ENV,
        "heavy_task_penalty": PROPOSED_HEAVY_TASK_EDGE_PENALTY,
        "validation_checkpoint": True,
    },
    {
        "name": "Hard Target Update",
        "use_prioritized": PROPOSED_USE_PRIORITIZED_REPLAY,
        "mu_proximal": PROPOSED_MU_PROXIMAL,
        "soft_tau": None,
        "action_aware_env": PROPOSED_USE_ACTION_AWARE_ENV,
        "heavy_task_penalty": PROPOSED_HEAVY_TASK_EDGE_PENALTY,
        "validation_checkpoint": True,
    },
    {
        "name": "No Heavy-Task Penalty",
        "use_prioritized": PROPOSED_USE_PRIORITIZED_REPLAY,
        "mu_proximal": PROPOSED_MU_PROXIMAL,
        "soft_tau": PROPOSED_TARGET_TAU,
        "action_aware_env": PROPOSED_USE_ACTION_AWARE_ENV,
        "heavy_task_penalty": False,
        "validation_checkpoint": True,
    },
]


''',
        "ablation configs",
    )
    src = regex_replace(
        src,
        r"def build_variant_zone_envs\(action_aware_env=True\):.*?return envs\n\n\n",
        '''def build_variant_zone_envs(config):
    envs = {}
    for zone in zone_names:
        zmask = train_df["zone"] == zone
        z_idx = zmask.values.nonzero()[0]
        if len(z_idx) == 0:
            continue
        z_df = train_df.iloc[z_idx].reset_index(drop=True)
        z_X = X_train_sc[z_idx]
        envs[zone] = AblationOffloadEnv(
            z_df,
            z_X,
            action_aware=bool(config.get("action_aware_env", PROPOSED_USE_ACTION_AWARE_ENV)),
            heavy_task_penalty=bool(config.get("heavy_task_penalty", PROPOSED_HEAVY_TASK_EDGE_PENALTY)),
        )
    return envs


''',
        "build_variant_zone_envs",
    )
    replacements = {
        'config["name"] == "Full Fed-DDQN"': 'config["name"] == "Fed-DDQN Proposed v6.6"',
        'local_envs = build_variant_zone_envs(config["action_aware_env"])': "local_envs = build_variant_zone_envs(config)",
        'df_multiseed_raw["Ablation"] == "Full Fed-DDQN"': 'df_multiseed_raw["Ablation"] == "Fed-DDQN Proposed v6.6"',
        'if config["name"] == "Full Fed-DDQN":': 'if config["name"] == "Fed-DDQN Proposed v6.6":',
        'evaluate_actions("Full Fed-DDQN", actions[mask], test_df.loc[mask].reset_index(drop=True), test_raw_for_suite[mask])': 'evaluate_actions("Fed-DDQN Proposed v6.6", actions[mask], test_df.loc[mask].reset_index(drop=True), test_raw_for_suite[mask])',
        '"Method": "Fed-DDQN Full (meanąstd)"': '"Method": "Fed-DDQN Proposed v6.6 (mean+/-std)"',
        'print("RUN_MULTI_SEED_ABLATION=False; skipped v6.5 multi-seed ablation suite.")': 'print("RUN_MULTI_SEED_ABLATION=False; skipped v6.6 multi-seed ablation suite.")',
        'print("MULTI-SEED + ABLATION SUITE FOR PROPOSED FED-DDQN")': 'print("MULTI-SEED + ABLATION SUITE FOR PROPOSED FED-DDQN v6.6")',
        'return f"{arr.mean():.{digits}f} ą {arr.std(ddof=0):.{digits}f}"': 'return f"{arr.mean():.{digits}f} +/- {arr.std(ddof=0):.{digits}f}"',
        'return "0.000 ą 0.000"': 'return "0.000 +/- 0.000"',
        'axes[0].set_title("Ablation: Avg Latency (mean ą std)")': 'axes[0].set_title("Ablation: Avg Latency (mean +/- std)")',
        'axes[1].set_title("Ablation: SLA Compliance (mean ą std)")': 'axes[1].set_title("Ablation: SLA Compliance (mean +/- std)")',
        'print("\\n=== Ablation Summary (mean ą std across seeds) ===")': 'print("\\n=== Ablation Summary (mean +/- std across seeds) ===")',
        'lm.load_state_dict(model.state_dict())\n            tgt.load_state_dict(target_model.state_dict())\n            lm.train()': 'lm.load_state_dict(model.state_dict())\n            tgt.load_state_dict(target_model.state_dict())\n            fedprox_mu = float(config["mu_proximal"])\n            fedprox_anchors = (\n                [param.detach().clone() for param in model.parameters()]\n                if fedprox_mu > 0.0 else []\n            )\n            lm.train()',
        'drift = sum(torch.sum((p - pg.detach()) ** 2) for p, pg in zip(lm.parameters(), model.parameters()))\n                    loss = td_loss + (float(config["mu_proximal"]) / 2.0) * drift': 'if fedprox_mu > 0.0 and (round_batches % PROPOSED_FEDPROX_INTERVAL == 0):\n                        drift = torch.zeros((), dtype=torch.float32, device=device)\n                        for param, anchor in zip(lm.parameters(), fedprox_anchors):\n                            drift = drift + torch.sum((param - anchor) ** 2)\n                        drift = torch.nan_to_num(\n                            torch.clamp(drift, max=PROPOSED_FEDPROX_MAX_DRIFT),\n                            nan=0.0,\n                            posinf=PROPOSED_FEDPROX_MAX_DRIFT,\n                            neginf=0.0,\n                        )\n                        loss = td_loss + (fedprox_mu / 2.0) * drift\n                    else:\n                        loss = td_loss\n                    if not torch.isfinite(loss):\n                        opt.zero_grad(set_to_none=True)\n                        continue',
    }
    for old, new in replacements.items():
        src = src.replace(old, new)

    src = replace_once(
        src,
        '"N": int(mask.sum()),',
        '"N": int(round(np.mean([row["N Eval"] for row in seed_metric_rows]))) if seed_metric_rows else 0,',
        "scenario N",
    )
    set_cell(nb, 41, src)


def update_existing_text(nb):
    replacements = {
        "v6.5_multiseed_albation": "v6.6",
        "v6.5": "v6.6",
        "v6.4": "v6.6",
        "cached + validation-optimized Fed-DDQN": "rebalanced proposed Fed-DDQN",
        "action-aware contention and SLA-margin reward": "evaluation-aligned reward with optional action-aware pressure",
        "prioritized replay, persistent zone buffers, soft target updates, adaptive FedProx": "non-IID FedAvg, dueling DDQN, soft target updates, light FedProx",
    }
    for cell in nb["cells"]:
        src = "".join(cell.get("source", []))
        for old, new in replacements.items():
            src = src.replace(old, new)
        cell["source"] = src.splitlines(keepends=True)


def update_sample_cell(nb):
    src = cell_text(nb, 31)
    src = replace_once(
        src,
        "sample_n = min(5000, len(test_tasks_all))\nsample_positions = rng_eval.choice(len(test_tasks_all), size=sample_n, replace=False)",
        "sample_n = len(test_tasks_all) if EVALUATE_FULL_TEST_SPLIT else min(5000, len(test_tasks_all))\nsample_positions = np.arange(len(test_tasks_all)) if EVALUATE_FULL_TEST_SPLIT else rng_eval.choice(len(test_tasks_all), size=sample_n, replace=False)",
        "fed performance sample size",
    )
    set_cell(nb, 31, src)


def clear_outputs(nb):
    for cell in nb["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None


def validate_code_cells(nb):
    for index, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        try:
            ast.parse(src)
        except SyntaxError as exc:
            raise SyntaxError(f"Syntax error in code cell {index}: {exc}") from exc


def main():
    nb = json.loads(SRC.read_text(encoding="utf-8"))
    update_runtime_cell(nb)
    update_existing_text(nb)
    set_cell(nb, 21, OFFLOAD_ENV)
    set_cell(nb, 23, ZONE_CELL)
    set_cell(nb, 27, FED_TRAIN_CELL)
    update_sample_cell(nb)
    set_cell(nb, 33, MAIN_EVAL_CELL)
    update_multiseed_cell(nb)
    set_cell(nb, 53, FINAL_SUMMARY_CELL)
    clear_outputs(nb)
    validate_code_cells(nb)
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT.name} with {len(nb['cells'])} cells")


if __name__ == "__main__":
    main()
