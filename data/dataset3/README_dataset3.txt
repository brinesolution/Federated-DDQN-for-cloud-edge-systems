Dataset3 - Realistic Synthetic Edge-Cloud IoT Dataset
=========================================================

Dataset3 keeps the exact CSV schemas used by Datasets2, but changes the data
generation semantics to be closer to real deployment behavior.

Files:
- dataset_A.csv
- edge_nodes.csv
- edge_state.csv
- network_state.csv
- cloud_nodes.csv
- cloud_state.csv
- code.py
- README_dataset3.txt

Schema compatibility:
All six CSV files keep the same column names and column counts as Datasets2.
The active notebook can use Dataset3 by changing only base_path to this folder.

Realism upgrades:
- time-correlated arrivals with normal, burst, emergency, firmware, industrial,
  and media/AI-heavy windows
- per-timestep workload pressure that affects network delay, packet loss, SNR,
  edge queues, edge CPU/memory availability, cloud queues, and cloud latency
- queue carryover across timesteps for edge and cloud state
- clustered edge failures and gradual degradation
- maintenance-driven cloud load shifts
- cold starts after idle-to-burst transitions
- outage, congestion, and jitter propagation across multiple signals
- dependencies mostly point to earlier tasks instead of arbitrary task IDs

Important limitation:
Dataset3 approximates race conditions through precomputed contention signals.
The notebook environment still reads fixed CSV state, so true policy-action-driven
state mutation would require changing the RL environment separately.

Intended score movement:
Scenario coverage        : 8/10   -> 9/10
Statistical realism      : 6.5/10 -> 8/10
Fault/stress realism     : 7.5/10 -> 8.5/10
Race-condition realism   : 2/10   -> 6.5/10
Real deployment closeness: 6/10   -> 7.5/10
Comparison fairness      : 7/10   -> 8/10
