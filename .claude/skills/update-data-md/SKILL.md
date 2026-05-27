---
name: update-data-md
description: Use this skill when the user asks to update, refresh, regenerate, or rebuild `docs/data.md` — the catalog of available ePIC background-mixed datasets in Rucio. The skill queries Rucio for all DIDs with `is_background_mixed=true`, drops the CI/`main` branch entries, groups the remaining real-campaign DIDs by campaign → data name, and rewrites `docs/data.md` using the `<DidTable>` Vue component (one table per data name, with per-row and per-table copy buttons). Trigger phrases: "update data.md", "refresh the data catalog", "regenerate data page", "pull the new datasets from rucio", "what backgrounds are on rucio", "list available DIDs".
---

# Update `docs/data.md`

`docs/data.md` is the project's human-readable catalog of background-mixed
datasets available in Rucio. Its source of truth is the output of
`rucio did list --filter 'is_background_mixed=true' 'epic:*'`. This skill
rebuilds the page from a fresh query.

The page uses the **`<DidTable>` Vue component** (registered in
`docs/.vitepress/theme/index.ts`) so every row has a 📋 copy button and
every table has a "Copy all" button — much friendlier than a flat bullet
list when you actually want to paste a DID somewhere.

---

## One-liner (preferred)

If `docker` and `python` are both available locally:

```bash
docker run --rm eicweb/eic_xl:nightly \
    rucio did list --filter 'is_background_mixed=true' 'epic:*' \
  | python scripts/update_data_md.py
```

That pipes the raw table straight into the parser, which writes
`docs/data.md`. Skip to step 4 (commit) below.

The remaining sections explain each step in case the one-liner can't run
straight through (e.g. you want to inspect the raw Rucio output, or the
container is launched via Apptainer on the JLab farm).

---

## 1. Query Rucio inside the `eic_xl` container

Rucio lives inside the `eicweb/eic_xl:nightly` image. The command can be
slow (tens of seconds to a couple of minutes).

**Docker (most portable):**

```bash
docker run --rm eicweb/eic_xl:nightly \
  rucio did list --filter 'is_background_mixed=true' 'epic:*' > /tmp/rucio.txt
```

**Apptainer / Singularity (JLab farm, CVMFS):**

```bash
apptainer exec /cvmfs/singularity.opensciencegrid.org/eicweb/eic_xl:nightly \
  rucio did list --filter 'is_background_mixed=true' 'epic:*' > /tmp/rucio.txt
```

**Authentication:** the container ships with a working Rucio config for the
EIC instance, but the user may need an active X.509 proxy / OIDC token. If
the command fails with a 401/403, surface that — auth is the user's
responsibility, not the skill's.

---

## 2. Run the parser

`scripts/update_data_md.py` reads the Rucio ASCII table from stdin or from
a file, parses each DID, drops `main/` branch entries, groups by
campaign → data name, sorts inside each group, and writes the markdown.

```bash
python scripts/update_data_md.py /tmp/rucio.txt
# or:
cat /tmp/rucio.txt | python scripts/update_data_md.py
```

Output (example):

```
Parsed 19 valid DIDs (skipped 21 `main/` entries)
Rendered 2 campaign(s), 2 data-name table(s)
Wrote C:\dev\ai_epic_background\docs\data.md
```

The script's parsing rules are baked into the code, but they match these
project conventions:

| Field      | Definition                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------- |
| partition  | `RECO` (EICrecon output) or `FULL` (DD4hep simulation output). Anything else is dropped.    |
| campaign   | The segment after the partition. `main` is treated as a CI branch and dropped.              |
| data_name  | The segment after `epic_craterlake/`.                                                       |
| beam_energy| First substring matching `\d+x\d+` in the remaining path (e.g. `10x100`, `18x275`).         |

Sort order inside one `(campaign, data_name)` table:

1. Beam energy, by `(lepton, hadron)` numerically.
2. `minQ2=N` ascending (DIDs without a `minQ2` go to the end).
3. **FULL above RECO** at the same `(energy, minQ2)`.

Campaigns are rendered newest-first (lexicographic descending on the
version tag, so `26.04.1` is above `26.03.0`).

---

## 3. What the output looks like

The rendered markdown has standard `## Campaign X` and `### <data_name>`
headings (so the sidebar/TOC pick them up), and one `<DidTable>` Vue
component per data name:

```markdown
# Data

...

## Campaign 26.04.1

### Bkg_Exact1S_2us

<DidTable :rows='[{"did":"epic:/FULL/26.04.1/.../10x100/minQ2=1","kind":"FULL","energy":"10x100"},{"did":"epic:/RECO/26.04.1/.../10x100/minQ2=1","kind":"RECO","energy":"10x100"}, ...]' />
```

Each row in the prop is `{did, kind, energy}`. The component renders:

- a 📋 per-row copy button (copies that single DID),
- a coloured kind badge (FULL = indigo, RECO = green),
- the beam-energy column (omitted automatically if all rows lack it),
- the full DID in `<code>`,
- a top-of-table toolbar with **Copy all (N)** plus, when both kinds are
  present, **FULL only** and **RECO only** buttons that copy just the
  filtered subset.

All copy buttons fall back from `navigator.clipboard.writeText` to a
`document.execCommand("copy")` shim, so they work in non-secure contexts
too.

---

## 4. Wire `data.md` into the docs

Already done in `docs/.vitepress/config.mts`:

- top nav has `{ text: 'Data', link: '/data' }`,
- sidebar has a `'Data' → 'Available Datasets' → /data` group.

If those entries are missing (e.g. after a config rewrite), add them back.

---

## 5. Commit

`docs/data.md` is the only artefact to commit. Do **not** commit:

- the raw Rucio output (`/tmp/rucio.txt` etc.),
- any temp parser scripts (`scripts/update_data_md.py` is the permanent one).

Typical commit message:

```
docs: refresh data.md from rucio (N DIDs across M campaigns)
```

---

## 6. Verify

Quick sanity checks before finishing:

- Every `## Campaign` heading is a version tag (e.g. `26.04.1`), never
  `main`.
- Every FULL has its RECO twin in the same `(energy, minQ2)` row pair where
  one exists in Rucio.
- The page builds: `cd docs && npm run build` succeeds without "page not
  found" or component warnings about `DidTable`.

Then report to the user: number of campaigns, number of DIDs rendered, the
path written (`docs/data.md`), and how many `main/` entries were skipped.

---

## Notes

- The Rucio output table widens to fit the longest DID; the parser uses
  `split("|", 2)[1]` and only looks at the first column, so column widths
  don't matter.
- Some DIDs have unusual tails (e.g. SIDIS:
  `.../SIDIS/D0_ABCONV/pythia8.306-1.1/10x100/q2_100/hiDiv`). The parser
  still finds `10x100` via the regex and emits them with that beam-energy
  tag; they sort to the end of the `minQ2=...` block (since they have no
  `minQ2`).
- The component lives at
  `docs/.vitepress/theme/components/DidTable.vue` and is globally
  registered in `theme/index.ts` — using `<DidTable>` from any markdown
  page works without per-page imports.
