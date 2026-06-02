# Repository Structure

```text
fed-ddqn-edge-cloud-iot/
├── README.md
├── requirements.txt
├── data/
│   └── dataset3/
├── docs/
├── notebooks/
│   └── v6.6.ipynb
├── results/
│   ├── exports/
│   └── figures/
├── scripts/
└── src/
    └── data_generation/
```

## Folder Roles

- `data/dataset3/`: benchmark data and generator copy.
- `notebooks/`: main experimental notebook.
- `src/data_generation/`: dataset generator and generator validation test.
- `scripts/`: helper scripts copied from the working project.
- `results/exports/`: CSV/JSON experiment outputs.
- `results/figures/`: selected reader-facing figures.
- `docs/`: dataset, result, and reproducibility documentation.

This Git-ready package is focused on reproducible code, data, scripts, selected
figures, and exported experiment metrics. Model checkpoints and runtime caches
are left out to keep the repository clone-friendly.
