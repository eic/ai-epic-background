# Campaigns

A "campaign" is a coherent production run with a fixed container image, a fixed
beam-energy set, and a fixed output base directory. Each one lives in its own
YAML config under `full-sim-pipeline/`.

## Existing campaigns

| Config file                              | Notes                                              |
| ---------------------------------------- | -------------------------------------------------- |
| `config-campaign-25-10.yaml`             | October 2025 production                            |
| `config-campaign-26-03.yaml`             | March 2026 production                              |
| `config-campaign-26-04.yaml`             | April 2026 production (current default)            |
| `config-campaign-official_2026-02.yaml`  | Official ePIC central production reuse for Feb 2026 |

## Config layout

The configs follow a uniform schema. Excerpt from `config-campaign-26-04.yaml`:

```yaml
# Base directory — everything else is relative to this
base_dir: "/work/eic3/users/romanov/meson-structure-2026-04-check"

# Bind mounts inside the container
bind_dirs:
  - "${base_dir}"

# Container image (pin a stable tag for reproducibility)
container: "/work/eic3/users/romanov/meson-structure-work/eicdev-eic-full-2026-04-25.sif"

# Pipeline scripts directory
scripts_dir: "/work/eic3/users/romanov/meson-structure-work/meson-structure/full-sim-pipeline"

# Set true to render scripts without submitting
dry_run: false

# Beam-energy combinations to process (electron x proton GeV)
energies:
  - "5x41"
  - "10x100"
  - "10x130"
  - "18x275"

# Events per output file
event_count: 5000

# Per-stage I/O paths — note ${base_dir} and ${energy} substitution
dd4hep_input:  "${base_dir}/afterburner/${energy}-priority"
dd4hep_output: "${base_dir}/dd4hep/${energy}"

dd4hep_saveall_input:  "${base_dir}/afterburner/${energy}-priority"
dd4hep_saveall_output: "${base_dir}/dd4hep_saveall/${energy}"

csv_dd4hep_input:  "${dd4hep_output}"
csv_dd4hep_output: "${base_dir}/csv_dd4hep${suffix}/${energy}"
```

The variables `${base_dir}`, `${energy}`, and `${suffix}` are interpolated by the
Python job-creation scripts at render time.

## Starting a new campaign

1. Copy the most recent config (e.g. `cp config-campaign-26-04.yaml
   config-campaign-26-08.yaml`).
2. Update `base_dir` to your new output root.
3. Pin `container:` to whatever `eic_xl` tag you want to lock in.
4. Adjust `energies` and `event_count` if needed.
5. Run the stage scripts in order:

   ```bash
   python 10_create_afterburner_jobs.py --config config-campaign-26-08.yaml
   python 20_create_npsim_jobs.py       --config config-campaign-26-08.yaml
   python 30_create_eicrecon_jobs.py    --config config-campaign-26-08.yaml
   python 41_create_csv_eicrecon_jobs.py --config config-campaign-26-08.yaml
   ```

   Each one renders the per-input scripts and a SLURM submitter into
   `${base_dir}/<stage>/${energy}/...`.

6. Submit the SLURM submitter for each stage when its inputs are ready.

## "saveall" variant

`21_create_npsim_saveall_jobs.py` runs `npsim` with **all** sensitive volumes
saving hits — including the tracking volume itself. This produces dramatically
larger outputs but is what you want for background occupancy / AI training:
every Geant4 hit is preserved, not just the ones in normal readout volumes.

The `dd4hep_saveall_*` config keys point at this branch of the pipeline.
