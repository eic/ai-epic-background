---
name: update-data-md
description: Use this skill when the user asks to update, refresh, regenerate, or rebuild `docs/data.md` — the catalog of available ePIC background-mixed datasets in Rucio. The skill queries Rucio for all DIDs with `is_background_mixed=true`, drops the CI/`main` branch entries, groups the remaining real-campaign DIDs by campaign → data name → beam energy (pairing the FULL DD4hep and RECO EICrecon variants of each dataset, with FULL listed first), and writes `docs/data.md`. Trigger phrases: "update data.md", "refresh the data catalog", "regenerate data page", "pull the new datasets from rucio", "what backgrounds are on rucio", "list available DIDs".
---

# Update `docs/data.md`

`docs/data.md` is the project's human-readable catalog of background-mixed
datasets available in Rucio. Its source of truth is the output of
`rucio did list --filter 'is_background_mixed=true' 'epic:*'`. This skill
rebuilds the page from a fresh query.

---

## 1. Run Rucio inside the `eic_xl` container

Rucio lives inside the `eicweb/eic_xl:nightly` image. The command can be
slow (tens of seconds to minutes).

**Docker (most portable):**

```bash
docker run --rm eicweb/eic_xl:nightly \
  rucio did list --filter 'is_background_mixed=true' 'epic:*'
```

**Apptainer / Singularity (JLab farm, CVMFS):**

```bash
apptainer exec /cvmfs/singularity.opensciencegrid.org/eicweb/eic_xl:nightly \
  rucio did list --filter 'is_background_mixed=true' 'epic:*'
```

Save the output to a file so the rest of the skill can work on it:

```bash
docker run --rm eicweb/eic_xl:nightly \
  rucio did list --filter 'is_background_mixed=true' 'epic:*' > /tmp/rucio.txt
```

**Authentication:** the container ships with a working Rucio config for the
EIC instance, but the user may need an active X.509 proxy / OIDC token. If
the command fails with a 401/403, surface that to the user — auth is their
responsibility, not the skill's.

---

## 2. Parse the table

Rucio prints an ASCII table:

```
+--------------------------------------+--------------+
| SCOPE:NAME                           | [DID TYPE]   |
|--------------------------------------+--------------|
| epic:/RECO/26.04.1/.../minQ2=1       | N/A          |
| epic:/FULL/26.04.1/.../minQ2=1       | N/A          |
+--------------------------------------+--------------+
```

Keep only data rows: lines starting with `|` whose first column starts with
`epic:/`. Each DID has the shape:

```
epic:/<PARTITION>/<CAMPAIGN>/epic_craterlake/<DATA_NAME>/<PHYSICS_AND_SIM_PARAMS...>
```

Pull these fields:

| Field      | Definition                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------- |
| partition  | `RECO` (EICrecon output) or `FULL` (DD4hep simulation output). Skip other values.           |
| campaign   | The segment after the partition (e.g. `26.04.1`, `26.03.0`).                                |
| data_name  | The segment after `epic_craterlake/` (e.g. `Bkg_Exact1S_2us`).                              |
| beam_energy| First substring matching the regex `\d+x\d+` in the remaining path (e.g. `10x100`).         |
| tail       | The remainder of the path (everything after the partition). Used for FULL/RECO pairing.     |

### Filtering

- **Drop** every DID whose campaign is `main` — these are CI / branch / test
  builds (`CI/Backgrounds/...`, `Test/...`). The user explicitly only cares
  about real campaigns (versioned tags like `26.04.1`).
- **Drop** rows where the partition is neither `FULL` nor `RECO`.
- `epic_craterlake` is always the same and is omitted from the rendered page.

### FULL / RECO pairing

Two DIDs are a pair iff their **tail** (everything after `epic:/<PARTITION>/`)
is identical. For each pair, emit FULL first then RECO. DIDs without a
partner are still listed, alone.

---

## 3. Group and render

The desired layout (use exactly this heading hierarchy):

```markdown
# Data

Available background-mixed datasets in Rucio. Source:
`rucio did list --filter 'is_background_mixed=true' 'epic:*'`.

Last updated: <ISO date>.

## Campaign 26.04.1

### Bkg_Exact1S_2us

#### 10x100

- **FULL** — `epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1`
- **RECO** — `epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1`
- **FULL** — `epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=10`
- **RECO** — `epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=10`

#### 10x275

- **FULL** — `epic:/FULL/26.04.1/.../10x275/minQ2=1`
- **RECO** — `epic:/RECO/26.04.1/.../10x275/minQ2=1`

### Bkg_Other_Data_Name

#### 18x275

- **RECO** — `epic:/RECO/26.04.1/.../18x275/...` (no FULL counterpart)

## Campaign 26.03.0

...
```

### Ordering rules

- **Campaigns**: newest first. Sort lexicographically descending on the
  version tag, so `26.04.1` is above `26.03.0`.
- **Data names within a campaign**: alphabetical.
- **Beam energies within a data name**: by lepton energy ascending then
  hadron energy ascending. Parse `LxH` and sort numerically.
- **Entries within a beam energy**: by the remaining tail (so `minQ2=1`,
  `minQ2=10`, `minQ2=100`, `minQ2=1000` come out in numeric `minQ2` order
  when present; otherwise lexicographic).

---

## 4. Reference parser

The transformation is small enough to inline. Save this to a temp file and
run it if you prefer a script over doing the parse in-head:

```python
#!/usr/bin/env python3
"""Parse `rucio did list` output and emit docs/data.md."""
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

RUCIO_TXT = Path(sys.argv[1])         # raw rucio output
OUT_MD    = Path(sys.argv[2])         # docs/data.md

ENERGY_RE = re.compile(r"^\d+x\d+$")
MINQ2_RE  = re.compile(r"minQ2=(\d+)")

def parse_did(did: str):
    # did looks like: epic:/RECO/26.04.1/epic_craterlake/<data>/.../<EnergyLxH>/...
    if not did.startswith("epic:/"):
        return None
    parts = did[len("epic:/"):].split("/")
    if len(parts) < 5:
        return None
    partition, campaign, third, data_name, *rest = parts
    if partition not in ("FULL", "RECO"):
        return None
    if campaign == "main":           # CI/branch builds
        return None
    if third != "epic_craterlake":
        return None
    energy = next((p for p in rest if ENERGY_RE.match(p)), None)
    if energy is None:
        return None
    tail = "/".join([campaign, third, data_name, *rest])  # for pairing
    return {
        "did": did,
        "partition": partition,
        "campaign": campaign,
        "data_name": data_name,
        "energy": energy,
        "tail": tail,
        "rest": "/".join(rest),
    }

# 1. Extract DIDs from the table
records = []
for line in RUCIO_TXT.read_text().splitlines():
    if not line.startswith("|"):
        continue
    first_col = line.split("|", 2)[1].strip()
    if not first_col.startswith("epic:/"):
        continue
    rec = parse_did(first_col)
    if rec:
        records.append(rec)

# 2. Pair FULL+RECO by shared tail
by_tail = defaultdict(dict)             # tail -> {FULL: rec, RECO: rec}
for r in records:
    by_tail[r["tail"]][r["partition"]] = r

# 3. Group by campaign -> data_name -> energy -> [pair, ...]
groups = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
seen = set()
for tail, pair in by_tail.items():
    if tail in seen:
        continue
    seen.add(tail)
    any_rec = pair.get("FULL") or pair["RECO"]
    groups[any_rec["campaign"]][any_rec["data_name"]][any_rec["energy"]].append(pair)

# 4. Sort and render
def energy_key(e):
    a, b = e.split("x")
    return (int(a), int(b))

def pair_key(pair):
    rec = pair.get("FULL") or pair["RECO"]
    m = MINQ2_RE.search(rec["rest"])
    return (int(m.group(1)) if m else 10**9, rec["rest"])

lines = [
    "# Data",
    "",
    "Available background-mixed datasets in Rucio. Source:",
    "`rucio did list --filter 'is_background_mixed=true' 'epic:*'`.",
    "",
    f"Last updated: {date.today().isoformat()}.",
    "",
]

for campaign in sorted(groups, reverse=True):
    lines += [f"## Campaign {campaign}", ""]
    for data_name in sorted(groups[campaign]):
        lines += [f"### {data_name}", ""]
        for energy in sorted(groups[campaign][data_name], key=energy_key):
            lines += [f"#### {energy}", ""]
            for pair in sorted(groups[campaign][data_name][energy], key=pair_key):
                if (rec := pair.get("FULL")):
                    lines.append(f"- **FULL** — `{rec['did']}`")
                if (rec := pair.get("RECO")):
                    lines.append(f"- **RECO** — `{rec['did']}`")
            lines.append("")

OUT_MD.write_text("\n".join(lines).rstrip() + "\n")
print(f"Wrote {OUT_MD} ({len(records)} DIDs, {sum(len(d) for c in groups.values() for d in c.values())} energy buckets)")
```

Invoke it:

```bash
python parse_rucio.py /tmp/rucio.txt docs/data.md
```

---

## 5. Wire `data.md` into the docs

Make sure `docs/.vitepress/config.mts` references the page. Under the
`sidebar` array, add a "Data" group (or extend an existing one) with:

```ts
{
  text: 'Data',
  collapsed: false,
  items: [
    { text: 'Available Datasets', link: '/data' },
  ]
},
```

And add a top-level nav entry if there isn't one already:

```ts
{ text: 'Data', link: '/data' },
```

Skip both edits if the entries already exist.

---

## 6. Verify

Quick sanity checks before finishing:

- Every campaign in the rendered page is a version tag (e.g. `26.04.1`),
  never `main`.
- Every FULL has a RECO neighbour where one exists in the source.
- The page builds: `cd docs && npm run build` should succeed without
  broken-link warnings about `data`.

Then report to the user: number of campaigns, number of DIDs rendered, and
the path written (`docs/data.md`).

---

## Notes

- The Rucio output table widens to accommodate the longest DID; don't rely
  on fixed column widths. The parser uses `split("|", 2)[1]` and only looks
  at the first column.
- A few DIDs in the wild have unusual tails (e.g. SIDIS:
  `.../SIDIS/D0_ABCONV/pythia8.306-1.1/10x100/q2_100/hiDiv`). The parser
  still finds `10x100` via the regex — just verify the rendered page is
  readable for those rows.
- Don't commit raw Rucio output (`/tmp/rucio.txt`); only commit
  `docs/data.md`.
