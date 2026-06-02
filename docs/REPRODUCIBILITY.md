# Reproducibility Notes

## What Is Included

- Main notebook: `notebooks/v6.6.ipynb`
- Dataset generator: `src/data_generation/generate_dataset3.py`
- Dataset CSVs: `data/dataset3/*.csv`
- Manuscript-ready result exports: `results/exports/*.csv` and `*.json`
- IEEE Access manuscript source and compiled PDF: `paper/ieee_access/`
- Selected figures: `results/figures/`

## What Is Not Included

Long-running caches, model checkpoints, and notebook runtime scratch outputs are not included in this GitHub-ready package.

Excluded examples:

- `_v64_cache/`
- `_v66_cache/`
- `*.pt`
- `*.pkl`
- `*.npz`
- LaTeX auxiliary build files

## Running The Notebook

The packaged notebook copy uses a repository-local dataset path:

```text
data/dataset3
```

For a full rerun from scratch, cache-only flags inside the notebook may need to be disabled. The manuscript result exports are included separately so the paper results remain inspectable without retraining.

## Dataset Checksums

Use:

```text
results/exports/dataset_checksums.csv
```

for file sizes, row counts, schemas, and SHA-256 checksums generated during the manuscript export step.

## Paper Build

The IEEE Access LaTeX draft is under:

```text
paper/ieee_access/main.tex
```

The compiled paper snapshot is:

```text
paper/ieee_access/main.pdf
```

The root working project used bundled Tectonic during manuscript development. External LaTeX setups may need package/class adjustments depending on local configuration.
