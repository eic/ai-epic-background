# Full-Sim Pipeline

`full-sim-pipeline/` orchestrates the full ePIC simulation chain end-to-end:
from generator-level HEPMC files, through afterburner beam effects, through
`npsim` (Geant4) detector simulation, through `EICrecon` reconstruction, and
finally to CSV files for downstream analysis.

It is implemented as a small set of **Python job-creation scripts** that consume a
single per-campaign YAML config and emit one Singularity-wrapped script per input
file plus a SLURM submitter script.

## Pipeline stages

![Full-sim pipeline stages: HEPMC → convert → afterburner → npsim (edm4hep, plus saveall all-hits branch) → EICrecon (edm4eic) → dd4hep and eicrecon CSV → analysis](/diagrams/full-sim-pipeline.svg)

## Scripts

| Script                                | Purpose                                                   |
| ------------------------------------- | --------------------------------------------------------- |
| `01_root_hepmc_klam_convert.py`       | ROOT → HEPMC for KLam events                              |
| `02_root_hepmc_pin_convert.py`        | ROOT → HEPMC for π⁻ events                                |
| `10_create_afterburner_jobs.py`       | Apply beam-effects afterburner to HEPMC                   |
| `20_create_npsim_jobs.py`             | Run `npsim` (DD4hep + Geant4) detector simulation         |
| `21_create_npsim_saveall_jobs.py`     | Same as above, but keeping **all** hits incl. tracking volumes |
| `30_create_eicrecon_jobs.py`          | Run `EICrecon` reconstruction                             |
| `40_create_csv_dd4hep_jobs.py`        | Convert `edm4hep` → CSV (sim level)                       |
| `41_create_csv_eicrecon_jobs.py`      | Convert `edm4eic` → CSV (reco level)                      |
| `50_create_analysis_jobs.py`          | Run physics analysis on CSV                               |
| `51_create_root_analysis_jobs.py`     | Run physics analysis directly on ROOT                     |
| `collect_job_stats.py`                | Aggregate timings / exit codes across a campaign          |
| `job_creator.py`                      | Shared `JobCreator` class — see [Job Creator](/full-sim-pipeline-jobs) |

Each `NN_create_*_jobs.py` is the same shape: load the YAML config, walk the input
files, render one container script per input, and emit a SLURM submitter script.

## Configuration

Each campaign has its own YAML file:

- `config-campaign-25-10.yaml`
- `config-campaign-26-03.yaml`
- `config-campaign-26-04.yaml`
- `config-campaign-official_2026-02.yaml`

These files set the campaign's base directory, container image, beam energies,
event count, and per-stage input/output paths. See the
[Campaigns page](/full-sim-pipeline-campaigns) for details and conventions.

## Continue reading

- [Job Creator](/full-sim-pipeline-jobs) — the shared `JobCreator` class.
- [Campaigns](/full-sim-pipeline-campaigns) — config-file conventions, list of
  campaigns, and how to start a new one.
