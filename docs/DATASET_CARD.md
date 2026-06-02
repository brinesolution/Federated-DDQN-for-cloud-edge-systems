# Dataset Card

## Name

Dataset3 edge-cloud IoT benchmark.

## Type

Real-world-inspired synthetic dataset. It is not measured deployment telemetry.

## Purpose

The dataset supports comparison of edge-cloud task offloading and resource allocation methods under bursty workload, network, edge, and cloud stress.

## Files

| File | Rows | Columns | Role |
|---|---:|---:|---|
| `data/dataset3/dataset_A.csv` | 100,000 | 23 | Task records |
| `data/dataset3/edge_nodes.csv` | 50 | 8 | Static edge node metadata |
| `data/dataset3/edge_state.csv` | 50,000 | 10 | Per-edge state over time |
| `data/dataset3/network_state.csv` | 1,000 | 11 | Per-timestep network state |
| `data/dataset3/cloud_nodes.csv` | 10 | 6 | Static cloud node metadata |
| `data/dataset3/cloud_state.csv` | 10,000 | 9 | Per-cloud state over time |

## Scenario Coverage

The generator includes:

- normal traffic,
- burst windows,
- emergency tasks,
- firmware/update windows,
- industrial telemetry surges,
- video/AI-heavy traffic,
- congestion,
- outage,
- jitter storms,
- edge degradation/failure,
- cloud maintenance,
- low-battery and corrupt-task cases.

## Intended Use

Use this dataset to evaluate relative behavior of edge/cloud offloading policies under a fixed offline benchmark. It is suitable for algorithm comparison, ablation, and paper figures.

## Limitations

- The benchmark is synthetic.
- The notebook uses an offline exogenous-transition evaluation sequence: policy actions affect current-task reward and metrics, but do not mutate future CSV queue/state rows.
- Closed-loop queue mutation and measured deployment traces remain future extensions.
