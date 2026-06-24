#!/usr/bin/env python3
"""
Script: csv_particle_analyses.py

MC truth analysis for *all* MCParticles dumped by trk_particles_to_csv.cxx.

Two kinds of plots:

  1. Kinematic / vertex distributions (momentum, pT, pz, eta, theta, energy,
     mass, vertex z/r) as manually-defined `hist.Hist` histograms with explicit,
     tunable binning. Each one is drawn twice: combined, and split/overlaid by
     particle origin (signal / background / Geant4 secondaries).

  2. Status-code *bar charts*. generatorStatus and simulatorStatus are sparse,
     categorical codes (1, 2, 2001, 2002, ... and bit-packed sim flags), so a
     histogram with continuous bins is the wrong tool -- we count the distinct
     values and draw a labelled bar per code instead.

Usage:
    python csv_particle_analyses.py -o out_dir file1.csv file2.csv
    python csv_particle_analyses.py -o plots data/*.particles.csv

Dependencies:
    pip install pandas numpy matplotlib hist mplhep
"""

import argparse
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import hist
from hist import Hist
from hist.axis import Regular as Axis

warnings.filterwarnings('ignore')

# Optional: HEP styling
try:
    import mplhep as hep
    plt.style.use(hep.style.ROOT)
except ImportError:
    print("Note: mplhep not installed, using default matplotlib style")


###############################################################################
# Origin codes (must match get_origin_status in trk_particles_to_csv.cxx)
###############################################################################

ORIGIN_LABELS = {
    0: "unknown",
    1: "signal",
    2: "g4-from-signal",
    3: "background",
    4: "g4-from-bg",
}

# Stable colour per origin so every overlay is consistent.
ORIGIN_COLORS = {
    0: "#7f7f7f",
    1: "#4878d0",
    2: "#6acc64",
    3: "#d65f5f",
    4: "#ee854a",
}

# EDM4hep MCParticle.simulatorStatus bit positions (see edm4hep/MCParticle.h).
SIM_STATUS_BITS = {
    30: "createdInSimulation",
    29: "backscatter",
    28: "vtxNotEndpointOfParent",
    27: "decayedInTracker",
    26: "decayedInCalorimeter",
    25: "leftDetector",
    24: "stopped",
    23: "overlay",
}


###############################################################################
# Histogram definitions  (tune limits here)
###############################################################################

def create_histograms():
    """All kinematic histograms, explicit names + predefined binning."""
    h = {}
    h['p']       = Hist(Axis(100,   0.0,  50.0, name="p",     label=r"$|\vec{p}|$ [GeV/c]"))
    h['pt']      = Hist(Axis(100,   0.0,  10.0, name="pt",    label=r"$p_T$ [GeV/c]"))
    h['pz']      = Hist(Axis(120, -20.0,  50.0, name="pz",    label=r"$p_z$ [GeV/c]"))
    h['eta']     = Hist(Axis(100,  -8.0,   8.0, name="eta",   label=r"$\eta$"))
    h['theta']   = Hist(Axis(90,    0.0, 180.0, name="theta", label=r"$\theta$ [deg]"))
    h['energy']  = Hist(Axis(100,   0.0,  50.0, name="energy", label=r"$E$ [GeV]"))
    h['mass']    = Hist(Axis(100,   0.0,   5.0, name="mass",  label=r"mass [GeV/c$^2$]"))
    h['vtx_z']   = Hist(Axis(200, -5000.0, 5000.0, name="vtx_z", label=r"vertex $z$ [mm]"))
    h['vtx_r']   = Hist(Axis(150,   0.0, 2000.0, name="vtx_r", label=r"vertex $r$ [mm]"))
    return h


# Which columns each histogram is filled from.
HIST_COLUMN = {
    'p': 'p', 'pt': 'pt', 'pz': 'prt_mom_z', 'eta': 'eta', 'theta': 'theta',
    'energy': 'prt_energy', 'mass': 'prt_mass', 'vtx_z': 'prt_vtx_pos_z', 'vtx_r': 'vtx_r',
}


###############################################################################
# Data loading
###############################################################################

def concat_csvs_with_unique_events(files):
    """Load and concatenate CSV files with globally unique event IDs."""
    dfs = []
    offset = 0
    for file in files:
        print(f"  Reading: {file}")
        if str(file).endswith('.zip'):
            df = pd.read_csv(file, compression='zip')
        else:
            df = pd.read_csv(file)
        df['evt'] = df['evt'] + offset
        offset = df['evt'].max() + 1
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def add_derived_columns(df):
    """Compute momentum magnitude, pT, eta, theta and vertex radius."""
    px, py, pz = df['prt_mom_x'], df['prt_mom_y'], df['prt_mom_z']
    df['p']  = np.sqrt(px**2 + py**2 + pz**2)
    df['pt'] = np.sqrt(px**2 + py**2)
    df['theta'] = np.degrees(np.arctan2(df['pt'], pz))
    df['eta'] = np.where(df['p'] > np.abs(pz), np.arctanh(pz / df['p']), np.nan)
    df['vtx_r'] = np.sqrt(df['prt_vtx_pos_x']**2 + df['prt_vtx_pos_y']**2)
    return df


###############################################################################
# Plot: kinematic 1D, combined and split-by-origin
###############################################################################

def _stats_text(values, edges):
    total = values.sum()
    if total == 0:
        return ""
    centers = (edges[:-1] + edges[1:]) / 2
    mean = np.average(centers, weights=values)
    std  = np.sqrt(np.average((centers - mean)**2, weights=values))
    return f"Entries: {int(total)}\nMean: {mean:.3g}\nStd: {std:.3g}"


def plot_kinematic_combined(key, hdef, series, out_dir):
    """Single combined histogram over all particles."""
    vals = series.dropna().values
    if len(vals) == 0:
        return
    h = hdef.copy()
    h.reset()
    h.fill(vals)

    fig, ax = plt.subplots(figsize=(10, 6))
    h.plot1d(ax=ax, linewidth=2, color="#4878d0")
    stats = _stats_text(h.values(), h.axes[0].edges)
    if stats:
        ax.text(0.95, 0.95, stats, transform=ax.transAxes, va='top', ha='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), fontsize=11)
    ax.set_xlabel(h.axes[0].label or h.axes[0].name)
    ax.set_ylabel("Counts")
    ax.set_title(f"{key} (all particles)")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = out_dir / f"kin_{key}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")


def plot_kinematic_by_origin(key, hdef, df, col, out_dir):
    """Overlay one histogram per origin."""
    fig, ax = plt.subplots(figsize=(10, 6))
    any_filled = False
    for origin, label in ORIGIN_LABELS.items():
        sub = df[df['prt_origin'] == origin][col].dropna().values
        if len(sub) == 0:
            continue
        h = hdef.copy()
        h.reset()
        h.fill(sub)
        h.plot1d(ax=ax, linewidth=1.8, color=ORIGIN_COLORS[origin],
                 label=f"{label} ({len(sub)})")
        any_filled = True
    if not any_filled:
        plt.close()
        return
    ax.set_xlabel(hdef.axes[0].label or hdef.axes[0].name)
    ax.set_ylabel("Counts")
    ax.set_title(f"{key} by origin")
    ax.set_yscale('log')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = out_dir / f"kin_{key}_by_origin.png"
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")


###############################################################################
# Plot: categorical bar charts (sparse status codes)
###############################################################################

def plot_value_counts_bar(series, title, xlabel, out_path, top=None, as_str=True):
    """Bar chart of distinct values of *series* (categorical, sparse)."""
    counts = series.value_counts().sort_index()
    if top is not None:
        counts = series.value_counts().nlargest(top).sort_index()
    if counts.empty:
        return

    labels = [str(i) for i in counts.index] if as_str else list(counts.index)
    fig, ax = plt.subplots(figsize=(max(8, 0.5 * len(labels) + 4), 6))
    bars = ax.bar(labels, counts.values, color="#4878d0", edgecolor='black', linewidth=0.8)
    total = counts.values.sum()
    for bar in bars:
        h = bar.get_height()
        pct = 100.0 * h / total if total else 0
        ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}\n({pct:.1f}%)",
                ha='center', va='bottom', fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.set_yscale('log')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


def plot_origin_bar(df, out_path):
    """Bar chart of particle counts per origin code."""
    counts = df['prt_origin'].value_counts().reindex(ORIGIN_LABELS.keys(), fill_value=0)
    labels = [f"{code}\n{ORIGIN_LABELS[code]}" for code in counts.index]
    colors = [ORIGIN_COLORS[code] for code in counts.index]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, counts.values, color=colors, edgecolor='black', linewidth=1.0)
    total = counts.values.sum()
    for bar in bars:
        h = bar.get_height()
        pct = 100.0 * h / total if total else 0
        ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}\n({pct:.1f}%)",
                ha='center', va='bottom', fontsize=10)
    ax.set_ylabel("Count")
    ax.set_title("Particles per origin")
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, max(counts.values) * 1.15 if counts.values.max() else 1)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


def plot_sim_status_bits(df, out_path):
    """Bar chart of how many particles have each simulatorStatus bit set."""
    sim = df['prt_sim_status'].fillna(0).astype(np.int64)
    names, fractions = [], []
    for bit, name in sorted(SIM_STATUS_BITS.items()):
        n = int(((sim >> bit) & 1).sum())
        names.append(f"{name}\n(bit {bit})")
        fractions.append(n)
    if not any(fractions):
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(names, fractions, color="#6acc64", edgecolor='black', linewidth=0.8)
    total = len(sim)
    for bar in bars:
        h = bar.get_height()
        pct = 100.0 * h / total if total else 0
        ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}\n({pct:.1f}%)",
                ha='center', va='bottom', fontsize=9)
    ax.set_ylabel("Particles with bit set")
    ax.set_title("simulatorStatus bit flags")
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


###############################################################################
# Main
###############################################################################

def main():
    parser = argparse.ArgumentParser(description="MC truth particle analysis from trk_particles_to_csv CSV files")
    parser.add_argument('-o', '--output', type=str, default='csv_particle_plots', help='Output directory')
    parser.add_argument('-b', '--beam', type=str, default=None, help='Beam configuration (e.g. 10x100)')
    parser.add_argument('-e', '--events', type=int, default=None, help='Max number of events to process')
    parser.add_argument('files', nargs='+', help='Input particle CSV files')
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("MC Truth Particle Analysis")
    if args.beam:
        print(f"Beam: {args.beam}")
    print("=" * 70)

    print("\nLoading CSV files...")
    df = concat_csvs_with_unique_events([Path(f) for f in args.files])

    if args.events is not None:
        keep = sorted(df['evt'].unique())[:args.events]
        df = df[df['evt'].isin(keep)]
        print(f"Limiting to {args.events} events")

    print(f"Total particles: {len(df)}  in {df['evt'].nunique()} events")

    df = add_derived_columns(df)

    # --- Kinematic histograms ---
    print("\nKinematic distributions...")
    hists = create_histograms()
    for key, hdef in hists.items():
        col = HIST_COLUMN[key]
        plot_kinematic_combined(key, hdef, df[col], out_dir)
        plot_kinematic_by_origin(key, hdef, df, col, out_dir)

    # --- Categorical status / identity bar charts ---
    print("\nStatus-code and identity bar charts...")
    plot_origin_bar(df, out_dir / "origin_counts.png")
    plot_value_counts_bar(df['prt_gen_status'], "generatorStatus codes",
                          "generatorStatus", out_dir / "gen_status_codes.png")
    plot_value_counts_bar(df['prt_sim_status'], "simulatorStatus raw codes",
                          "simulatorStatus (raw int)", out_dir / "sim_status_codes.png")
    plot_sim_status_bits(df, out_dir / "sim_status_bits.png")
    plot_value_counts_bar(df['prt_pdg'], "PDG codes (top 30)",
                          "PDG", out_dir / "pdg_codes.png", top=30)

    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print(f"Output plots saved in: {out_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
