#!/usr/bin/env python3
"""Summarize `rucio did list` output to help author docs/data.md by hand.

This script is **read-only**: it never writes docs/data.md. The dataset
strips on that page are authored with the `<DidStrips>` Vue component,
whose tags (label, colour, tooltip) are a human/LLM judgement call — the
DID path has no fixed schema, so there is nothing reliable to parse into
tags. Instead, this tool digests the raw Rucio table into the material you
need to author strips: one group per `(campaign, data_name)`, the shared
DID prefix, FULL/RECO counts, and the distinct path segments that vary
within the group (the candidates for tag groups).

Read the printed summary, then hand-edit the `<DidStrips>` blocks in
docs/data.md. See `.claude/skills/update-data-md/SKILL.md` for the full
authoring guide.

Usage
-----

  # From a file:
  python scripts/summarize_rucio_dids.py rucio.txt

  # From stdin (the typical pipeline):
  docker run --rm eicweb/eic_xl:nightly \\
      rucio did list --filter 'is_background_mixed=true' 'epic:*' \\
    | python scripts/summarize_rucio_dids.py

  # Machine-readable JSON instead of the text report:
  python scripts/summarize_rucio_dids.py rucio.txt --json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_did(did: str) -> dict | None:
    """Parse one Rucio DID. Returns None if it should be skipped."""
    if not did.startswith("epic:/"):
        return None
    parts = did[len("epic:/"):].split("/")
    if len(parts) < 5:
        return None
    partition, campaign, third, data_name, *rest = parts
    if partition not in ("FULL", "RECO"):
        return None
    if campaign == "main":
        # CI / branch / Test entries — not real campaigns
        return None
    if third != "epic_craterlake":
        return None
    return {
        "did": did,
        "partition": partition,
        "campaign": campaign,
        "data_name": data_name,
        "segments": rest,  # everything after epic_craterlake/<data_name>/
    }


def read_dids(stream) -> tuple[list[dict], int]:
    """Pull DID strings out of the Rucio ASCII table and parse them.

    Returns (records, skipped_main_count).
    """
    records: list[dict] = []
    skipped_main = 0
    for line in stream:
        line = line.rstrip("\n")
        if not line.startswith("|"):
            continue
        first_col = line.split("|", 2)[1].strip()
        if not first_col.startswith("epic:/"):
            continue
        if "/main/" in first_col:
            skipped_main += 1
        rec = parse_did(first_col)
        if rec:
            records.append(rec)
    return records, skipped_main


def common_prefix_path(dids: list[str]) -> str:
    """Longest shared leading path (segment-wise) across DIDs, keeping the
    `epic:` scheme prefix. Segments that fully agree are kept verbatim."""
    if not dids:
        return ""
    split = [d.split("/") for d in dids]
    shared: list[str] = []
    for col in zip(*split):
        if len(set(col)) == 1:
            shared.append(col[0])
        else:
            break
    prefix = "/".join(shared)
    # keep a trailing slash to signal it's a prefix, not a full DID
    return prefix + "/" if prefix and not prefix.endswith("/") else prefix


def summarize(records: list[dict]) -> list[dict]:
    """Group by (campaign, data_name) and describe each group."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in records:
        groups[(r["campaign"], r["data_name"])].append(r)

    out: list[dict] = []
    for (campaign, data_name) in sorted(groups, key=lambda k: (k[0], k[1]), reverse=True):
        recs = groups[(campaign, data_name)]
        dids = sorted(r["did"] for r in recs)
        full = sum(1 for r in recs if r["partition"] == "FULL")
        reco = sum(1 for r in recs if r["partition"] == "RECO")

        # didpath prefix. When both partitions are present, fold FULL/RECO into a
        # {FULL|RECO} placeholder first — otherwise the shared prefix would stop
        # at the partition segment and collapse to just `epic:/`.
        if full and reco:
            folded = [d.replace("/FULL/", "/{FULL|RECO}/", 1)
                        .replace("/RECO/", "/{FULL|RECO}/", 1) for d in dids]
            prefix = common_prefix_path(folded)
        else:
            prefix = common_prefix_path(dids)

        # distinct segment values by position (after data_name), and the flat
        # union of every distinct segment (the candidate tag pool)
        by_position: dict[int, list[str]] = defaultdict(list)
        pool: list[str] = []
        seen: set[str] = set()
        for r in recs:
            for i, seg in enumerate(r["segments"]):
                if seg not in by_position[i]:
                    by_position[i].append(seg)
                if seg not in seen:
                    seen.add(seg)
                    pool.append(seg)

        out.append({
            "campaign": campaign,
            "data_name": data_name,
            "didpath": prefix,
            "full": full,
            "reco": reco,
            "n_dids": len(dids),
            "segments_by_position": {str(i): v for i, v in sorted(by_position.items())},
            "segment_pool": pool,
            "dids": dids,
        })
    return out


def print_report(summary: list[dict], skipped_main: int) -> None:
    n_campaigns = len({g["campaign"] for g in summary})
    print(f"# {len(summary)} strip(s) across {n_campaigns} campaign(s) "
          f"(skipped {skipped_main} `main/` entries)\n")
    for g in summary:
        print(f"## Campaign {g['campaign']}  —  {g['data_name']}")
        print(f"   didpath : {g['didpath']}")
        print(f"   version : {g['campaign']}")
        print(f"   name    : {g['data_name']}")
        counts = []
        if g["full"]:
            counts.append(f"FULL·{g['full']}")
        if g["reco"]:
            counts.append(f"RECO·{g['reco']}")
        print(f"   dids    : {g['n_dids']}  ({', '.join(counts)})")
        print("   varying segments (position → distinct values — candidate tag groups):")
        for pos, vals in g["segments_by_position"].items():
            if len(vals) == 1:
                continue  # constant → belongs in <More>, not a main tag group
            print(f"       [{pos}] {', '.join(vals)}")
        constants = [
            vals[0] for vals in g["segments_by_position"].values() if len(vals) == 1
        ]
        if constants:
            print(f"   constant segments (candidates for <More>): {', '.join(constants)}")
        print("   DIDs:")
        for d in g["dids"]:
            print(f"       {d}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="Path to the raw `rucio did list` output. If omitted, read from stdin.",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit the grouped summary as JSON instead of the human report.",
    )
    args = ap.parse_args()

    stream = sys.stdin if args.input is None else args.input.open("r", encoding="utf-8")
    try:
        records, skipped_main = read_dids(stream)
    finally:
        if args.input is not None:
            stream.close()

    if not records:
        print(
            "error: no valid DIDs parsed from input — is the input a Rucio "
            "`did list` table?",
            file=sys.stderr,
        )
        return 1

    summary = summarize(records)
    if args.json:
        print(json.dumps({"skipped_main": skipped_main, "groups": summary}, indent=2))
    else:
        print_report(summary, skipped_main)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
