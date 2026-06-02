# Repository Structure

```text
fed-ddqn-edge-cloud-iot/
├── README.md
├── requirements.txt
├── data/
│   ├── dataset3/
│   │   ├── _v64_cache/
│   │   └── _v66_cache/
│   └── old/
├── docs/
├── notebooks/
│   ├── v6.6.ipynb
│   └── old/
├── results/
│   ├── exports/
│   └── figures/
├── scripts/
└── src/
    └── data_generation/
```

## Folder Roles

- `data/dataset3/`: benchmark data, generator copy, and quick-run cache files.
- `data/old/`: earlier dataset snapshots retained for development history.
- `notebooks/`: main experimental notebook plus older notebook versions.
- `src/data_generation/`: dataset generator and generator validation test.
- `scripts/`: helper scripts copied from the working project.
- `results/exports/`: CSV/JSON experiment outputs.
- `results/figures/`: selected reader-facing figures.
- `docs/`: dataset, result, and reproducibility documentation.

See `docs/HISTORY_AND_CACHE.md` for the historical notebook/dataset inventory
and quick-run cache notes.

This Git-ready package is focused on reproducible research code, data, scripts,
selected figures, exported experiment metrics, historical notebook/dataset
versions, and quick-run caches. Paper drafts, PDFs, LaTeX sources, reference
bundles, and publishing folders are intentionally not part of this package.
