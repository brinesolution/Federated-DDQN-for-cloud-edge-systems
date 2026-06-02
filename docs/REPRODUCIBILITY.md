# Reproducibility Notes

## What Is Included

- Main notebook: `notebooks/v6.6.ipynb`
- Dataset generator: `src/data_generation/generate_dataset3.py`
- Dataset CSVs: `data/dataset3/*.csv`
- Historical dataset snapshots: `data/old/`
- Historical notebooks: `notebooks/old/`
- Quick-run caches and model artifacts: `data/dataset3/_v64_cache/`
- Experiment result exports: `results/exports/*.csv` and `*.json`
- Selected figures: `results/figures/`

## What Is Not Included

Notebook runtime scratch outputs and publishing files are not included in this GitHub-ready package.

Excluded examples:

- paper draft folders
- PDFs
- LaTeX sources and build outputs
- temporary scratch folders

## Running The Notebook

The packaged notebook copy uses a repository-local dataset path:

```text
data/dataset3
```

For a full rerun from scratch, cache-only flags inside the notebook may need to be disabled. For faster inspection, keep the default cache-aware configuration and use the included `data/dataset3/_v64_cache/` artifacts. The exported result files are included separately so key metrics remain inspectable without retraining.

## Dataset Checksums

Use:

```text
results/exports/dataset_checksums.csv
```

for file sizes, row counts, schemas, and SHA-256 checksums generated during the experiment export step.
