#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["uproot"]
# ///
"""Check whether podio/edm4hep ROOT files are intact and fully written.

A podio frame file is only usable once its writing job closes cleanly: the
``events`` TTree is filled incrementally, but the ``podio_metadata`` tree (the
collection ID table / type info the reader needs) is written *last*, on close.
A job that was killed leaves an ``events`` tree with however many entries were
flushed and **no** ``podio_metadata`` -- ROOT can still recover and read the
events, but podio cannot open it.

This script reports, per file: whether ``podio_metadata`` is present and how
many entries the ``events`` tree holds.

Usage
-----

  # Shell expands the glob; we just take the file paths as argv.
  # `uv run` reads the inline script metadata above and pulls in uproot:
  uv run scripts/check_podio_files.py /work/.../*.edm4hep.root

  # Several explicit files:
  uv run scripts/check_podio_files.py a.edm4hep.root b.edm4eic.root

Exit code is non-zero if any file is missing metadata or unreadable, so it can
gate a pipeline:

  uv run scripts/check_podio_files.py /work/.../*.root && echo "all good"

Pass ``--rm`` to delete every file that is NOT ok (truncated / missing
metadata / unreadable); existing-but-missing paths are left alone:

  uv run scripts/check_podio_files.py --rm /work/.../*.root

Needs only ``uv`` (no ROOT). The script is also directly executable
(``./scripts/check_podio_files.py ...``) via the ``uv run`` shebang.
"""
from __future__ import annotations

import argparse
import os
import sys

import uproot


def check_file(path: str) -> tuple[bool, str]:
    """Return (ok, message) for a single file.

    ok is True only when the file opens, has a ``podio_metadata`` tree, and has
    a readable ``events`` tree.
    """
    if not os.path.exists(path):
        return False, "MISSING_FILE"

    try:
        with uproot.open(path) as f:
            # uproot keys carry a ";<cycle>" suffix; strip it before matching.
            keys = {k.split(";")[0] for k in f.keys(recursive=False)}
            has_meta = "podio_metadata" in keys

            n_events = -1
            if "events" in keys:
                try:
                    n_events = f["events"].num_entries
                except Exception as exc:  # noqa: BLE001 - report, don't crash
                    return False, f"events unreadable: {exc}"

            ok = has_meta and n_events >= 0
            meta = "YES" if has_meta else "NO"
            return ok, f"meta={meta} events={n_events}"

    except Exception as exc:  # noqa: BLE001 - a zombie/truncated file lands here
        return False, f"OPEN_FAILED: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check podio/edm4hep ROOT files for podio_metadata and event count."
    )
    parser.add_argument("files", nargs="+", help="ROOT files (shell-expanded glob is fine)")
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Only print files that are NOT ok.",
    )
    parser.add_argument(
        "--rm", action="store_true",
        help="Delete files that are NOT ok (skips MISSING_FILE, which has nothing to delete).",
    )
    args = parser.parse_args()

    all_ok = True
    for path in args.files:
        ok, msg = check_file(path)
        all_ok = all_ok and ok
        removed = ""
        if not ok and args.rm and os.path.exists(path):
            try:
                os.remove(path)
                removed = " [removed]"
            except OSError as exc:
                removed = f" [rm failed: {exc}]"
        if ok and args.quiet:
            continue
        flag = "OK  " if ok else "BAD "
        print(f"{flag} {os.path.basename(path):<55} {msg}{removed}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
