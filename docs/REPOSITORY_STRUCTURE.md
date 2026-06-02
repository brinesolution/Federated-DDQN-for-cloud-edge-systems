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
├── paper/
│   └── ieee_access/
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
- `results/exports/`: CSV/JSON outputs used by the paper.
- `results/figures/`: selected reader-facing figures.
- `paper/ieee_access/`: active IEEE Access source/PDF snapshot.
- `docs/`: project context and reproducibility documentation.
