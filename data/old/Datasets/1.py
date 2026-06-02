import numpy as np
import pandas as pd
import os

np.random.seed(42)

# ==============================
# CONFIG
# ==============================
n = 100000
num_edges = 50
num_cloud = 10
num_timesteps = 1000
num_devices = 5000

save_path = r"C:\Users\mayan\Desktop\3STSEM\ai\model"
os.makedirs(save_path, exist_ok=True)

print("Saving to:", save_path)

# ==============================
# TASK GENERATION
# ==============================

task_id = np.arange(1, n+1)

# Heavy-tailed sizes
small = np.random.lognormal(mean=1.0, sigma=0.9, size=int(n*0.85))
medium = np.random.uniform(10, 200, int(n*0.13))
large = np.random.uniform(200, 1024, n - len(small) - len(medium))

task_size_mb = np.concatenate([small, medium, large])
np.random.shuffle(task_size_mb)
task_size_mb = np.clip(task_size_mb, 0.1, 1024)

# Task types
task_types = ["sensor", "image", "ai", "video"]
task_type = np.random.choice(task_types, size=n, p=[0.5,0.25,0.15,0.10])

# Output size
output_ratio = np.random.normal(0.5, 0.2, n)
rare_expand = np.random.rand(n) < 0.05
output_ratio[rare_expand] = np.random.uniform(1.1,1.8,np.sum(rare_expand))
output_size_mb = np.clip(task_size_mb * output_ratio, 0.05, 1500)

# CPU cycles
cpu_cycles = task_size_mb * np.random.uniform(900,1600,n)

# Adjust by task type
cpu_cycles[task_type=="sensor"] *= 0.5
cpu_cycles[task_type=="image"] *= 1.5
cpu_cycles[task_type=="ai"] *= 3
cpu_cycles[task_type=="video"] *= 2

# Memory
memory_req_mb = task_size_mb * np.random.uniform(1.0,2.5,n)

# Device modeling
device_id = np.random.randint(1, num_devices+1, n)
device_type = np.random.choice(
    ["mobile","sensor","iot","edge_device"],
    size=n,
    p=[0.3,0.3,0.2,0.2]
)

# Priority
priority_level = np.zeros(n)
priority_level[task_size_mb < 5] = np.random.choice([1,2], size=np.sum(task_size_mb < 5), p=[0.7,0.3])
priority_level[(task_size_mb >= 5) & (task_size_mb < 100)] = np.random.choice([1,2,3], size=np.sum((task_size_mb >= 5) & (task_size_mb < 100)), p=[0.4,0.4,0.2])
priority_level[task_size_mb >= 100] = np.random.choice([2,3], size=np.sum(task_size_mb >= 100), p=[0.3,0.7])
priority_level = priority_level.astype(int)

# Deadline (improved realism)
deadline_base = np.random.uniform(200,2000,n)
deadline_ms = deadline_base / priority_level
deadline_ms -= cpu_cycles * 0.01
deadline_ms = np.clip(deadline_ms, 50, None)

# Security
security_sensitivity = np.clip(priority_level * np.random.uniform(0.2,0.5,n),0,1)

# Energy
energy_required = cpu_cycles * np.random.uniform(0.0004,0.0012,n)

# Bursty arrival
arrival_time = np.random.exponential(scale=150,size=n)
burst_mask = np.random.rand(n) < 0.1
arrival_time[burst_mask] *= 0.3
arrival_time = np.clip(arrival_time.astype(int),1,num_timesteps)

# Assign edge
assigned_edge_id = np.random.randint(1,num_edges+1,n)

# Placeholder rejection
rejection_flag = np.zeros(n)

# ==============================
# SAVE TASK DATASET
# ==============================

dataset_A = pd.DataFrame({
    "task_id": task_id,
    "device_id": device_id,
    "device_type": device_type,
    "task_type": task_type,
    "task_size_mb": task_size_mb,
    "output_size_mb": output_size_mb,
    "cpu_cycles": cpu_cycles,
    "memory_req_mb": memory_req_mb,
    "deadline_ms": deadline_ms,
    "priority_level": priority_level,
    "security_sensitivity": security_sensitivity,
    "energy_required": energy_required,
    "arrival_time": arrival_time,
    "assigned_edge_id": assigned_edge_id,
    "rejection_flag": rejection_flag
})

dataset_A.to_csv(os.path.join(save_path, "dataset_A.csv"), index=False)
print("dataset_A saved")

# ==============================
# EDGE NODES
# ==============================

edge_nodes = pd.DataFrame({
    "edge_id": np.arange(1,num_edges+1),
    "edge_cpu_capacity": np.random.uniform(4000,12000,num_edges),
    "edge_memory_capacity": np.random.uniform(8,32,num_edges),
    "edge_bandwidth_capacity": np.random.uniform(100,1000,num_edges),
    "edge_energy_capacity": np.random.uniform(2000,6000,num_edges)
})

edge_nodes.to_csv(os.path.join(save_path,"edge_nodes.csv"), index=False)

# ==============================
# NETWORK STATE
# ==============================

network_state = []

for t in range(1, num_timesteps+1):

    packet_loss = np.random.uniform(0.0,0.05)
    if np.random.rand() < 0.01:
        packet_loss = np.random.uniform(0.1,0.3)

    channel_utilization = np.random.uniform(0.3,0.9)

    uplink = 300 - packet_loss*200
    uplink *= (1 - 0.5*channel_utilization)

    downlink = uplink
    delay = np.random.uniform(5,80) + packet_loss*100

    network_state.append([
        t, max(uplink,50), max(downlink,50),
        delay, packet_loss, channel_utilization
    ])

network_state = pd.DataFrame(network_state, columns=[
    "timestep","uplink_bandwidth","downlink_bandwidth",
    "network_delay_ms","packet_loss_rate","channel_utilization"
])

network_state.to_csv(os.path.join(save_path,"network_state.csv"), index=False)

# ==============================
# EDGE STATE (CORRELATED)
# ==============================

edge_state = []
delay_map = dict(zip(network_state["timestep"], network_state["network_delay_ms"]))

for t in range(1, num_timesteps+1):
    for i in range(num_edges):

        cpu_util = np.random.uniform(0.3,0.9)
        mem_util = np.random.uniform(0.2,0.85)
        queue_length = np.random.poisson(lam=5)

        # correlated congestion
        if delay_map[t] > 70:
            queue_length += np.random.randint(10,30)
            cpu_util = min(cpu_util + 0.1, 1.0)

        # rare overload
        if np.random.rand() < 0.02:
            queue_length += np.random.randint(20,50)

        edge_state.append([
            t, i+1,
            edge_nodes.loc[i,"edge_cpu_capacity"]*(1-cpu_util),
            edge_nodes.loc[i,"edge_memory_capacity"]*(1-mem_util),
            queue_length,
            np.random.uniform(5,30),
            edge_nodes.loc[i,"edge_energy_capacity"]*np.random.uniform(0.4,1.0)
        ])

edge_state = pd.DataFrame(edge_state, columns=[
    "timestep","edge_id","edge_cpu_available",
    "edge_memory_available","edge_queue_length",
    "edge_latency_current","edge_energy_level"
])

edge_state.to_csv(os.path.join(save_path,"edge_state.csv"), index=False)

# ==============================
# CLOUD STATE
# ==============================

cloud_nodes = pd.DataFrame({
    "cloud_id": np.arange(1,num_cloud+1),
    "cloud_cpu_capacity": np.random.uniform(20000,60000,num_cloud),
    "cloud_memory_capacity": np.random.uniform(64,256,num_cloud),
    "cloud_bandwidth_capacity": np.random.uniform(500,2000,num_cloud)
})

cloud_nodes.to_csv(os.path.join(save_path,"cloud_nodes.csv"), index=False)

cloud_state = []

for t in range(1, num_timesteps+1):
    for i in range(num_cloud):

        cpu_util = np.random.uniform(0.2,0.85)
        mem_util = np.random.uniform(0.3,0.8)
        queue_length = np.random.poisson(lam=10)

        if np.random.rand() < 0.01:
            queue_length += np.random.randint(50,100)

        cloud_state.append([
            t, i+1,
            cloud_nodes.loc[i,"cloud_cpu_capacity"]*(1-cpu_util),
            cloud_nodes.loc[i,"cloud_memory_capacity"]*(1-mem_util),
            queue_length,
            np.random.uniform(20,100)
        ])

cloud_state = pd.DataFrame(cloud_state, columns=[
    "timestep","cloud_id","cloud_cpu_available",
    "cloud_memory_available","cloud_queue_length",
    "cloud_latency_current"
])

cloud_state.to_csv(os.path.join(save_path,"cloud_state.csv"), index=False)

print("ALL DATASETS GENERATED SUCCESSFULLY")