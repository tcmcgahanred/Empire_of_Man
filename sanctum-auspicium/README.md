# Sanctum Auspicium

The *seat of detection* — a personal, open-source intelligence apparatus and an Empire of Man (EoM) sub-project. It is an umbrella over more than one intelligence effort, all **unclassified / OSINT**.

## Efforts

**Effort 1 — CTI (built, operational).** A weekly OSINT cyber threat intelligence cycle supporting a California Cybersecurity Integration Center (CCIC) role. Produces a weekly brief for low-maturity State/Local/Tribal/Territorial (SLTT) partners across a 34-county California Area of Responsibility. Product is **TLP:CLEAR** (freely shareable).

**Effort 2 — S2 (future, not built).** A weekly intelligence cycle supporting a [Redacted]. Shares the machinery (collection patterns, scoring discipline, human-gate philosophy) but keeps its own doctrine — IPB frameworks: MCOO, OAKOC, METT-TC, ASCOPE, PMESII-PT. All work **unclassified / open-source**.

## Naming scheme (Inquisition / Ordo theme)

| Name | Role | Type |
|------|------|------|
| **Sanctum Auspicium** | Project umbrella (seat of detection) | Project |
| **Acolyte** (`acolyte.py`) | Collector — gathers signal from feeds | Script |
| **Arbites** (`arbites.py`) | Pre-filter / scorer — provisional judgment on items | Script |
| **Codex** | Intelligence requirements & doctrine (KIQ / PIRs / scoring model) | Doc |
| **Vox** | The intelligence brief itself (the product disseminated) | Product |
| **Cogitator** | The intelligence-cycle tracker (process map + status) | Doc/diagram |

Names that already exist in EoM and are **not** reused here: **Conclave** (a pfSense firewall), **Interrogator_Ravenor** (the collector VM this runs on). "Project Ravenor" was an earlier informal name for the CTI pipeline; **Sanctum Auspicium** is the proper umbrella going forward.

## Architecture

```
[ Acolyte ]            [ Arbites ]              [ Human Gate ]          [ Vox ]
 collector      -->     pre-filter/scorer  -->   analyst review   -->   published brief
 (autonomous,           (scores corpus,          (verify, merge,        (TLP:CLEAR,
  daily, on Ravenor)     surfaces top ~55,         cut to 5-8,            weekly)
      |                  + drop list)              override scores)
      v
 Google Drive corpus  (handoff surface between collection and analysis)
```

Governed by the **Codex**. Tracked by the **Cogitator**. Synthesis is **manual** (human-triggered; no API/tokens) by deliberate choice.

## Doctrine

*Restraint is the product.* 5–8 items per edition. Quality over quantity on sensors, generous on items; prefer false positives to false negatives; convergence-based multiplicative scoring (tier weights 8/4/2/1 × elevation multipliers); the human analyst always overrides the score.

## Stack

Python (feedparser, trafilatura, rclone), systemd, Google Drive corpus, draw.io tracker. Runs on the **Interrogator_Ravenor** VM in the EoM lab (PG-Ordo_Xenos, `192.168.3.10`).

## Status

Collection operational (autonomous daily on Ravenor). Pre-filter (Arbites) built and tuned. Synthesis manual. Distribution/TLP:CLEAR presentation layer not yet built.

## Repo layout

```
sanctum-auspicium/
├── README.md
├── CHANGELOG.md             # curated highlights (git log = full record)
├── VERSIONING.md            # git-as-truth; artifact version anchors
├── cti/                     # Effort 1 — CCIC SLTT cyber
│   ├── acolyte.py           # collector          (import from Sanctum chat)
│   ├── arbites.py           # pre-filter / scorer (import from Sanctum chat)
│   ├── codex.md             # intelligence requirements & doctrine (import)
│   ├── cogitator.drawio     # intel-cycle tracker (import)
│   ├── config/
│   │   ├── feeds.txt                 # live feed list (lives on Ravenor)
│   │   └── trusted_sources_AOR.txt   # curated AOR sources (pending verify)
│   ├── editions/
│   │   └── vox_v20260810.md          # brief editions, publish-date keyed (import)
│   └── docs/
│       └── effort_briefing.md        # external-review explainer (import)
└── s2/                      # Effort 2 — CANG Aviation S2 (future stub)
    └── README.md
```

See `cti/README.md` for the artifact import map (working filename → Sanctum name).
