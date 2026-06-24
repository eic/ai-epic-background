# EIC AI Background

Full-simulation pipelines and CSV-based machine-learning datasets for the
ePIC detector at the Electron-Ion Collider.

## What is this project?

This site documents the **EIC AI Background** project — a set of tools for producing
and consuming background-rich datasets from full ePIC detector simulations, with a focus
on use cases for AI / ML training and physics studies of detector occupancy.

The work has three pillars:

1. **`full-sim-pipeline/`** — orchestration scripts that drive the ePIC simulation chain
   (`afterburner` → `npsim` → `EICrecon`) on the JLab farm and produce reconstructed
   `edm4eic` ROOT files for one or more beam-energy campaigns.
2. **`csv_convert/`** — a small C++/ROOT converter (`trk_hits_to_csv.cxx`) plus
   Snakemake workflow that flattens those ROOT files into CSV: one row per
   tracker hit with the linked `MCParticle` truth.
3. **`analyses/`** — standalone Python analyses on the produced CSVs. Each
   analysis lives in its own subfolder with its scripts and a short README.

The CSV output is deliberately simple so it can be consumed by Python, by LLM-generated
plotting scripts, or fed directly into a `torch.utils.data.Dataset` for ML training.

## Quick links

- [Full-Sim Pipeline overview](/full-sim-pipeline) — end-to-end ePIC simulation chain
  runnable on JLab SLURM with reproducible per-campaign configs.
- [Backgrounds](/background) — how signal events get mixed with the official ePIC
  background cocktails into 2 µs timeframes, with all the flags and references.
- [CSV Convert](/csv-convert) — lightweight C++/ROOT converter that turns edm4eic ROOT
  files into flat CSV with full hit, particle, and detector context.
- [AI / ML datasets](/ai-datasets) — tracker hits, MC truth, and detector tags packed
  into CSVs that load directly into pandas, numpy, or PyTorch dataloaders.
- [Available datasets](/data) — current background-mixed datasets on Rucio.
- [Data format](/data-format) — exact column layout produced by the converter.

## Pipeline at a glance

![HEPMC events → afterburner ROOT → edm4hep → edm4eic → CSV hits → AI/ML training and Python analysis](/diagrams/pipeline-overview.svg)

For the background-mixing step that sits between afterburner and `npsim`, see the
[Backgrounds](/background) page.

## Why CSV?

Tracker-hit CSVs are dead simple to produce in C++ (no extra dependencies beyond
`fmt::format`) and trivial to load anywhere downstream:

- `pandas.read_csv()` for exploration and plotting
- `numpy.loadtxt` / `pyarrow` for bulk numeric work
- A few lines of Python for `torch.utils.data.Dataset`
- LLM-generated analysis scripts, which work much more reliably on flat CSV than on
  EDM4EIC's PODIO graph

See the [Data Format](/data-format) page for the exact column layout produced by the
converter.

## Reproducibility

The entire chain is reproducible by design:

- Pinned `eic_xl` Singularity containers — every job runs in the same image.
- Snakemake workflows for the CSV-conversion step.
- One YAML campaign config per release, checked into the repo.

So any run can be re-executed at any time, against the exact container and detector
release it was originally produced with.

## Project structure

```
ai-epic-background/
├── csv_convert/              # ROOT → CSV converter + Snakemake workflow
│   ├── trk_hits_to_csv.cxx
│   ├── CMakeLists.txt
│   ├── Snakefile
│   ├── run_jlab_slurm.sh
│   └── pyproject.toml
├── analyses/                 # Python analyses (one subfolder each)
│   └── time-vs-z-plots/
│       └── background_analysis.py
├── full-sim-pipeline/        # ePIC simulation orchestration
│   ├── 10_create_afterburner_jobs.py
│   ├── 11_create_background_jobs.py
│   ├── 20_create_npsim_jobs.py
│   ├── 21_create_npsim_saveall_jobs.py
│   ├── 22_create_npsim_background_jobs.py
│   ├── 30_create_eicrecon_jobs.py
│   ├── 40_create_csv_dd4hep_jobs.py
│   ├── 41_create_csv_eicrecon_jobs.py
│   ├── 50_create_analysis_jobs.py
│   ├── job_creator.py
│   └── config-campaign-*.yaml
├── docs/                     # this VitePress site
└── .github/workflows/        # GitHub Pages deployment
```

## Where to start

- New here? Start with the [Full-Sim Pipeline overview](/full-sim-pipeline).
- Want to know how backgrounds are mixed? Go to [Backgrounds](/background).
- Looking for the data itself? See [Available datasets](/data).
- Just want flat CSV out of an existing ROOT file? Jump to [CSV Convert](/csv-convert).
