# Historical Versions And Cache Notes

This repository is a research-code package, so it keeps the development history that is useful for understanding how the Fed-DDQN experiment evolved.

## Notebook History

The main notebook is:

```text
notebooks/v6.6.ipynb
```

Older notebook versions are retained under:

```text
notebooks/old/
```

Included versions:

- `federated_ddqn_v4_improved.ipynb`
- `federated_ddqn_v5_final.ipynb`
- `6.0.ipynb`
- `6.1.ipynb`
- `v6.2.ipynb`
- `v6.3.ipynb`
- `v6.4.ipynb`
- `v6.5_multiseed_albation.ipynb`

Use these only for development timeline/context. The current reproducible experiment entrypoint is `notebooks/v6.6.ipynb`.

## Dataset History

The current benchmark is:

```text
data/dataset3/
```

Earlier dataset snapshots are retained under:

```text
data/old/Datasets/
data/old/Datasets2/
```

These folders preserve the previous CSV schemas and generation scripts/notebooks that were used before the final Dataset3 benchmark.

## Included Quick-Run Cache

The current notebook is cache-aware and can reuse artifacts from:

```text
data/dataset3/_v64_cache/
```

This folder includes cached features, labels, trained model checkpoints, baseline checkpoints, policy-evaluation artifacts, allocator artifacts, and multi-seed/ablation outputs. It is included so another user can inspect or rerun much of the notebook faster when the dataset snapshot and flags match.

Small experiment-export cache files are also kept under:

```text
data/dataset3/_v66_cache/experiment_exports/
```

These files mirror the exported CSV/JSON result artifacts in a cache-style location.

## What Is Still Kept Out

This package does not include paper drafts, PDFs, LaTeX source trees, reference bundles, or publishing-specific folders. Those remain outside the GitHub-ready research-code repository.
