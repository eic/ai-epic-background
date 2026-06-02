#!/usr/bin/env python3
"""
42_create_datasets_list.py

Discover Rucio datasets for a campaign and write one small YAML per dataset
describing where its files live. This is the *input* step for the CSV
conversion: 41_create_csv_eicrecon_jobs.py reads these YAMLs and streams the
PFNs straight through the ROOT macros (no local copy of the .edm4eic.root).

What it does
------------
1. `rucio did list --filter <rucio_did_filters> <rucio_did_pattern>`
   -> the set of dataset DIDs for the campaign.
2. For each DID:
   `rucio replica list file --protocols root --pfns --rses isopenaccess <did>`
   -> the list of root:// PFNs that make up the dataset.
3. Writes `<datasets_dir>/<slug>.yaml`:

       did: epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/.../minQ2=1
       slug: Bkg_Exact1S_2us_DIS_NC_10x100_minQ2=1
       energy: 10x100
       n_files: 123
       files:
         - root://.../...1.0000.eicrecon.edm4eic.root
         - root://.../...1.0001.eicrecon.edm4eic.root

The directory tree of the DID is *not* mirrored. Each dataset collapses to a
single flat slug; the full DID is preserved inside the YAML so provenance is
never lost.

Config keys (campaign YAML)
---------------------------
    rucio_did_filters:   "is_background_mixed=true"
    rucio_did_pattern:   "epic:*RECO/26.04.1*"
    datasets_dir:        "${base_dir}/datasets"
    slug_drop_tokens:    ["GoldCt", "10um"]   # optional; tokens dropped from slug
    max_files_per_dataset: 0                   # optional; 0 = all files

Run inside eic-shell (or anywhere `rucio` is authenticated):
    python 42_create_datasets_list.py -c config-campaign-26-04.yaml
"""

import argparse
import os
import re
import subprocess
import sys
from glob import glob

import yaml

from job_creator import load_config

ENERGY_RE = re.compile(r"^\d+x\d+$")


def make_rucio_runner(container, bind_dirs):
    """Return a run(args) that executes `rucio <args>` inside the container.

    rucio is run via `singularity exec -B <d>:<d> ... <container> rucio ...`
    so the host does not need rucio on PATH.
    """
    bindings = []
    for d in bind_dirs:
        d = os.path.abspath(d)
        bindings += ["-B", f"{d}:{d}"]
    prefix = ["singularity", "exec", *bindings, container, "rucio"]

    def run(args):
        cmd = [*prefix, *args]
        print("  $ " + " ".join(cmd))
        try:
            out = subprocess.run(
                cmd, check=True, text=True, capture_output=True,
            ).stdout
        except FileNotFoundError:
            sys.exit("ERROR: 'singularity' not found on PATH.")
        except subprocess.CalledProcessError as e:
            sys.stderr.write(e.stdout or "")
            sys.stderr.write(e.stderr or "")
            sys.exit(f"ERROR: rucio command failed (exit {e.returncode}).")
        return out.splitlines()

    return run


def parse_did_lines(lines):
    """Pull DID strings out of rucio output (plain lines or ASCII table)."""
    dids = []
    for line in lines:
        line = line.strip()
        # New CLI prints plain DIDs; old CLI prints a '| epic:/... |' table.
        if line.startswith("|"):
            line = line.split("|", 2)[1].strip()
        if line.startswith("epic:/"):
            dids.append(line)
    return dids


def parse_pfn_lines(lines):
    """Keep only the root:// PFN lines from `rucio replica list ... --pfns`."""
    return [ln.strip() for ln in lines if ln.strip().startswith("root://")]


def did_to_slug(did, drop_tokens=()):
    """Collapse a DID into one flat, filesystem-safe slug.

    Everything after the detector-config segment (epic_craterlake) is joined
    with '_'. Tokens in `drop_tokens` (e.g. constant GoldCt/10um) are removed.
    The full DID is stored in the YAML, so this slug can be lossy/pretty.
    """
    assert did.startswith("epic:/"), did
    parts = did[len("epic:/"):].split("/")
    if "epic_craterlake" in parts:
        tail = parts[parts.index("epic_craterlake") + 1:]
    else:
        tail = parts[3:]  # skip RECO/<ver>/<det>
    drop = set(drop_tokens)
    tail = [p for p in tail if p and p not in drop]
    slug = "_".join(tail)
    # Keep alnum . _ = + - ; replace anything else.
    return re.sub(r"[^A-Za-z0-9._=+-]", "_", slug)


def energy_of(did):
    for p in did[len("epic:/"):].split("/"):
        if ENERGY_RE.match(p):
            return p
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-c", "--config", required=True, help="Campaign config YAML")
    parser.add_argument("--max-files", type=int, default=None,
                        help="Cap files per dataset (override config; 0 = all)")
    parser.add_argument("--clean", action="store_true",
                        help="Remove existing *.yaml in datasets_dir first")
    args = parser.parse_args()

    config = load_config(args.config)

    filters = config.get("rucio_did_filters", None)
    pattern = config.get("rucio_did_pattern", None)
    if not pattern:
        sys.exit("ERROR: config has no 'rucio_did_pattern'.")
    datasets_dir = config.get("datasets_dir", None)
    if not datasets_dir:
        sys.exit("ERROR: config has no 'datasets_dir'.")
    container = config.get("container", None)
    if not container:
        sys.exit("ERROR: config has no 'container'.")
    bind_dirs = list(config.get("bind_dirs", []))
    drop_tokens = list(config.get("slug_drop_tokens", []))
    max_files = args.max_files if args.max_files is not None \
        else int(config.get("max_files_per_dataset", 0))

    datasets_dir = os.path.abspath(datasets_dir)
    os.makedirs(datasets_dir, exist_ok=True)
    if args.clean:
        for f in glob(os.path.join(datasets_dir, "*.yaml")):
            os.remove(f)

    run_rucio = make_rucio_runner(container, bind_dirs)

    print("=" * 70)
    print("RUCIO DATASET DISCOVERY")
    print(f"  container: {container}")
    print(f"  binds:   {bind_dirs}")
    print(f"  filters: {filters}")
    print(f"  pattern: {pattern}")
    print(f"  output:  {datasets_dir}")
    if drop_tokens:
        print(f"  slug drops: {drop_tokens}")
    if max_files:
        print(f"  max files/dataset: {max_files}")
    print("=" * 70)

    did_args = ["did", "list"]
    if filters:
        did_args += ["--filter", str(filters)]
    did_args += [str(pattern)]
    dids = parse_did_lines(run_rucio(did_args))
    print(f"\nFound {len(dids)} dataset DIDs.\n")

    written = []
    for i, did in enumerate(dids, 1):
        slug = did_to_slug(did, drop_tokens)
        print(f"[{i}/{len(dids)}] {slug}")
        pfns = parse_pfn_lines(run_rucio(
            ["replica", "list", "file", "--protocols", "root",
             "--pfns", "--rses", "isopenaccess", did]
        ))
        if max_files:
            pfns = pfns[:max_files]
        if not pfns:
            print(f"      WARN: no PFNs for {did} -- skipping")
            continue

        out_path = os.path.join(datasets_dir, f"{slug}.yaml")
        with open(out_path, "w") as f:
            yaml.safe_dump(
                {
                    "did": did,
                    "slug": slug,
                    "energy": energy_of(did),
                    "n_files": len(pfns),
                    "files": pfns,
                },
                f, sort_keys=False, default_flow_style=False,
            )
        written.append(out_path)
        print(f"      {len(pfns)} files -> {out_path}")

    print("\n" + "=" * 70)
    print(f"Wrote {len(written)} dataset YAML(s) to {datasets_dir}")
    print("Next:")
    print(f"  python 41_create_csv_eicrecon_jobs.py -c {args.config}")
    print("=" * 70)


if __name__ == "__main__":
    main()
