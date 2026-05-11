# Running the Converter

`trk_hits_to_csv.cxx` can be used in two complementary ways: as a ROOT macro
(no build step) or as a CMake-built executable (better for IDEs / debugging).

## Option 1 — ROOT macro

Run directly with `root` inside an environment that has ROOT + EDM4EIC available
(e.g. inside the `eic_xl` container):

```bash
root -x -l -b -q 'trk_hits_to_csv.cxx("input.edm4eic.root", "output.csv")'

# Limit number of events:
root -x -l -b -q 'trk_hits_to_csv.cxx("input.edm4eic.root", "output.csv", 100)'
```

This is what the [Snakemake workflow](/csv-convert-snakemake) uses under the hood.

## Option 2 — CMake build

Useful for IDE integration (code completion, debugging, faster turnaround):

```bash
cd csv_convert
mkdir build && cd build
cmake ..
make

# Run:
./trk_hits_to_csv -n 100 -o output.csv input.edm4eic.root
```

`CMakeLists.txt` finds these dependencies via `find_package`:

- `ROOT` (Core, RIO, Tree, Hist, Gpad, Graf)
- `podio`
- `EDM4HEP`
- `EDM4EIC`
- `fmt`

All of these are available inside the `eic_xl` container.

### CLI flags

| Flag       | Meaning                                |
| ---------- | -------------------------------------- |
| `-n N`     | Process at most `N` events             |
| `-o file`  | Output CSV path (default: `hits.csv`)  |
| `-h`       | Print usage                            |

Positional arguments are interpreted as input ROOT files.

## Quick visualisation

Once a CSV is produced, you can inspect a single event with the plotting script
in [`analyses/time-vs-z-plots/`](https://github.com/eic/eic-ai-background/tree/main/analyses/time-vs-z-plots):

```bash
uv run python ../analyses/time-vs-z-plots/background_analysis.py output.csv 0 -o event_0_hits.png
```

This writes two figures: a `time vs z` scatter plot for the requested event, and a
companion plot covering the full time range. Hits are colored by `prt_status`
(red for `prt_status == 1`, primary particles).
