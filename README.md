# Fed-DDQN Edge-Cloud IoT Offloading

Personal research-code repository for channel-aware task offloading and adaptive resource allocation in edge-cloud IoT systems. This is a research-related project package: it keeps the runnable code, generated datasets, experiment history, cached model artifacts, and result summaries together, while leaving paper drafts and publishing files outside the repo.

This repository contains the **code, dataset, scripts, exported metrics, and result figures** needed to inspect and rerun the project.

## Core Idea

The project studies a two-stage scheduling pipeline:

1. **Stage 1: Federated Double Deep Q-Network (Fed-DDQN)** for binary edge/cloud task offloading across non-IID edge zones.
2. **Stage 2: Rejection-aware residual resource allocator** for CPU, memory, and bandwidth assignment after a task is selected for edge execution.

The main proposed model is **Fed-DDQN**. Other methods are included as comparison baselines.

## Repository Structure

```text
data/dataset3/        Synthetic edge-cloud IoT benchmark CSVs and generator copy
data/old/             Earlier dataset snapshots used during development
notebooks/            Main experimental notebook and older notebook versions
src/data_generation/  Dataset generator and generator test
scripts/              Helper scripts for notebook and figure export work
results/exports/      CSV/JSON experiment outputs
results/figures/      Selected result figures
docs/                 Dataset, results, and reproducibility notes
```

## Dataset

`data/dataset3/` contains a real-world-inspired synthetic benchmark. It includes bursty arrivals, edge queue carryover, congestion, outage, jitter, edge degradation, cloud maintenance, low-battery tasks, emergency tasks, and firmware/update-style workload phases.

| File | Rows | Purpose |
|---|---:|---|
| `dataset_A.csv` | 100,000 | Task table |
| `edge_nodes.csv` | 50 | Static edge node table |
| `edge_state.csv` | 50,000 | Edge node state over 1,000 timesteps |
| `network_state.csv` | 1,000 | Network/channel state over time |
| `cloud_nodes.csv` | 10 | Static cloud node table |
| `cloud_state.csv` | 10,000 | Cloud node state over 1,000 timesteps |

The dataset is synthetic, not measured telemetry.

Earlier dataset snapshots are kept under `data/old/`:

- `data/old/Datasets/`
- `data/old/Datasets2/`

These are included for project history and comparison against the final Dataset3 benchmark.

## Main Results

The table below is copied from `results/exports/main_policy_comparison_test_only.csv`. It uses the valid held-out policy-evaluation subset with `N = 9,733`.

| Method | Avg. latency | SLA % | SLA miss % | Rejection % | Edge usage % |
|---|---:|---:|---:|---:|---:|
| DDQN | 144.926 | 97.49 | 2.51 | 3.90 | 73.71 |
| MTOSA | 231.841 | 89.71 | 10.29 | 11.52 | 25.50 |
| FL-DDPG | 138.373 | 97.67 | 2.33 | 3.74 | 71.23 |
| GTPSO | 203.551 | 90.36 | 9.64 | 10.89 | 10.62 |
| PTS-RA | 228.897 | 90.61 | 9.39 | 10.64 | 12.49 |
| JTOS | 207.521 | 90.54 | 9.46 | 10.71 | 18.30 |
| **Fed-DDQN (Proposed)** | **136.009** | **97.73** | **2.27** | **3.68** | **67.43** |
| Oracle | 123.310 | 97.99 | 2.01 | 3.43 | 69.27 |

Oracle is a non-trainable latency-reference rule over generated finite edge/cloud alternatives. It is not a deployable policy.

## Summary

- Fed-DDQN achieved **136.009 ms** average latency on the valid held-out policy-evaluation subset.
- Fed-DDQN reduced average latency by **6.15%** relative to centralized DDQN.
- Fed-DDQN reduced average latency by **1.71%** relative to the FL-DDPG-style baseline.
- Fed-DDQN reported **97.73% SLA satisfaction** and **3.68% rejection**.
- The latency-reference Oracle reached **123.310 ms**.

## Stage-2 Allocator

The resource allocator is evaluated after Stage 1 selects edge execution. It assigns normalized CPU, memory, and bandwidth shares under capacity constraints.

The exported results support this high-level readout:

- Rejection-Aware Demand has the lowest proxy-target MAE.
- Residual + Risk Projection has the best efficiency score, lowest under-allocation, and zero capacity violation.

See `results/exports/allocator_target_risk_spec.json` for target/risk details.

## Running

Install dependencies:

```powershell
pip install -r requirements.txt
```

Open the notebook:

```powershell
jupyter lab notebooks/v6.6.ipynb
```

The notebook copy resolves the dataset from `data/dataset3` when run from either the repository root or the `notebooks/` folder.

Quick-run caches are included under:

```text
data/dataset3/_v64_cache/
data/dataset3/_v66_cache/experiment_exports/
```

These cache files allow faster inspection and reruns when the notebook configuration matches the included Dataset3 snapshot. Use `results/exports/` to inspect saved output metrics without retraining.

Older notebook versions are stored in `notebooks/old/` for development history. The main current experiment entrypoint remains `notebooks/v6.6.ipynb`.

## Regenerating Dataset3

```powershell
python src/data_generation/generate_dataset3.py
```

Back up the included CSVs before overwriting them if you need to preserve this snapshot.

## Documentation

- `docs/DATASET_CARD.md`
- `docs/HISTORY_AND_CACHE.md`
- `docs/RESULTS_SUMMARY.md`
- `docs/REPRODUCIBILITY.md`
- `docs/REPOSITORY_STRUCTURE.md`

## License

No open-source license has been assigned yet. Treat this as a personal research-code repository.
