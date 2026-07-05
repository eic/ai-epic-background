# Data

Available **background-mixed** datasets in Rucio. Source of truth:

```bash
rucio did list --filter 'is_background_mixed=true' 'epic:*RECO/26.04.1*'
```

The campaign strips below are authored by hand with the `<DidStrips>`
component — see `.vitepress/theme/components/DidStrips.vue`. To refresh them
after a new Rucio campaign, run the `update-data-md` skill: it queries Rucio,
digests the DIDs with `scripts/summarize_rucio_dids.py`, and guides authoring
the strips (labels, colours, and tooltips are set by hand).

_Last updated: **2026-06-29**_

## Conventions

- **FULL** — DD4hep simulation output (sim-level, full Geant4 hits).
- **RECO** — EICrecon reconstruction output (reco-level).
- Each strip covers one `(campaign, data_name)` pair. Click a strip to reveal
  the exact Rucio DIDs with copy buttons; hover any tag for a description.
- `main/` branch / CI / Test entries are filtered out — only versioned
  campaigns are shown.
- `epic_craterlake` is the only detector configuration.
- Use the per-row 📋 to copy a single DID, the **Copy all** button to copy
  every DID in a strip (newline-separated), or click the prefix line to copy
  the shared DID prefix.

<!-- BEGIN STRIPS -->

## Campaign 26.05.0

<DidStrips
  didpath="epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/"
  version="26.05.0"
  name="Bkg_Exact1S_2us_e_only"
>
  <Tags color="violet" desc="Physics process">
    <Tag desc="Electroweak / Beyond-Standard-Model">EW_BSM</Tag>
    <Tag desc="Axion-like particle signal">ALP</Tag>
  </Tags>
  <Tags color="fuchsia" desc="Final state / decay channel">
    <Tag desc="Final state a -> e, mu+ mu-">aem-ax-emmupmum</Tag>
    <Tag desc="Final state a -> e e">aem-axem</Tag>
  </Tags>
  <Tags color="sky" desc="Beam energy">
    <Tag desc="Beam energy 10x110 GeV (e 10 x p 110)">10x110</Tag>
  </Tags>
  <Tags color="rose" desc="ALP signal mass">
    <Tag desc="ALP mass = 0.1 GeV">ma_0.1</Tag>
    <Tag desc="ALP mass = 0.2 GeV">ma_0.2</Tag>
    <Tag desc="ALP mass = 0.5 GeV">ma_0.5</Tag>
    <Tag desc="ALP mass = 1.0 GeV">ma_1.0</Tag>
    <Tag desc="ALP mass = 2.0 GeV">ma_2.0</Tag>
    <Tag desc="ALP mass = 5.0 GeV">ma_5.0</Tag>
    <Tag desc="ALP mass = 10.0 GeV">ma_10.0</Tag>
    <Tag desc="ALP mass = 20.0 GeV">ma_20.0</Tag>
  </Tags>
  <More color="slate">
    <Tag desc="Detector: ePIC craterlake">epic_craterlake</Tag>
    <Tag desc="Generator: MadGraph5 v3.7.0">madgraph5-3.7.0-1.0</Tag>
    <Tag desc="Beam-pipe gold coating">GoldCt</Tag>
    <Tag desc="Coating thickness 10 um">10um</Tag>
  </More>
  <Dids>
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-ax-emmupmum/10x110/ma_0.1
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-ax-emmupmum/10x110/ma_0.2
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-ax-emmupmum/10x110/ma_0.5
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-ax-emmupmum/10x110/ma_1.0
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-ax-emmupmum/10x110/ma_2.0
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-ax-emmupmum/10x110/ma_5.0
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-ax-emmupmum/10x110/ma_10.0
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-ax-emmupmum/10x110/ma_20.0
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-axem/10x110/ma_0.1
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-axem/10x110/ma_0.2
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-axem/10x110/ma_0.5
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-axem/10x110/ma_1.0
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-axem/10x110/ma_2.0
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-axem/10x110/ma_5.0
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-axem/10x110/ma_10.0
epic:/RECO/26.05.0/epic_craterlake/Bkg_Exact1S_2us_e_only/GoldCt/10um/EW_BSM/ALP/madgraph5-3.7.0-1.0/aem-axem/10x110/ma_20.0
  </Dids>
</DidStrips>

## Campaign 26.04.1

<DidStrips
  didpath="epic:/{FULL|RECO}/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/"
  version="26.04.1"
  name="Bkg_Exact1S_2us"
>
  <Tags color="violet" desc="Physics process">
    <Tag desc="Deep Inelastic Scattering">DIS</Tag>
    <Tag desc="Neutral-current exchange">NC</Tag>
  </Tags>
  <Tags color="sky" desc="Beam energy">
    <Tag desc="Beam energy 10x100 GeV (e 10 x p 100)">10x100</Tag>
    <Tag desc="Beam energy 10x275 GeV (e 10 x p 275)">10x275</Tag>
  </Tags>
  <Tags color="amber" desc="Minimum momentum transfer">
    <Tag desc="Minimum Q2 >= 1 GeV2">minQ2=1</Tag>
    <Tag desc="Minimum Q2 >= 10 GeV2">minQ2=10</Tag>
    <Tag desc="Minimum Q2 >= 100 GeV2">minQ2=100</Tag>
    <Tag desc="Minimum Q2 >= 1000 GeV2">minQ2=1000</Tag>
  </Tags>
  <More color="slate">
    <Tag desc="Detector: ePIC craterlake">epic_craterlake</Tag>
    <Tag desc="Beam-pipe gold coating">GoldCt</Tag>
    <Tag desc="Coating thickness 10 um">10um</Tag>
  </More>
  <Dids>
epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1
epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1
epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=10
epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=10
epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=100
epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=100
epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1000
epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1000
epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x275/minQ2=1
epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x275/minQ2=1
epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x275/minQ2=10
epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x275/minQ2=10
epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x275/minQ2=100
epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x275/minQ2=100
epic:/FULL/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x275/minQ2=1000
epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x275/minQ2=1000
  </Dids>
</DidStrips>

## Campaign 26.03.0

<DidStrips
  didpath="epic:/RECO/26.03.0/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/"
  version="26.03.0"
  name="Bkg_Exact1S_2us"
>
  <Tags color="violet" desc="Physics process">
    <Tag desc="Deep Inelastic Scattering">DIS</Tag>
    <Tag desc="Neutral-current exchange">NC</Tag>
    <Tag desc="Semi-Inclusive DIS">SIDIS</Tag>
    <Tag desc="D0 (afterburner conversion)">D0_ABCONV</Tag>
  </Tags>
  <Tags color="sky" desc="Beam energy">
    <Tag desc="Beam energy 10x100 GeV">10x100</Tag>
    <Tag desc="Beam energy 10x275 GeV">10x275</Tag>
  </Tags>
  <Tags color="amber" desc="Momentum transfer">
    <Tag desc="Minimum Q2 >= 1 GeV2">minQ2=1</Tag>
    <Tag desc="Q2 = 100 GeV2">q2_100</Tag>
  </Tags>
  <More color="slate">
    <Tag desc="Detector: ePIC craterlake">epic_craterlake</Tag>
    <Tag desc="Generator: PYTHIA 8.306">pythia8.306-1.1</Tag>
    <Tag desc="High beam divergence">hiDiv</Tag>
  </More>
  <Dids>
epic:/RECO/26.03.0/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1
epic:/RECO/26.03.0/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/SIDIS/D0_ABCONV/pythia8.306-1.1/10x100/q2_100/hiDiv
epic:/RECO/26.03.0/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x275/minQ2=1
  </Dids>
</DidStrips>

<!-- END STRIPS -->

## Campaign 25.10

Not available on Rucio, but can be downloaded from JLab xrootd
(`root://dtn-eic.jlab.org//volatile/eic/...`). These strips list the
**directory paths** under each background configuration rather than leaf DIDs.

<DidStrips
  didpath="/volatile/eic/EPIC/RECO/25.10.0/epic_craterlake/Bkg_1SignalPer2usFrame/"
  version="25.10.0"
  name="Bkg_1SignalPer2usFrame"
>
  <Tags color="orange" desc="Background type">
    <Tag desc="Synchrotron radiation background (10 GeV, vacuum)">Synrad</Tag>
  </Tags>
  <More color="slate">
    <Tag desc="Detector: ePIC craterlake">epic_craterlake</Tag>
  </More>
  <Dids>
/volatile/eic/EPIC/RECO/25.10.0/epic_craterlake/Bkg_1SignalPer2usFrame/Synrad_10GeV_Vac_10000Ahr_Runtime_50s_Egas_10GeV_Hgas_275GeV
  </Dids>
</DidStrips>

<DidStrips
  didpath="/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_1SignalPer2usFrame/"
  version="25.10.4"
  name="Bkg_1SignalPer2usFrame"
>
  <Tags color="violet" desc="Physics process">
    <Tag desc="Deep Inelastic Scattering (NC, 10x100 & 10x275)">DIS</Tag>
    <Tag desc="Exclusive processes (DDVCS_ABCONV, DVMP)">EXCLUSIVE</Tag>
    <Tag desc="Semi-Inclusive DIS">SIDIS</Tag>
    <Tag desc="Synchrotron radiation background (18 GeV)">Synrad</Tag>
  </Tags>
  <More color="slate">
    <Tag desc="Detector: ePIC craterlake">epic_craterlake</Tag>
  </More>
  <Dids>
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_1SignalPer2usFrame/DIS/NC/10x100
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_1SignalPer2usFrame/DIS/NC/10x275
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_1SignalPer2usFrame/EXCLUSIVE/DDVCS_ABCONV
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_1SignalPer2usFrame/EXCLUSIVE/DVMP
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_1SignalPer2usFrame/SIDIS
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_1SignalPer2usFrame/Synrad_18GeV_Vac_10000Ahr_Runtime_50s_Egas_18GeV_Hgas_275GeV
  </Dids>
</DidStrips>

<DidStrips
  didpath="/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_Exactly1SignalPer2usFrame/"
  version="25.10.4"
  name="Bkg_Exactly1SignalPer2usFrame"
>
  <Tags color="violet" desc="Physics process">
    <Tag desc="Exclusive processes">EXCLUSIVE</Tag>
    <Tag desc="Semi-Inclusive DIS">SIDIS</Tag>
  </Tags>
  <Dids>
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_Exactly1SignalPer2usFrame/EXCLUSIVE
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_Exactly1SignalPer2usFrame/SIDIS
  </Dids>
</DidStrips>

<DidStrips
  didpath="/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_OnlyPer2usFrame/"
  version="25.10.4"
  name="Bkg_OnlyPer2usFrame"
>
  <Tags color="teal" desc="Background composition">
    <Tag desc="Only proton beam-gas background">proton-beamgas</Tag>
  </Tags>
  <Dids>
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_OnlyPer2usFrame/
  </Dids>
</DidStrips>

<DidStrips
  didpath="/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_RealisticSignalPer2usFrame/"
  version="25.10.4"
  name="Bkg_RealisticSignalPer2usFrame"
>
  <Tags color="violet" desc="Physics process">
    <Tag desc="Semi-Inclusive DIS (realistic signal only)">SIDIS</Tag>
  </Tags>
  <Dids>
/volatile/eic/EPIC/RECO/25.10.4/epic_craterlake/Bkg_RealisticSignalPer2usFrame/SIDIS
  </Dids>
</DidStrips>


## Using these DIDs

A DID is just a pointer — it resolves to a set of files (PFNs) on Rucio
Storage Elements. Two upstream pages cover this in full; this section is
the bare minimum to get you started.

- 📚 [Rucio usage tutorial](https://eic.github.io/tutorial-file-access/02-rucio_usage/index.html) — setup, auth, full command reference.
- 📚 [Use-cases tutorial](https://eic.github.io/tutorial-file-access/03-use_cases/index.html) — download vs. stream, batch workflows, common patterns.

### 1. One-time setup (inside `eic-shell`)

```bash
# Voms / OIDC auth — pick what matches your account (see Rucio tutorial).
rucio whoami
```

If `rucio whoami` returns your identity, you're done. If not, follow the
auth steps on the [Rucio usage tutorial](https://eic.github.io/tutorial-file-access/02-rucio_usage/index.html).

### 2. See what's inside a dataset

```bash
rucio did content list 'epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1'
```

Get list of files to 

```bash
rucio replica list file --protocols root --pfns --rses isopenaccess 'epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1'
```

### 3. Download files locally

```bash
rucio download 'epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=1'
```

> (!) You probably don't want to download the full dataset!

Downloads land in a directory tree mirroring the DID. Add `--nrandom N`
to pull only a sample, or `--rse <RSE>` to pin a storage element.

### 4. Stream over XRootD (no local copy)

Most analyses can read directly from XRootD — faster on the JLab farm and
saves disk:

```bash
# List replica URLs for a DID
rucio list-file-replicas --pfns 'epic:/RECO/26.04.1/.../minQ2=1' | head

# Then open them directly, e.g. in ROOT / uproot / EICrecon:
root -l 'root://dtn-eic.jlab.org//volatile/eic/EPIC/RECO/.../file.edm4eic.root'
```

See [use-cases](https://eic.github.io/tutorial-file-access/03-use_cases/index.html) for the recommended patterns when running many jobs over a dataset.
