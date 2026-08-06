# Changelog — Sanctum Auspicium

All notable changes to the Sanctum Auspicium intelligence apparatus. **Git is the source of truth**; this file is the curated-highlights layer and `git log` is the full record. Artifacts carry a one-time starting-version anchor (see `VERSIONING.md`), then history flows through commits. Editions of the brief (Vox) are keyed by publish date (`vYYYYMMDD`), separate from code versioning.

## [2026-08-04] Scaffolded into EoM + CTI effort milestones

Sub-project established under Empire of Man. First substantive entry captures the CTI (Effort 1) work completed to date.

- **Collector (Acolyte) title-dedup added** and confirmed — dedups by URL-hash **and** normalized-title-hash. A large backfill run dropped 98% on the second pass.
- **Feed set verified** against real egress; national trusted sources loaded (~49 live).
- **Dropped 34 county Google News keyword feeds** as noise — keyword search on a general index is the wrong instrument for local-incident detection.
- **Intelligence requirements (Codex) finalized** — 1 KIQ, 4 PIRs, multiplicative scoring model (tier weights 8/4/2/1 × elevation multipliers 1.5/1.5/1.3/1.3), and Layer-4 cut doctrine (prefer false positives; strict on sensors, generous on items; wide cutoff; mandatory drop list; scoring must show reasoning).
- **Pre-filter (Arbites) built and tuned over 4 passes** on the real corpus — fixed keyword collisions (substring matches like "cisco" inside "Francisco"), tightened tier-1 to require California *as subject* of an incident (not passing mention), added empty-title guard. Reliably surfaces genuine California SLTT incidents at the top.
- **Staging brief edition v20260810 produced** from clean corpus (water/wastewater OT sector lead).
- **External review (Gemini) incorporated** — accepted: upstream pre-filter, ransomware-leak-site AOR sensor idea, cross-section dedup, primary-source elevation. Rejected: additive scoring rewrite (would reverse the deliberate convergence design).
- **Version control decided** — Git as source of truth; private GitHub remote authoritative; VS + Ravenor both working copies; secrets stay in Keeper, blocked by `.gitignore`.

### Open / next
- Import artifacts into the tree under the Sanctum scheme (Acolyte / Arbites / Codex / Vox / Cogitator) with version-anchor headers.
- Verify + load curated AOR trusted sources (MS-ISAC, Cal OES, CDT, CA regional press).
- Build CA AG breach-registry scraper (authoritative AOR breach sensor; not RSS).
- Add ransomware-leak-site aggregator filtered for California (early-warning AOR sensor).
- Build distribution template + TLP:CLEAR presentation layer.
- Future: stand up the S2 aviation-intel effort under the same umbrella (unclassified; IPB doctrine).
