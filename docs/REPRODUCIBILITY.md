# Reproducibility Notes

## What Is Included

- Main notebook: `notebooks/v6.6.ipynb`
- Dataset generator: `src/data_generation/generate_dataset3.py`
- Dataset CSVs: `data/dataset3/*.csv`
- Experiment result exports: `results/exports/*.csv` and `*.json`
- Selected figures: `results/figures/`

## What Is Not Included

Long-running caches, model checkpoints, and notebook runtime scratch outputs are not included in this GitHub-ready package.

Excluded examples:

- `_v64_cache/`
- `_v66_cache/`
- `*.pt`
- `*.pkl`
- `*.npz`

## Running The Notebook

The packaged notebook copy uses a repository-local dataset path:

```text
data/dataset3
```

For a full rerun from scratch, cache-only flags inside the notebook may need to be disabled. The exported result files are included separately so key metrics remain inspectable without retraining.

## Dataset Checksums

Use:

```text
results/exports/dataset_checksums.csv
```

for file sizes, row counts, schemas, and SHA-256 checksums generated during the experiment export step.
