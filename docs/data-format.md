# Data Format

The CSV files produced by `trk_hits_to_csv.cxx` contain **one row per tracker hit
association**. Each row joins three things:

- the reconstructed tracker hit (`edm4eic::TrackerHit`),
- the underlying simulation hit (`edm4hep::SimTrackerHit`),
- the `MCParticle` that produced the simulation hit.

This makes every row self-contained: it carries enough truth and reconstructed
information to be used standalone for analysis or ML training.

## Columns

The header is written by `HitRecord::make_csv_header()` in `trk_hits_to_csv.cxx`.

### Event and indexing

| Column      | Type   | Description                                         |
| ----------- | ------ | --------------------------------------------------- |
| `evt`       | uint64 | Event number within the run                         |
| `hit_index` | uint64 | Index of the hit-association in its collection      |
| `prt_index` | uint64 | Index of the `MCParticle` that produced the sim hit |

### Particle identification & kinematics

| Column        | Unit  | Description                                                      |
| ------------- | ----- | ---------------------------------------------------------------- |
| `prt_pdg`     | —     | PDG code (e.g. `11` = e⁻, `211` = π⁺, `2212` = proton)           |
| `prt_status`  | —     | Generator status: `1` = primary from generator, `0` = G4-created |
| `prt_energy`  | GeV   | Total energy                                                     |
| `prt_charge`  | e     | Electric charge                                                  |
| `prt_mom_x/y/z` | GeV/c | Momentum components                                            |

### Particle vertex (production point)

| Column                     | Unit | Description                |
| -------------------------- | ---- | -------------------------- |
| `prt_vtx_time`             | ns   | Time at production vertex  |
| `prt_vtx_pos_x/y/z`        | mm   | Vertex position components |

### Particle endpoint (decay / absorption)

| Column                     | Unit | Description                                                    |
| -------------------------- | ---- | -------------------------------------------------------------- |
| `prt_end_time`             | ns   | Time at endpoint (currently mirrors `prt_vtx_time` in EDM4hep) |
| `prt_end_pos_x/y/z`        | mm   | Endpoint position components                                   |

### Tracker hit detector info

| Column               | Type   | Description                                            |
| -------------------- | ------ | ------------------------------------------------------ |
| `trk_hit_cell_id`    | uint64 | Full cell ID (encodes the detector hierarchy)          |
| `trk_hit_system_id`  | uint64 | Detector system ID (low byte of `cell_id`)             |
| `trk_hit_system_name`| string | Human-readable detector name (e.g. `SiBarrelVertex`)   |

### Tracker hit position, time, and uncertainties

| Column                                             | Unit  | Description                            |
| -------------------------------------------------- | ----- | -------------------------------------- |
| `trk_hit_pos_x/y/z`                                | mm    | Reconstructed hit position             |
| `trk_hit_time`                                     | ns    | Reconstructed hit time                 |
| `trk_hit_pos_err_xx`, `trk_hit_pos_err_yy`, `trk_hit_pos_err_zz` | mm² | Diagonal of the position covariance |
| `trk_hit_time_err`                                 | ns    | Time uncertainty                       |
| `trk_hit_edep`                                     | GeV   | Energy deposited in the sensor         |
| `trk_hit_edep_err`                                 | GeV   | Energy-deposition uncertainty          |

## Detector coverage

The converter currently iterates over all standard ePIC tracker hit-association
collections:

```
B0TrackerRawHitAssociations          ForwardOffMTrackerRawHitAssociations
BackwardMPGDEndcapRawHitAssociations  ForwardRomanPotRawHitAssociations
ForwardMPGDEndcapRawHitAssociations   MPGDBarrelRawHitAssociations
OuterMPGDBarrelRawHitAssociations     RICHEndcapNRawHitsAssociations
SiBarrelRawHitAssociations            SiBarrelVertexRawHitAssociations
SiEndcapTrackerRawHitAssociations     TOFBarrelRawHitAssociations
TOFEndcapRawHitAssociations
```

Calorimeter associations are listed in the source but not currently written to the
CSV (the `process_calo_hits` call is commented out in `process_event`).

## Loading the CSV

```python
import pandas as pd

df = pd.read_csv("hits.csv")
print(df.shape, df.columns.tolist()[:6])

# Filter one event
event_0 = df[df["evt"] == 0]

# Keep only primary particles
primaries = df[df["prt_status"] == 1]

# Group by detector system
hits_per_system = df.groupby("trk_hit_system_name").size()
```

For visualisation of a single event, see
`analyses/time-vs-z-plots/background_analysis.py`, which produces `time vs z`
scatter plots colored by `prt_status`.
