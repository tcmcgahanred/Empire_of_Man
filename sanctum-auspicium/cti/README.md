# CTI — Effort 1 (CCIC SLTT Cyber)

Weekly OSINT cyber threat intelligence cycle for a 34-county California AOR. TLP:CLEAR.

## Artifact import map

The code/docs below live in the **Sanctum Auspicium** working chat and need to be brought into this tree (renamed to the Sanctum scheme). State per the handoff:

| Working file (Sanctum chat) | → lands as | Sanctum name | State |
|---|---|---|---|
| `collector.py` | `cti/acolyte.py` | **Acolyte** | Deployed, working (on Ravenor) |
| `prefilter.py` | `cti/arbites.py` | **Arbites** | Built, tuned (4 passes), tested |
| `CCIC_WCTI_intelligence_requirements.md` | `cti/codex.md` | **Codex** | Current |
| `CCIC_WCTI_v20260810_STAGING.md` | `cti/editions/vox_v20260810.md` | **Vox** (edition) | Current sample edition |
| `CCIC_WCTI_intel_cycle_tracker.drawio` | `cti/cogitator.drawio` | **Cogitator** | Current |
| `CCIC_WCTI_effort_briefing_for_review.md` | `cti/docs/effort_briefing.md` | (unnamed — *Testimony* / *Dossier*?) | Current |
| `collector_title_dedup.py` | (merge into Acolyte) | Acolyte component | Integrated; keep as reference |
| `ravenor_feeds_MASTER.txt` | `cti/config/feeds_master.txt` | Acolyte config | Reference (partly superseded by live `feeds.txt`) |
| `ravenor_AOR_trusted_sources.txt` | `cti/config/trusted_sources_AOR.txt` | Acolyte config | **Pending verify/load** |

## Notes
- `config/feeds.txt` is the **live** feed list and lives on the Ravenor VM (`/opt/ravenor/feeds.txt`); the copy here is a mirror for version tracking.
- Synthesis is deliberately **manual** — no API/token spend. Arbites surfaces ~55 candidates + a drop list; the human cuts to 5–8.
- One open naming decision: the external-review explainer has no Sanctum name yet (candidates: **Testimony**, **Dossier**).
