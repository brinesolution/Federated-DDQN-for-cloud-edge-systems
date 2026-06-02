# Federated DDQN Edge-Cloud IoT Offloading Research

Personal research project for channel-aware task offloading and rejection-aware resource allocation in edge-cloud IoT systems.

The core contribution is a two-stage scheduling pipeline:

1. **Stage 1: Federated Double Deep Q-Network (Fed-DDQN)** for binary edge/cloud task offloading across non-IID edge zones.
2. **Stage 2: Rejection-aware residual resource allocator** for CPU, memory, and bandwidth assignment after a task is selected for edge execution.

The comparison models are included only as baselines. The proposed model is **Fed-DDQN**.

## Repository Contents

```text
data/dataset3/                 Real-world-inspired synthetic benchmark CSVs and generator
notebooks/v6.6.ipynb           Main experimental notebook
src/data_generation/           Dataset generator and generator test
scripts/                       Notebook/build helper scripts
results/exports/               Manuscript-ready CSV/JSON result exports
results/figures/               Selected result figures
paper/ieee_access/             IEEE Access LaTeX draft source and compiled PDF
docs/                          Project context, manuscript plan, sync ledger, dataset card
```

## Dataset

The dataset is synthetic but deployment-inspired. It contains bursty arrivals, edge queue carryover, congestion, outage, jitter, edge degradation, cloud maintenance, low-battery tasks, emergency tasks, and firmware/update-style workload phases.

Main files:

| File | Rows | Purpose |
|---|---:|---|
| `dataset_A.csv` | 100,000 | Task table |
| `edge_nodes.csv` | 50 | Static edge node table |
| `edge_state.csv` | 50,000 | Edge node state over 1,000 timesteps |
| `network_state.csv` | 1,000 | Network/channel state over time |
| `cloud_nodes.csv` | 10 | Static cloud node table |
| `cloud_state.csv` | 10,000 | Cloud node state over 1,000 timesteps |

The dataset is **not measured telemetry**. It should be described as realistic synthetic or real-world-inspired synthetic data.

## Main Test Results

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

Oracle is a non-trainable latency-reference rule over generated finite edge/cloud alternatives. It is not a deployable policy and not a universal QoS ceiling.

## Key Result Summary

- Fed-DDQN achieved **136.009 ms** average latency on the valid held-out policy-evaluation subset.
- Fed-DDQN reduced average latency by **6.15%** relative to centralized DDQN.
- Fed-DDQN reduced average latency by **1.71%** relative to the FL-DDPG-style baseline.
- Fed-DDQN reported **97.73% SLA satisfaction** and **3.68% rejection**.
- The latency-reference Oracle reached **123.310 ms**, leaving measurable latency headroom.
- Stage 2 evaluates allocation only on the allocator-valid edge-selected subset.

## Stage-2 Allocator Summary

The resource allocator is evaluated after Stage 1 selects edge execution. It does not change the offloading decision. It assigns normalized CPU, memory, and bandwidth shares under capacity constraints.

Important manuscript wording:

- Rejection-Aware Demand gives the lowest proxy-target MAE.
- Residual + Risk Projection gives the best efficiency score, lowest under-allocation, and zero capacity violation.
- Allocator claims are proxy-target gains on the allocator-valid edge-selected subset.

See `results/exports/allocator_target_risk_spec.json` and the paper tables for the detailed allocator target/risk specification.

## Running The Project

Install a Python environment with the packages listed in `requirements.txt`.

```powershell
pip install -r requirements.txt
```

Open the notebook:

```powershell
jupyter lab notebooks/v6.6.ipynb
```

The packaged notebook copy resolves the dataset from `data/dataset3` when run from either the repository root or the `notebooks/` folder.

Model checkpoints and long-run training caches are intentionally not included. The result exports under `results/exports/` preserve the manuscript-ready numerical outputs.

## Regenerating Dataset3

```powershell
python src/data_generation/generate_dataset3.py
```

The original generator was copied from `dataset3/code.py`. Before overwriting included CSVs, back them up if you need to preserve the manuscript snapshot.

## Paper Draft

The active IEEE Access draft is included under:

```text
paper/ieee_access/
```

Important files:

- `paper/ieee_access/main.tex`
- `paper/ieee_access/main.pdf`
- `paper/ieee_access/sections/`
- `paper/ieee_access/tables/`
- `paper/ieee_access/figures/`

## Reproducibility Notes

See:

- `docs/DATASET_CARD.md`
- `docs/REPRODUCIBILITY.md`
- `results/exports/reproducibility_manifest.json`
- `results/exports/dataset_checksums.csv`

## License

No open-source license has been assigned yet. Treat this as a personal research repository pending publication decisions.
