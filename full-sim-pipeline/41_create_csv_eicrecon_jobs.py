#!/usr/bin/env python3
"""
41_create_csv_eicrecon_jobs.py
Generate and submit CSV conversion jobs using JobCreator.

Reads the per-dataset YAMLs written by 42_create_datasets_list.py and streams
each dataset's root:// PFNs through the ROOT macros to produce CSV outputs.
There is no local-file mode: to "convert a local directory", make a dataset
YAML that lists those files (see 42_create_datasets_list.py).
"""

import argparse
import os
import re
from glob import glob
from typing import Dict
import textwrap
from job_creator import JobCreator, load_config, write_top_master_scripts

this_dir = os.path.dirname(os.path.abspath(__file__))
csv_convert_dir_default = os.path.join(os.path.dirname(this_dir), 'csv_convert')


def create_container_script_template():
    """Create container job template for CSV conversion (simple & readable)."""
    return textwrap.dedent("""\
    #!/bin/bash
    set -euo pipefail

    echo "= CSV CONVERSION ============================================================"
    echo "  Input: {input_file}"
    echo "  Macros dir: {csv_convert_dir}"
    echo "==========================================================================="

    cd "{csv_convert_dir}"

    zip_csv() {{
      # Compress "$1" -> "$1.zip" (max deflate, level 9), verify the archive,
      # then delete the original CSV. On any failure: keep the CSV, drop the
      # partial zip, and return non-zero. Never deletes a CSV whose zip did
      # not verify.
      local csv="$1" zip="$1.zip"
      if python3 -c "import os,sys,zipfile; c,z=sys.argv[1],sys.argv[2]; f=zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9); f.write(c,os.path.basename(c)); f.close(); v=zipfile.ZipFile(z); sys.exit(1 if v.testzip() is not None or not v.namelist() else 0)" "$csv" "$zip" && [ -s "$zip" ]; then
        echo "[ZIP] $csv -> $zip (deflate-9, verified); removing CSV"
        rm -f "$csv"
      else
        echo "[ERR] zip failed for $csv; keeping CSV, removing partial zip"
        rm -f "$zip"
        return 1
      fi
    }}

    convert() {{
      local label="$1" macro="$2" out="$3"

      if [ ! -f "$out" ]; then
        echo "[RUN] $label via $macro"
        root -x -l -b -q "$macro(\\"{input_file}\\",\\"$out\\")"
      else
        echo "[SKIP] $label CSV exists"
      fi

      if [ -f "$out" ] && [ ! -f "$out.zip" ]; then
        zip_csv "$out"
      else
        echo "[SKIP] $label zip exists or CSV missing"
      fi
    }}

    convert "trk_hits" "trk_hits.cxx" "{trk_hits_csv}"
    convert "mc_particles" "mc_particles.cxx" "{mc_particles_csv}"
    convert "reco_particles" "reco_particles.cxx" "{reco_particles_csv}"

    echo "==========================================================================="
    echo "Done. Outputs in: {input_dir}"
    """)



def csv_file_id(input_file):
    """Short, unique CSV id from a root filename: its trailing file index.

    The name ends in "<divergence>.<index>", e.g. "..._hiDiv_1.0000" where the
    "1" belongs to hiDiv_1 and ".0000" is the file index. We keep only the
    index (the last digit run after the dot):

        pythia8NCDIS_..._hiDiv_1.0000.eicrecon.edm4eic.root -> "0000"

    Within a dataset files differ only by this index, so it is unique.
    Falls back to the full stripped basename if no trailing number is found.
    """
    name = os.path.basename(input_file)
    for suffix in ('.eicrecon.edm4eic.root', '.edm4eic.root', '.root'):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    m = re.search(r'(\d+)$', name)
    return m.group(1) if m else name


def make_custom_params_updater(config_path):
    """Create a custom params updater with access to the config path."""
    # Load once: the updater runs per input file, and re-parsing the config
    # YAML thousands of times is a real cost.
    config = load_config(config_path)

    def custom_params_updater(params: Dict) -> Dict:
        """Add custom parameters for CSV conversion."""
        input_file = params['input_file']
        input_dir = os.path.dirname(input_file)
        output_dir = params['output_dir']
        file_id = csv_file_id(input_file)

        params['csv_convert_dir'] = config.get('csv_convert_dir', csv_convert_dir_default)
        params['input_dir'] = input_dir
        params['trk_hits_csv'] = os.path.join(output_dir, f"{file_id}.trk_hits.csv")
        params['mc_particles_csv'] = os.path.join(output_dir, f"{file_id}.mc_particles.csv")
        params['reco_particles_csv'] = os.path.join(output_dir, f"{file_id}.reco_particles.csv")

        return params
    return custom_params_updater


def build_dataset_creator(config, slug, files, output_base, config_path):
    """Build a JobCreator for one dataset (streamed root:// PFNs).

    Output (and per-dataset jobs/logs) land under <output_base>/<slug>.
    """
    csv_convert_dir = config.get('csv_convert_dir', csv_convert_dir_default)
    output_dir = os.path.join(output_base, slug)

    bind_dirs = config.bind_dirs.copy() if 'bind_dirs' in config else []
    if csv_convert_dir not in bind_dirs:
        bind_dirs.append(csv_convert_dir)

    runner = JobCreator(
        input_files=list(files),
        # CSV paths are computed by the params updater from output_dir; this
        # func only needs to return something sane per file.
        output_file_name_func=lambda input_file, output_dir: output_dir,
        output_dir=output_dir,
        bind_dirs=bind_dirs,
        events=config.event_count,
        container=config.container,
        beam_config=slug,
        slurm_files_per_job=int(config.get('slurm_files_per_job', 20)),
    )
    runner.container_script_template = create_container_script_template()
    runner.container_script_params_updater = make_custom_params_updater(config_path)
    runner.run()
    return runner


def main():
    parser = argparse.ArgumentParser(
        description="Generate CSV conversion jobs from dataset YAMLs.")
    parser.add_argument('-c', '--config', required=True, help="Path to config YAML file")
    args = parser.parse_args()

    config = load_config(args.config)
    datasets_dir = os.path.abspath(config.datasets_dir)
    output_base = os.path.abspath(config.csv_eicrecon_output)

    yamls = sorted(glob(os.path.join(datasets_dir, '*.yaml')))
    if not yamls:
        raise SystemExit(
            f"No dataset YAMLs in {datasets_dir}. "
            f"Run 42_create_datasets_list.py -c {args.config} first.")

    print(f"Datasets: {len(yamls)} YAML(s) in {datasets_dir}")
    print(f"Output base: {output_base}")

    creators = []
    for y in yamls:
        ds = load_config(y)
        files = list(ds.get('files', []))
        if not files:
            print(f"  Skipping {os.path.basename(y)}: no files")
            continue
        print(f"\n--- {ds.slug} ({len(files)} files) ---")
        creators.append(
            build_dataset_creator(config, ds.slug, files, output_base, config_path=args.config)
        )

    write_top_master_scripts(creators, top_dir=output_base)
    print("ALL DATASETS PROCESSED SUCCESSFULLY")


if __name__ == "__main__":
    main()
