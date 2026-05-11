# Snakemake & SLURM

The `Snakefile` under `csv_convert/` runs `trk_hits_to_csv.cxx` over all
`*.edm4eic.root` files in a chosen input directory and writes one CSV per input,
then zips each result into a parallel `csv-zip/` tree.

## Configuring paths

The Snakefile reads the output base from the `OUT_BASE` environment variable. If
it's missing, the workflow errors with a helpful message:

```bash
export OUT_BASE="/volatile/eic/$USER/25.10.4_bkg-1signal-2us-frame_dis-nc_10x100_minq2-1"
```

The current default `INPUT_DIR` is hard-coded near the top of the Snakefile to:

```
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_1SignalPer2usFrame/DIS/NC/10x100/minQ2=1
```

Edit this value if you want to point at a different campaign.

## Container

The workflow runs each rule inside the ePIC nightly Singularity image:

```
/cvmfs/singularity.opensciencegrid.org/eicweb/eic_xl:nightly
```

Pin to a stable tag (e.g. `25.10.x-stable`) for reproducible production runs.

## Setup

We use [`uv`](https://docs.astral.sh/uv/) for Python deps:

```bash
cd csv_convert
uv sync
```

This installs `snakemake`, `pandas`, `matplotlib`, and the `cluster-generic`
executor plugin used for SLURM submission.

## Running locally

Dry run (shows what would execute):

```bash
uv run snakemake -n
```

Run with 8 cores inside the container:

```bash
uv run snakemake --cores 8 \
  --use-singularity \
  --singularity-args "--bind /volatile:/volatile --bind /cvmfs:/cvmfs"
```

## Running on SLURM (JLab)

The simplest way is the bundled helper script:

```bash
./run_jlab_slurm.sh /volatile/eic/$USER/25.10.4_bkg-1signal-2us-frame_dis-nc_10x100_minq2-1
```

It exports `OUT_BASE`, ensures the log directory exists, and then submits
Snakemake to the SLURM `production` partition with up to 2000 concurrent jobs.

If you want full control, the equivalent manual invocation is:

```bash
OUT_BASE="/volatile/eic/$USER/25.10.4_bkg-1signal-2us-frame_dis-nc_10x100_minq2-1"
LOGS="${OUT_BASE}/logs"
mkdir -p "$LOGS"

uv run snakemake \
  --executor cluster-generic --jobs 2000 \
  --cluster-generic-submit-cmd "sbatch \
    --account=eic \
    --partition=production \
    --cpus-per-task={threads} \
    --mem=4000 \
    --time=01:00:00 \
    --output=${LOGS}/slurm-%j.out \
    --error=${LOGS}/slurm-%j.err" \
  --use-singularity \
  --singularity-args "--bind /volatile:/volatile --bind /cvmfs:/cvmfs"
```

## Outputs

After a successful run, `OUT_BASE` looks like:

```
$OUT_BASE/
├── csv/<sample>.csv          # one row per tracker hit
├── csv-zip/<sample>.csv.zip  # zipped CSVs (smaller, friendlier for transfer)
└── logs/<sample>.hits.log    # per-job logs
```

Inputs are matched against `*.edm4eic.root`; the basename (minus the suffix) becomes
`<sample>`. The Snakefile slices to the first 100 inputs by default — adjust the
`inputs = inputs[:100]` line if you want more.

## Prerequisites

- `uv` for Python package management
- `apptainer` / `singularity` on compute nodes
- Access to `/cvmfs` and `/volatile` (JLab farm)
- SLURM for batch mode
