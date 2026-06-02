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
import shlex
import subprocess
import sys
from glob import glob

import yaml

from job_creator import load_config

ENERGY_RE = re.compile(r"^\d+x\d+$")       # 10x100
FRAME_LEN_RE = re.compile(r"^\d+us$")      # 2us
MINQ2_RE = re.compile(r"minQ2=(\S+)")
Q2_ALT_RE = re.compile(r"q2_(\w+)")
GEN_RE = re.compile(r"^([A-Za-z]+\d*)")    # pythia8  (from pythia8NCDIS...)
XANGLE_RE = re.compile(r"xAngle=(-?\d+(?:\.\d+)?)")
DIV_RE = re.compile(r"(hiDiv|loDiv)(?:_(\d+))?")

# Token -> canonical value mappings (extend as new conventions appear).
DATA_TYPE = {"RECO": "reconstructed", "FULL": "simulated"}
FRAME_TYPE = {"Exact1S": "1sig-per-fr"}
PROCESS = {"DIS": "dis", "SIDIS": "sidis"}
INTERACTION = {"NC": "nc", "CC": "cc"}


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
        # Quote for display only; execution uses the argv list (no shell), so
        # the literal '*' is passed straight to rucio for server-side matching.
        print("  $ " + " ".join(shlex.quote(c) for c in cmd))
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


META_LINE_RE = re.compile(r"^(\w+):\s*(.*)$")


def _convert_meta_value(raw):
    """Coerce a rucio metadata string value to None / bool / int / float / str."""
    v = raw.strip()
    if v == "" or v == "None":
        return None
    if v == "True":
        return True
    if v == "False":
        return False
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


def parse_rucio_metadata(lines, drop_none=True):
    """Parse `rucio did metadata list --plugin ALL` aligned `key:  value` output.

    Splits on the first ':' only (so datetime values keep their colons) and
    type-converts each value. None-valued keys are dropped by default to keep
    the data card tidy.
    """
    meta = {}
    for line in lines:
        m = META_LINE_RE.match(line.rstrip())
        if not m:
            continue
        val = _convert_meta_value(m.group(2))
        if drop_none and val is None:
            continue
        meta[m.group(1)] = val
    return meta


def fetch_rucio_metadata(run_rucio, did):
    """Return the rucio metadata dict for one DID (via the container runner)."""
    return parse_rucio_metadata(
        run_rucio(["did", "metadata", "list", "--plugin", "ALL", did]))


def parse_metadata(did, sample_file=None):
    """Extract structured metadata from a DID (+ a sample filename).

    Example DID:
      epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1
    Example file:
      ...pythia8NCDIS_10x100_minQ2=1_beamEffects_xAngle=-0.025_hiDiv_1.0000.eicrecon.edm4eic.root

    Returns a dict; unknown tokens fall back to a lowercased form rather than
    failing, so new conventions degrade gracefully (the full DID is also kept).
    """
    assert did.startswith("epic:/"), did
    parts = did[len("epic:/"):].split("/")
    partition = parts[0]
    tail = parts[3:]  # everything after RECO/<campaign>/<detector>

    meta = {
        "data_type": DATA_TYPE.get(partition, partition.lower()),
        "campaign": parts[1] if len(parts) > 1 else None,
        "detector": parts[2] if len(parts) > 2 else None,
        "has_background": False,
    }

    # --- background segment, e.g. "Bkg_Exact1S_2us" ---
    for tok in tail:
        sub = tok.split("_")
        if sub[0] == "Bkg":
            meta["has_background"] = True
            for s in sub[1:]:
                if FRAME_LEN_RE.match(s):
                    meta["frame_len"] = s
                elif s in FRAME_TYPE:
                    meta["frame_type"] = FRAME_TYPE[s]
                else:
                    meta.setdefault("frame_type", s.lower())
            break

    # --- beampipe, e.g. "GoldCt/10um" -> gold-coat-10um ---
    if "GoldCt" in tail:
        i = tail.index("GoldCt")
        thick = tail[i + 1] if i + 1 < len(tail) else None
        meta["beampipe"] = "gold-coat" + (f"-{thick}" if thick else "")

    # --- physics process / interaction (DIS, NC, ...) ---
    process = next((PROCESS[t] for t in tail if t in PROCESS), None)
    interaction = next((INTERACTION[t] for t in tail if t in INTERACTION), None)

    # --- beam energy ---
    meta["beam_energy"] = next((t for t in tail if ENERGY_RE.match(t)), None)

    # --- q2 ("minQ2=1" -> gt-1, "q2_100" -> gt-100) ---
    m = MINQ2_RE.search(did) or Q2_ALT_RE.search(did)
    meta["q2"] = f"gt-{m.group(1)}" if m else None

    # --- generator + beam effects from a sample filename ---
    generator = "pythia8"
    if sample_file:
        fn = os.path.basename(sample_file)
        gm = GEN_RE.match(fn)
        if gm:
            generator = gm.group(1).lower()
        meta["beam_effects"] = "beamEffects" in fn
        xm = XANGLE_RE.search(fn)
        if xm:
            meta["beam_crossing_angle"] = float(xm.group(1))
        dm = DIV_RE.search(fn)
        if dm:
            meta["beam_divergence"] = dm.group(1).lower() + \
                (f"_{dm.group(2)}" if dm.group(2) else "")
    meta["generator"] = generator

    # --- physics = generator-interaction-process (e.g. pythia8-nc-dis) ---
    if process:
        bits = [generator] + ([interaction] if interaction else []) + [process]
        meta["physics"] = "-".join(bits)

    return meta


def rename_token(tok):
    """Tidy a single DID path token for use in a slug (no '=' in names)."""
    m = re.fullmatch(r"minQ2=(\S+)", tok)
    if m:
        return f"q2-gt-{m.group(1)}"   # minQ2=1 -> q2-gt-1
    return tok


def did_to_slug(did):
    """Flatten the DID path into one directory slug that mirrors the DID.

    Everything after the detector segment (epic_craterlake) is kept and joined
    with '_', so the slug stays close to the DID and it's obvious which dataset
    a directory came from. Only light tidying is applied (e.g. minQ2=1 ->
    q2-gt-1); '=' and other odd chars never appear in the name.

      .../Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1
      -> Bkg_Exact1S_2us_GoldCt_10um_DIS_NC_10x100_q2-gt-1
    """
    assert did.startswith("epic:/"), did
    parts = did[len("epic:/"):].split("/")
    if "epic_craterlake" in parts:
        tail = parts[parts.index("epic_craterlake") + 1:]
    else:
        tail = parts[3:]  # skip RECO/<campaign>/<detector>
    slug = "_".join(rename_token(t) for t in tail if t)
    # Allow alnum . _ - only; anything else (incl. '=') becomes '_'.
    return re.sub(r"[^A-Za-z0-9._-]", "_", slug)


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
        print(f"[{i}/{len(dids)}] {did}")
        pfns = parse_pfn_lines(run_rucio(
            ["replica", "list", "file", "--protocols", "root",
             "--pfns", "--rses", "isopenaccess", did]
        ))
        if max_files:
            pfns = pfns[:max_files]
        if not pfns:
            print(f"      WARN: no PFNs for {did} -- skipping")
            continue

        meta = parse_metadata(did, sample_file=pfns[0])
        slug = did_to_slug(did)
        rucio_meta = fetch_rucio_metadata(run_rucio, did)

        out_path = os.path.join(datasets_dir, f"{slug}.yaml")
        with open(out_path, "w") as f:
            yaml.safe_dump(
                {
                    "did": did,
                    "slug": slug,
                    "metadata": meta,
                    "rucio_metadata": rucio_meta,
                    "n_files": len(pfns),
                    "files": pfns,
                },
                f, sort_keys=False, default_flow_style=False,
            )
        written.append(out_path)
        print(f"      {slug}  ({len(pfns)} files) -> {out_path}")

    print("\n" + "=" * 70)
    print(f"Wrote {len(written)} dataset YAML(s) to {datasets_dir}")
    print("Next:")
    print(f"  python 41_create_csv_eicrecon_jobs.py -c {args.config}")
    print("=" * 70)


if __name__ == "__main__":
    main()
