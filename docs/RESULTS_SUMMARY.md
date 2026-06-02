# Results Summary

This file summarizes the exported experiment results stored under `results/exports/`.

## Main Comparison

Evaluation subset: valid held-out policy-evaluation rows, `N = 9,733`.

| Method | Avg. latency | SLA % | Rejection % | Edge usage % |
|---|---:|---:|---:|---:|
| DDQN | 144.926 | 97.49 | 3.90 | 73.71 |
| MTOSA | 231.841 | 89.71 | 11.52 | 25.50 |
| FL-DDPG | 138.373 | 97.67 | 3.74 | 71.23 |
| GTPSO | 203.551 | 90.36 | 10.89 | 10.62 |
| PTS-RA | 228.897 | 90.61 | 10.64 | 12.49 |
| JTOS | 207.521 | 90.54 | 10.71 | 18.30 |
| Fed-DDQN (Proposed) | 136.009 | 97.73 | 3.68 | 67.43 |
| Oracle | 123.310 | 97.99 | 3.43 | 69.27 |

## Main Claims Supported By These Exports

- Fed-DDQN gives the lowest average latency among the implemented main comparison methods.
- The Fed-DDQN latency is 6.15% lower than centralized DDQN.
- The Fed-DDQN latency is 1.71% lower than the FL-DDPG-style comparator.
- The proposed method keeps SLA and rejection behavior close to the latency-reference Oracle while remaining deployable/trainable.

## Fed-DDQN Ablation Summary

Three-seed ablation exports show that the proposed configuration is a balanced design across latency, SLA, rejection, edge usage, validation score, and rounds run.

The action-aware pressure variant can slightly reduce latency, but the proposed configuration is retained for the balanced validation-selected tradeoff.

See `results/exports/fed_ddqn_ablation_summary.csv`.

## Stage-2 Resource Allocation

Stage 2 is evaluated only for allocator-valid edge-selected tasks. Its role is resource assignment after Stage 1 chooses edge.

The allocator export summary:

- Rejection-Aware Demand has the lowest proxy-target MAE.
- Residual + Risk Projection has the best efficiency score, lowest under-allocation, and zero capacity violation.

See `results/exports/allocator_target_risk_spec.json`.
