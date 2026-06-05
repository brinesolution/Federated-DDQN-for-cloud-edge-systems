# Reproducibility Notes

## What Is Included

- Main notebook: `notebooks/v6.6.ipynb`
- Dataset generator: `src/data_generation/generate_dataset3.py`
- Dataset CSVs: `data/dataset3/*.csv`
- Historical dataset snapshots: `data/old/`
- Historical notebooks: `notebooks/old/`
- Cached model artifacts and quick-run caches: `data/dataset3/_v64_cache/`
- Experiment result exports: `results/exports/*.csv` and `*.json`
- Selected figures: `results/figures/`

## What Is Not Included

Notebook scratch outputs and publication files are not included in this repository.

Excluded examples:

- paper draft folders
- PDFs
- LaTeX sources and build outputs
- temporary scratch folders

## Running The Notebook

The notebook uses a repository-local dataset path:

```text
data/dataset3
```

For a full rerun from scratch, some cache-only flags inside the notebook may need to be disabled. For faster inspection, keep the default cache-aware configuration and use the included `data/dataset3/_v64_cache/` artifacts. The exported result files are also included so the main metrics can be inspected without retraining.

## Dataset Checksums

Use:

```text
results/exports/dataset_checksums.csv
```

for file sizes, row counts, schemas, and SHA-256 checksums generated during the export step.
