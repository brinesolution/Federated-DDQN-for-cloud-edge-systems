import numpy as np
import pandas as pd
import os
from scipy.stats import pareto, weibull_min

np.random.seed(42)

# ==============================
# CONFIG
# ==============================
n              = 100000
num_edges      = 50
num_cloud      = 10
num_timesteps  = 1000
num_devices    = 5000

save_path = r"C:\Users\mayan\Desktop\3STSEM\ai\model\Datasets2"
os.makedirs(save_path, exist_ok=True)
print("Saving to:", save_path)
# ==============================
# TASK GENERATION
# ==============================
task_id = np.arange(1, n + 1)

# ── Task types with realistic proportions ──
task_types = ["sensor", "image", "ai", "video",
              "voice", "telemetry", "firmware_update", "emergency"]
task_type_probs = [0.35, 0.20, 0.12, 0.10,
                   0.10, 0.07, 0.03, 0.03]
task_type = np.random.choice(task_types, size=n, p=task_type_probs)

# ── Heavy-tailed task sizes (Pareto-like, realistic IoT workload) ──
small  = np.random.lognormal(mean=0.5,  sigma=0.8,  size=int(n * 0.60))  # tiny sensors
medium = np.random.lognormal(mean=3.0,  sigma=0.6,  size=int(n * 0.25))  # images/voice
large  = np.random.uniform(100, 600,                size=int(n * 0.12))  # video/AI
huge   = np.random.uniform(600, 1024,               size=n - len(small) - len(medium) - len(large))  # firmware

task_size_mb = np.concatenate([small, medium, large, huge])
np.random.shuffle(task_size_mb)
task_size_mb = np.clip(task_size_mb, 0.01, 1024.0)

# ── SPECIAL CASE 1: Emergency tasks — always tiny, ultra-low deadline ──
emerg_mask              = task_type == "emergency"
task_size_mb[emerg_mask] = np.random.uniform(0.01, 0.5, emerg_mask.sum())

# ── SPECIAL CASE 2: Firmware updates — always huge ──
firm_mask               = task_type == "firmware_update"
task_size_mb[firm_mask]  = np.random.uniform(200, 1024, firm_mask.sum())

# ── CPU cycles (task-type aware) ──
base_cpu = task_size_mb * np.random.uniform(800, 1800, n)
cpu_multiplier = {
    "sensor":          0.4,
    "telemetry":       0.5,
    "voice":           0.8,
    "image":           1.5,
    "video":           2.5,
    "ai":              4.0,
    "firmware_update": 0.2,   # mostly I/O, not compute
    "emergency":       0.3,   # simple threshold checks
}
cpu_cycles = base_cpu.copy()
for ttype, mult in cpu_multiplier.items():
    cpu_cycles[task_type == ttype] *= mult

# ── SPECIAL CASE 3: CPU spike — rare compute-intensive burst ──
spike_mask             = (np.random.rand(n) < 0.02)
cpu_cycles[spike_mask] *= np.random.uniform(5, 15, spike_mask.sum())

# ── SPECIAL CASE 4: Corrupted / malformed tasks (0 CPU, near-zero size) ──
corrupt_mask              = (np.random.rand(n) < 0.005)
cpu_cycles[corrupt_mask]   = np.random.uniform(0.001, 1.0, corrupt_mask.sum())
task_size_mb[corrupt_mask] = np.random.uniform(0.001, 0.01, corrupt_mask.sum())

cpu_cycles = np.clip(cpu_cycles, 1.0, 1e9)

# ── Memory requirements ──
mem_multiplier = {
    "sensor": 1.0, "telemetry": 1.0, "voice": 1.5,
    "image": 2.0, "video": 3.0, "ai": 5.0,
    "firmware_update": 1.2, "emergency": 0.8
}
memory_req_mb = task_size_mb * np.array(
    [mem_multiplier[t] for t in task_type]
) * np.random.uniform(0.8, 1.5, n)

# ── SPECIAL CASE 5: Memory-hungry AI tasks ──
ai_mask = task_type == "ai"
memory_req_mb[ai_mask] *= np.random.uniform(2.0, 6.0, ai_mask.sum())
memory_req_mb = np.clip(memory_req_mb, 1.0, 65536.0)

# ── Device modeling ──
device_id   = np.random.randint(1, num_devices + 1, n)
device_type = np.random.choice(
    ["mobile", "sensor", "iot", "edge_device",
     "drone", "vehicle", "wearable", "industrial"],
    size=n,
    p=[0.25, 0.25, 0.15, 0.15, 0.05, 0.05, 0.05, 0.05]
)

# ── Priority level ──
priority_base = np.ones(n, dtype=int)
priority_base[task_size_mb < 5]   = np.random.choice([1,2],   np.sum(task_size_mb < 5),   p=[0.7,0.3])
priority_base[(task_size_mb>=5) & (task_size_mb<100)] = np.random.choice(
    [1,2,3], np.sum((task_size_mb>=5)&(task_size_mb<100)), p=[0.4,0.4,0.2])
priority_base[task_size_mb >= 100] = np.random.choice([2,3],  np.sum(task_size_mb>=100),  p=[0.3,0.7])

# Emergency → always priority 3 | Firmware → always priority 1
priority_base[emerg_mask] = 3
priority_base[firm_mask]  = 1
priority_level = priority_base.astype(int)

# ── Deadline (priority + type aware) ──
type_deadline_factor = {
    "emergency": 0.1,   "voice": 0.3,
    "sensor":    0.8,   "telemetry": 1.0,
    "image":     1.5,   "video": 3.0,
    "ai":        5.0,   "firmware_update": 20.0,
}
deadline_factor  = np.array([type_deadline_factor[t] for t in task_type])
deadline_ms      = (np.random.uniform(200, 2000, n) * deadline_factor) / priority_level
deadline_ms     -= cpu_cycles * 0.005
deadline_ms      = np.clip(deadline_ms, 20.0, 1e6)

# SPECIAL CASE 6: Impossible deadlines (stress test) — 1% tasks
impossible_mask         = np.random.rand(n) < 0.01
deadline_ms[impossible_mask] = np.random.uniform(1, 10, impossible_mask.sum())

# ── Security sensitivity ──
security_base = priority_level * np.random.uniform(0.2, 0.5, n)
# Medical/industrial IoT devices have higher security sensitivity
medical_mask  = device_type == "industrial"
security_base[medical_mask] *= np.random.uniform(1.5, 2.0, medical_mask.sum())
security_sensitivity = np.clip(security_base, 0.0, 1.0)

# ── Energy ──
energy_required = cpu_cycles * np.random.uniform(0.0003, 0.0015, n)

# SPECIAL CASE 7: Low-battery devices — reduced energy budget
low_batt_mask              = np.random.rand(n) < 0.08
energy_required[low_batt_mask] *= 0.2   # tight energy constraint

energy_required = np.clip(energy_required, 0.01, 5000.0)

# ── Output size ──
output_ratio    = np.random.normal(0.5, 0.2, n)
rare_expand     = np.random.rand(n) < 0.05
output_ratio[rare_expand] = np.random.uniform(1.1, 1.8, rare_expand.sum())
output_size_mb  = np.clip(task_size_mb * output_ratio, 0.01, 2048.0)

# ── Arrival time (bursty + periodic + random) ──
#   Mix 3 arrival patterns:
#   60% exponential (random IoT), 30% burst clusters, 10% periodic
pattern = np.random.choice(["random","burst","periodic"], size=n, p=[0.60,0.30,0.10])

arrival_time = np.zeros(n, dtype=int)
arrival_time[pattern=="random"]   = np.random.exponential(150, (pattern=="random").sum())
arrival_time[pattern=="periodic"] = np.tile(
    np.arange(1, num_timesteps+1, 10),
    (pattern=="periodic").sum() // 100 + 1
)[:(pattern=="periodic").sum()]

# Burst: cluster around random centres
burst_centres = np.random.choice(num_timesteps, 20, replace=False)
burst_idx     = np.where(pattern=="burst")[0]
assigned_centre = np.random.choice(burst_centres, len(burst_idx))
arrival_time[burst_idx] = (
    assigned_centre + np.random.normal(0, 5, len(burst_idx))
).astype(int)

arrival_time = np.clip(arrival_time, 1, num_timesteps)

# ── Edge assignment (proximity-aware) ──
assigned_edge_id = np.random.randint(1, num_edges + 1, n)

# SPECIAL CASE 8: Devices prefer nearby edges (80% stay on same 5 edges) ──
sticky_mask = np.random.rand(n) < 0.80
sticky_edge = (device_id[sticky_mask] % num_edges) + 1
assigned_edge_id[sticky_mask] = sticky_edge

# ── Dependency flag (task chains) ──
has_dependency = (np.random.rand(n) < 0.15).astype(int)
depends_on_task = np.where(
    has_dependency,
    np.random.randint(1, n+1, n),
    0
)

# ── Retransmission count (0–3, higher with bad network) ──
retransmission_count = np.random.choice([0,1,2,3], n, p=[0.80,0.12,0.05,0.03])

# ── Task flags ──
is_real_time  = np.isin(task_type, ["voice","emergency","sensor"]).astype(int)
is_encrypted  = (security_sensitivity > 0.5).astype(int)
rejection_flag= np.zeros(n, dtype=int)

print("Task type distribution:")
print(pd.Series(task_type).value_counts())
print(f"\nCorrupt tasks   : {corrupt_mask.sum()}")
print(f"Emergency tasks : {emerg_mask.sum()}")
print(f"Firmware tasks  : {firm_mask.sum()}")
print(f"CPU spike tasks : {spike_mask.sum()}")
print(f"Low-battery     : {low_batt_mask.sum()}")
print(f"Impossible DL   : {impossible_mask.sum()}")
dataset_A = pd.DataFrame({
    "task_id":              task_id,
    "device_id":            device_id,
    "device_type":          device_type,
    "task_type":            task_type,
    "task_size_mb":         np.round(task_size_mb, 4),
    "output_size_mb":       np.round(output_size_mb, 4),
    "cpu_cycles":           np.round(cpu_cycles, 2),
    "memory_req_mb":        np.round(memory_req_mb, 2),
    "deadline_ms":          np.round(deadline_ms, 2),
    "priority_level":       priority_level,
    "security_sensitivity": np.round(security_sensitivity, 4),
    "energy_required":      np.round(energy_required, 4),
    "arrival_time":         arrival_time,
    "assigned_edge_id":     assigned_edge_id,
    "has_dependency":       has_dependency,
    "depends_on_task":      depends_on_task,
    "retransmission_count": retransmission_count,
    "is_real_time":         is_real_time,
    "is_encrypted":         is_encrypted,
    "is_corrupt":           corrupt_mask.astype(int),
    "is_low_battery":       low_batt_mask.astype(int),
    "impossible_deadline":  impossible_mask.astype(int),
    "rejection_flag":       rejection_flag,
})

dataset_A.to_csv(os.path.join(save_path, "dataset_A.csv"), index=False)
print(f"dataset_A saved  →  shape: {dataset_A.shape}")
print(dataset_A.describe().T[["mean","std","min","max"]])
# ==============================
# EDGE NODES
# ==============================
np.random.seed(10)

# Three tiers of edge nodes (micro / standard / powerful)
tier = np.random.choice(["micro","standard","powerful"], num_edges, p=[0.3,0.5,0.2])

cpu_cap = np.where(tier=="micro",    np.random.uniform(1000,3000,  num_edges),
          np.where(tier=="standard", np.random.uniform(4000,10000, num_edges),
                                     np.random.uniform(12000,30000,num_edges)))

mem_cap = np.where(tier=="micro",    np.random.uniform(2,  8,   num_edges),
          np.where(tier=="standard", np.random.uniform(8,  32,  num_edges),
                                     np.random.uniform(32, 128, num_edges)))

bw_cap  = np.where(tier=="micro",    np.random.uniform(50, 200,  num_edges),
          np.where(tier=="standard", np.random.uniform(200,600,  num_edges),
                                     np.random.uniform(600,2000, num_edges)))

edge_nodes = pd.DataFrame({
    "edge_id":                np.arange(1, num_edges + 1),
    "tier":                   tier,
    "edge_cpu_capacity":      np.round(cpu_cap, 1),
    "edge_memory_capacity":   np.round(mem_cap, 2),
    "edge_bandwidth_capacity":np.round(bw_cap,  1),
    "edge_energy_capacity":   np.round(np.random.uniform(1000, 8000, num_edges), 1),
    "is_renewable_powered":   (np.random.rand(num_edges) < 0.25).astype(int),
    "location_zone":          np.random.choice(
                                  ["urban","suburban","rural","industrial"],
                                  num_edges, p=[0.4,0.3,0.2,0.1]),
})

edge_nodes.to_csv(os.path.join(save_path, "edge_nodes.csv"), index=False)
print("edge_nodes saved")
print(edge_nodes["tier"].value_counts())
# ==============================
# NETWORK STATE
# ==============================
np.random.seed(20)
network_rows = []

# Pre-define special network events
outage_windows   = [(200,215), (600,605)]          # full outage windows
congestion_peaks = [100, 300, 500, 700, 900]       # periodic congestion
jitter_storm     = (400, 450)                       # high jitter period

for t in range(1, num_timesteps + 1):

    # ── Base packet loss ──
    packet_loss = np.random.beta(0.5, 10)           # mostly low, occasional spike

    # SPECIAL: random outage
    if any(s <= t <= e for s, e in outage_windows):
        packet_loss = np.random.uniform(0.5, 0.99)  # near-complete loss

    # SPECIAL: rare flash congestion (1% probability)
    if np.random.rand() < 0.01:
        packet_loss = np.random.uniform(0.15, 0.40)

    # ── Channel utilization (sinusoidal daily pattern + noise) ──
    time_of_day    = (t % 100) / 100.0
    chan_util_base = 0.3 + 0.5 * np.sin(2 * np.pi * time_of_day)  # daily cycle
    chan_util       = np.clip(chan_util_base + np.random.normal(0, 0.1), 0.05, 0.99)

    # SPECIAL: congestion peak
    if any(abs(t - cp) < 15 for cp in congestion_peaks):
        chan_util = min(chan_util + np.random.uniform(0.1, 0.35), 0.99)

    # ── Bandwidth (depends on utilization + loss) ──
    uplink   = max(10, 350 * (1 - packet_loss) * (1 - 0.6 * chan_util)
                    + np.random.normal(0, 15))
    downlink = max(10, uplink * np.random.uniform(1.2, 2.0)
                    + np.random.normal(0, 10))

    # Outage → near-zero bandwidth
    if any(s <= t <= e for s, e in outage_windows):
        uplink   = np.random.uniform(0.1, 2.0)
        downlink = np.random.uniform(0.1, 2.0)

    # ── Network delay ──
    delay_base = 5 + 80 * packet_loss + 40 * chan_util
    # SPECIAL: jitter storm → high variance delay
    if jitter_storm[0] <= t <= jitter_storm[1]:
        delay_base += np.random.exponential(80)
    delay = max(1.0, delay_base + np.random.normal(0, 8))

    # ── Load factor (for edge queue augmentation) ──
    load_factor = 1.0 + 0.5 * np.sin(2 * np.pi * t / 200)

    # ── SNR (signal quality) ──
    snr_db = np.random.normal(25, 8)
    if any(s <= t <= e for s, e in outage_windows):
        snr_db = np.random.uniform(-5, 5)
    snr_db = np.clip(snr_db, -10, 50)

    network_rows.append([
        t,
        round(uplink,   3),
        round(downlink, 3),
        round(delay,    3),
        round(packet_loss, 5),
        round(chan_util,   4),
        round(load_factor, 4),
        round(snr_db,      2),
        int(any(s <= t <= e for s, e in outage_windows)),    # is_outage
        int(any(abs(t-cp) < 15 for cp in congestion_peaks)), # is_congestion
        int(jitter_storm[0] <= t <= jitter_storm[1]),         # is_jitter_storm
    ])

network_state = pd.DataFrame(network_rows, columns=[
    "timestep", "uplink_bandwidth", "downlink_bandwidth",
    "network_delay_ms", "packet_loss_rate", "channel_utilization",
    "load_factor", "snr_db",
    "is_outage", "is_congestion", "is_jitter_storm"
])

network_state.to_csv(os.path.join(save_path, "network_state.csv"), index=False)
print("network_state saved")
print(f"Outage timesteps    : {network_state['is_outage'].sum()}")
print(f"Congestion timesteps: {network_state['is_congestion'].sum()}")
print(f"Jitter storm steps  : {network_state['is_jitter_storm'].sum()}")
# ==============================
# EDGE STATE
# ==============================
np.random.seed(30)

delay_map    = dict(zip(network_state["timestep"], network_state["network_delay_ms"]))
outage_map   = dict(zip(network_state["timestep"], network_state["is_outage"]))
congest_map  = dict(zip(network_state["timestep"], network_state["is_congestion"]))

# Pre-assign which edges have failures and when
edge_failure_schedule = {}   # edge_id → set of failed timesteps
for eid in range(1, num_edges + 1):
    if np.random.rand() < 0.15:   # 15% of edges experience at least one failure
        fail_start = np.random.randint(1, num_timesteps - 20)
        fail_dur   = np.random.randint(5, 30)
        edge_failure_schedule[eid] = set(range(fail_start, fail_start + fail_dur))

# Gradual degradation edges (wear-out model)
degrading_edges = set(
    np.random.choice(range(1, num_edges + 1),
                     size=int(num_edges * 0.10), replace=False)
)

edge_rows = []

for t in range(1, num_timesteps + 1):
    net_delay  = delay_map[t]
    is_outage  = outage_map[t]
    is_congest = congest_map[t]

    for eid in range(1, num_edges + 1):
        cap_cpu = edge_nodes.loc[eid-1, "edge_cpu_capacity"]
        cap_mem = edge_nodes.loc[eid-1, "edge_memory_capacity"]
        tier    = edge_nodes.loc[eid-1, "tier"]

        # ── Base utilization ──
        cpu_util = np.random.uniform(0.2, 0.75)
        mem_util = np.random.uniform(0.2, 0.70)
        queue    = np.random.poisson(lam=4)

        # ── Correlated with network congestion ──
        if net_delay > 70:
            queue    += np.random.randint(8, 25)
            cpu_util  = min(cpu_util + 0.15, 1.0)

        if is_congest:
            queue    += np.random.randint(5, 20)
            cpu_util  = min(cpu_util + 0.10, 1.0)

        # ── SPECIAL CASE A: Edge node failure (offline) ──
        if t in edge_failure_schedule.get(eid, set()):
            cpu_avail = 0.0
            mem_avail = 0.0
            queue     = 999          # sentinel for "node down"
            edge_rows.append([
                t, eid, 0.0, 0.0, 999,
                9999.0, 0.0, 1, 0, 0
            ])
            continue

        # ── SPECIAL CASE B: Gradual degradation ──
        if eid in degrading_edges:
            degradation = min(0.9, (t / num_timesteps) * 0.8)
            cpu_util    = min(cpu_util + degradation, 0.99)
            mem_util    = min(mem_util + degradation * 0.5, 0.99)

        # ── SPECIAL CASE C: Rare overload spike ──
        if np.random.rand() < 0.015:
            queue    += np.random.randint(30, 80)
            cpu_util  = min(cpu_util + 0.3, 1.0)

        # ── SPECIAL CASE D: Network outage → edge isolation ──
        if is_outage:
            # Edge still processes locally but can't offload further
            cpu_util = min(cpu_util + 0.20, 1.0)
            queue   += np.random.randint(10, 30)

        # ── Micro-edge nodes saturate faster ──
        if tier == "micro" and np.random.rand() < 0.05:
            cpu_util = min(cpu_util + 0.25, 1.0)
            queue   += np.random.randint(5, 15)

        cpu_avail   = max(0.0, cap_cpu * (1 - cpu_util))
        mem_avail   = max(0.0, cap_mem * (1 - mem_util))
        energy_lvl  = edge_nodes.loc[eid-1,"edge_energy_capacity"] * np.random.uniform(0.3,1.0)

        # Renewable edges replenish energy randomly
        if edge_nodes.loc[eid-1, "is_renewable_powered"]:
            energy_lvl = min(energy_lvl * np.random.uniform(1.0, 1.4),
                             edge_nodes.loc[eid-1, "edge_energy_capacity"])

        edge_rows.append([
            t, eid,
            round(cpu_avail, 2),
            round(mem_avail, 4),
            int(queue),
            round(np.random.uniform(3, 35), 2),
            round(energy_lvl, 2),
            0,                          # is_failed
            int(eid in degrading_edges),
            int(is_outage),
        ])

edge_state = pd.DataFrame(edge_rows, columns=[
    "timestep", "edge_id",
    "edge_cpu_available", "edge_memory_available",
    "edge_queue_length", "edge_latency_current",
    "edge_energy_level",
    "is_failed", "is_degrading", "is_isolated"
])

edge_state.to_csv(os.path.join(save_path, "edge_state.csv"), index=False)
print("edge_state saved")
print(f"Failed edge records   : {edge_state['is_failed'].sum()}")
print(f"Degrading edge records: {edge_state['is_degrading'].sum()}")
print(f"Isolated edge records : {edge_state['is_isolated'].sum()}")
# ==============================
# CLOUD NODES
# ==============================
np.random.seed(40)

cloud_region = np.random.choice(
    ["us-east","us-west","eu-central","ap-south","ap-east"],
    num_cloud, p=[0.30,0.20,0.25,0.15,0.10]
)

cloud_nodes = pd.DataFrame({
    "cloud_id":                  np.arange(1, num_cloud + 1),
    "region":                    cloud_region,
    "cloud_cpu_capacity":        np.round(np.random.uniform(20000, 80000, num_cloud), 1),
    "cloud_memory_capacity":     np.round(np.random.uniform(128, 512, num_cloud), 1),
    "cloud_bandwidth_capacity":  np.round(np.random.uniform(1000, 5000, num_cloud), 1),
    "sla_tier":                  np.random.choice(["gold","silver","bronze"],
                                     num_cloud, p=[0.3,0.5,0.2]),
})

cloud_nodes.to_csv(os.path.join(save_path, "cloud_nodes.csv"), index=False)
print("cloud_nodes saved")

# ==============================
# CLOUD STATE
# ==============================

# Pre-define cloud-level events
maintenance_windows = {
    1: [(300, 320)],   # cloud node 1 goes into maintenance
    5: [(600, 610)],
}
cloud_overload_prob = {cid: 0.01 + 0.01 * (cid % 3) for cid in range(1, num_cloud + 1)}

cloud_rows = []

for t in range(1, num_timesteps + 1):
    for cid in range(1, num_cloud + 1):

        cpu_util = np.random.uniform(0.15, 0.80)
        mem_util = np.random.uniform(0.20, 0.75)
        queue    = np.random.poisson(lam=8)

        # ── SPECIAL CASE: Maintenance window → node unavailable ──
        in_maint = any(
            s <= t <= e
            for s, e in maintenance_windows.get(cid, [])
        )
        if in_maint:
            cloud_rows.append([
                t, cid, 0.0, 0.0, 9999,
                9999.0, 1, 0, 0
            ])
            continue

        # ── SPECIAL CASE: Overload event ──
        if np.random.rand() < cloud_overload_prob[cid]:
            cpu_util  = np.random.uniform(0.90, 0.99)
            queue    += np.random.randint(80, 200)

        # ── SPECIAL CASE: Cold-start delay (rare) ──
        cold_start_latency = 0.0
        if np.random.rand() < 0.005:
            cold_start_latency = np.random.uniform(500, 2000)  # ms

        # ── Regional latency offset ──
        region_latency_offset = {
            "us-east": 20, "us-west": 35, "eu-central": 45,
            "ap-south": 80, "ap-east": 70
        }
        base_latency = (
            region_latency_offset[cloud_nodes.loc[cid-1, "region"]]
            + np.random.uniform(5, 30)
            + cold_start_latency
        )

        cap_cpu = cloud_nodes.loc[cid-1, "cloud_cpu_capacity"]
        cap_mem = cloud_nodes.loc[cid-1, "cloud_memory_capacity"]

        cloud_rows.append([
            t, cid,
            round(cap_cpu * (1 - cpu_util), 2),
            round(cap_mem * (1 - mem_util), 4),
            int(queue),
            round(base_latency, 2),
            0,                              # is_in_maintenance
            int(cpu_util > 0.90),           # is_overloaded
            int(cold_start_latency > 0),    # had_cold_start
        ])

cloud_state = pd.DataFrame(cloud_rows, columns=[
    "timestep", "cloud_id",
    "cloud_cpu_available", "cloud_memory_available",
    "cloud_queue_length", "cloud_latency_current",
    "is_in_maintenance", "is_overloaded", "had_cold_start"
])

cloud_state.to_csv(os.path.join(save_path, "cloud_state.csv"), index=False)
print("cloud_state saved")
print(f"Maintenance records : {cloud_state['is_in_maintenance'].sum()}")
print(f"Overload records    : {cloud_state['is_overloaded'].sum()}")
print(f"Cold-start records  : {cloud_state['had_cold_start'].sum()}")
# ==============================
# VALIDATION & SUMMARY
# ==============================
print("\n" + "="*55)
print("DATASET GENERATION COMPLETE — SUMMARY")
print("="*55)

files = {
    "dataset_A.csv":    dataset_A,
    "edge_nodes.csv":   edge_nodes,
    "network_state.csv":network_state,
    "edge_state.csv":   edge_state,
    "cloud_nodes.csv":  cloud_nodes,
    "cloud_state.csv":  cloud_state,
}

for fname, df in files.items():
    fpath = os.path.join(save_path, fname)
    size  = os.path.getsize(fpath) / 1024
    print(f"  {fname:<25} rows={len(df):>8,}  cols={df.shape[1]:>3}  "
          f"size={size:>8.1f} KB")

print("\n── Edge Cases Injected ──────────────────────────────")
print(f"  Corrupt tasks            : {dataset_A['is_corrupt'].sum():>6,}")
print(f"  Low-battery tasks        : {dataset_A['is_low_battery'].sum():>6,}")
print(f"  Impossible deadlines     : {dataset_A['impossible_deadline'].sum():>6,}")
print(f"  Emergency tasks          : {(dataset_A['task_type']=='emergency').sum():>6,}")
print(f"  Firmware updates         : {(dataset_A['task_type']=='firmware_update').sum():>6,}")
print(f"  Task dependencies        : {dataset_A['has_dependency'].sum():>6,}")
print(f"  Network outage steps     : {network_state['is_outage'].sum():>6,}")
print(f"  Network congestion steps : {network_state['is_congestion'].sum():>6,}")
print(f"  Jitter storm steps       : {network_state['is_jitter_storm'].sum():>6,}")
print(f"  Failed edge records      : {edge_state['is_failed'].sum():>6,}")
print(f"  Degrading edge records   : {edge_state['is_degrading'].sum():>6,}")
print(f"  Cloud maintenance records: {cloud_state['is_in_maintenance'].sum():>6,}")
print(f"  Cloud overload records   : {cloud_state['is_overloaded'].sum():>6,}")
print("="*55)