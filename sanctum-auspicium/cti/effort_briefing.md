# CCIC Weekly Cyber Threat Intelligence Pipeline — Effort Briefing for External Review

*Prepared for a fresh reviewer (human or LLM) with no prior context. The goal is to explain what was built, why, and where the open questions are — so you can critique the design, catch mistakes, and suggest improvements.*

---

## 1. Who and what

The operator is a cyber threat intelligence analyst at the California Cybersecurity Integration Center (CCIC). His job includes producing a weekly threat-intelligence brief for State, Local, Tribal, and Territorial (SLTT) partners in the CCIC Area of Responsibility (AOR) — a 34-county region of California (Central Valley, Sierra, and northeastern interior; **not** the Bay Area, Los Angeles, San Diego, or the north coast). His audience is mostly low-maturity organizations: county and city government, school districts, small water/wastewater utilities — often without dedicated security staff.

The effort in this chat was to design and partially build an **OSINT collection-and-synthesis pipeline** that produces that weekly brief with as little manual effort as possible, while keeping analytical quality and editorial discipline high.

His guiding editorial principle, stated repeatedly: **"restraint is the product."** The brief targets 5–8 items per edition. Every item must have a clear "why an SLTT org should care" angle. Items without SLTT relevance get cut.

---

## 2. The architecture (three stages + a human gate)

```
[COLLECTION]            [SYNTHESIS]              [DISTRIBUTION]
Ravenor collector  -->  Claude reads corpus  --> Human analyst pass
(autonomous, daily)     applies scoring model    -> distribution template
   |                    drafts staging brief      -> publish to SLTT
   v                         |                          Monday AM
Google Drive corpus  <-------+
(the handoff surface)
```

**Stage 1 — Collection (built, running).** A dedicated Ubuntu VM called "Interrogator_Ravenor" runs a Python collector on a systemd timer. It reads a list of RSS/Atom feed URLs from a text file, pulls articles, extracts full text, deduplicates, writes each article as a dated JSON file, and pushes the corpus to Google Drive via rclone. It sits on an isolated, outbound-only network segment behind its own firewall — it collects from the internet but nothing can reach back into it. (This is part of a larger home detection-engineering lab, themed on Warhammer 40K, which is why the hostnames are lore names. The lab context isn't essential to evaluating the pipeline.)

**Stage 2 — Synthesis (design complete, runs manually).** A human opens a Claude chat with a Google Drive connector, Claude reads the week's corpus, applies a prioritization scoring model (below), and drafts a "staging brief." The operator explicitly decided **not** to automate this yet — an automated path exists on paper (a Python script on Ravenor calling the Anthropic API) but he's not ready to take on the API cost/complexity. So synthesis is human-triggered weekly for now.

**Stage 3 — Distribution (not built).** The staging brief is deliberately a *content-only* artifact with no handling markings. It gets lifted into a separate "distribution template" where presentation, deeper analysis, and a TLP:CLEAR handling marking are applied before publishing. That template doesn't exist yet.

**The human gate.** Every brief gets a human analyst review before publishing — verifying claims against primary sources, cutting items, fixing framing. The scoring model orders and prioritizes; the human always overrides.

---

## 3. The intelligence requirements model (the interesting part)

Collection is deliberately a **wide net** governed by a single broad Key Intelligence Question (KIQ): *what cyber threats endanger California SLTT organizations and the infrastructure they depend on?* Anything credibly cyber-threat-relevant is collected. Filtering happens downstream, not at collection.

Prioritization is governed by four Priority Intelligence Requirements (PIRs) and a **multiplicative scoring model**:

**Score = (tier weight) × (product of elevation multipliers)**

Base tier weights (an item takes its single highest qualifying tier):
- Tier 1 — a California organization directly affected: **8.0**
- Tier 2 — an SLTT sector (water, K-12, local gov) targeted anywhere: **4.0**
- Tier 3 — actively-exploited vuln (CISA KEV) in SLTT-common tech: **2.0**
- Tier 4 — broad/national threat with SLTT relevance: **1.0**

Elevation multipliers (absent = 1.0, so they never suppress; present = boost):
- Actively exploited / on CISA KEV: ×1.5
- Affects low-maturity SLTT tech: ×1.5
- Supply-chain / procurement angle: ×1.3
- Ransomware against public-sector / critical infrastructure: ×1.3

**Design intent — "convergence wins."** The tier spacing (8/4/2/1) is deliberately narrow enough that a heavily-elevated lower-tier item can outrank a bare higher-tier one. Example: an out-of-state school ransomware incident on common tech (tier 2 × KEV × low-maturity × ransomware = 4.0 × 1.5 × 1.5 × 1.3 = 11.7) outranks a quiet California breach with no urgency signals (tier 1 = 8.0). This mirrors the analyst's threat-convergence philosophy (Intent × Opportunity × Capability). It was a deliberate, explicitly-confirmed choice, not an accident. The score is an ordering aid; analyst judgment overrides it.

**Question for reviewers:** Is a multiplicative model the right call here, or does it over-reward convergence? Are the specific weights (8/4/2/1 and the 1.3–1.5 multipliers) defensible, or arbitrary? They're explicitly flagged as "tune empirically over the first several editions."

---

## 4. Feed collection strategy

Two very different feed classes were built:

**National feeds (high-volume, mostly low-weight):** ~40 sources — government/CERT advisories (CISA, MS-ISAC, CERT/CC), vendor PSIRTs (Fortinet, Cisco, Palo Alto, Microsoft), exploitation-evidence feeds (GreyNoise, Rapid7, ZDI), and cyber news/research (Krebs, BleepingComputer, The Hacker News, Dark Reading, The Record, etc.). These were sourced partly from the analyst's own Feedly export (which turned out to be stale — a third of its URLs pointed to dead/moved feeds) and partly from a live-polled public CTI feed directory.

**AOR local feeds (the hard part — first attempt failed, now being rebuilt):** The original approach used ~46 Google News RSS *query* feeds scoped to California — statewide queries, sector queries, and one query per AOR county (34 counties). The intent was sound: a ransomware hit on a small California county or school district usually never reaches national cyber press, so the pipeline needed a local sensor. **The execution was wrong.** Google News keyword queries return everything matching a county *name* and treat the cyber terms as loose hints, not hard filters — so the county feeds returned mostly irrelevant local news (traffic accidents, county fairs, wildlife) and near-zero actual cyber incidents. These 34 county feeds were **dropped** as noise. The lesson: keyword search on a general news index is the wrong instrument for precision local-incident detection.

The rebuild uses **curated reliable sources ingested wholesale**, with AOR relevance decided by the scoring layer rather than by keyword pre-filtering: gov/SLTT trade press (StateScoop, EdScoop, GovTech, K-12 Dive), California regional outlets (Sacramento/Fresno/Modesto Bees, CalMatters), and official California sources (MS-ISAC — the multi-state SLTT ISAC, Cal OES, California Dept. of Technology). This candidate set is assembled but not yet verified/loaded.

**Known unsolved issue — the CA Attorney General breach list.** California's DOJ publishes a registry of organizations that reported breaches affecting Californians. This is arguably the single highest-value AOR source — a literal list of in-scope breached orgs, and the authoritative version of what the county feeds were poorly approximating. But it's a web portal, not an RSS feed, so the current collector can't ingest it. It needs a custom scraper. Flagged, not built.

**Every feed URL is verified against the collector's actual network egress** (HTTP status check) before loading — because a feed that works from a browser may 403 from a datacenter/server IP.

**Operating doctrine (settled this effort):** *quality over quantity.* Use reliable sensors, exploit each fully, and pursue diversity among them — but a feed earns its place only if it is both reliable AND additive (offers a vantage the others don't). A noisy sensor gets dropped, not patched. Coverage is a property that emerges from good sensors well-operated, not a target chased by adding feeds.

---

## 5. A real technical problem that got solved (worth scrutiny)

Google News RSS links are **redirect tokens, not publisher URLs.** The collector originally deduplicated by hashing the article URL. With ~46 overlapping Google News query feeds, the same California breach caught by three different queries would produce three *different* redirect tokens → all three pass URL-dedup → the same story lands in the corpus multiple times.

The fix: a second deduplication pass keyed on a **normalized article title** (lowercased, punctuation stripped, trailing outlet suffix like "- BleepingComputer" removed, hashed). An article is stored only if both its URL-hash and its title-hash are new. This was tested (three title variants of the same story correctly collapsed to one; genuinely different stories stayed separate) and deployed.

**Questions for reviewers:**
- Is title-normalization dedup robust enough, or will it false-merge distinct stories with similar headlines (e.g., "County X hit by ransomware" vs. "County Y hit by ransomware" — these differ, but aggressive normalization could be risky on very generic headlines)?
- The dedup has a `MIN_TITLE_LEN` guard (titles under 15 normalized chars aren't title-deduped, falling back to URL-dedup alone). Is that threshold sensible?

---

## 6. Current state (as of this session)

**Working and autonomous:**
- Collector runs daily, ~49 verified national trusted-source feeds live (county keyword feeds removed).
- Title-dedup deployed and **confirmed working**: the first full pull over the expanded feed set collected ~5,961 articles; the immediate second run collected only 124 — a 98% drop, proving dedup collapses the overlap rather than re-storing it. The ~5,961 was a **one-time backfill** (Google News returns up to ~100 items per query going back ~6 days). Steady-state daily collection is expected in the low hundreds.
- A staging brief was produced from the cleaned corpus (edition v20260810), led by a CISA warning on active threat-actor targeting of water/wastewater operational-technology (PLCs) — a strong, directly SLTT-relevant lead. Analyst verification pass still pending.

**Corrected this effort:**
- The 34 county Google News keyword feeds were dropped as noise (they returned local news, not cyber incidents). AOR-direct coverage is being rebuilt on curated reliable sources plus the CA AG breach registry.

**Deliberately deferred:**
- Automated synthesis (Anthropic API on Ravenor) — operator not ready for token cost/complexity. Synthesis stays manual.
- Distribution template + TLP:CLEAR handling layer.
- CA AG breach-list scraper.
- Host monitoring (Wazuh agent) on the collector VM.

**Open questions the operator would value outside input on:**
1. **Corpus volume vs. synthesis load.** The expanded feed set produces a large corpus — the first pull was ~6,000 articles (one-time backfill), and steady-state will likely be a few hundred per week. That is a large haystack from which to hand-draft a 5–8 item brief. Is the scoring model sufficient to manage that, or does the collection net need tightening, or a smarter automated pre-filter ahead of the human? This is the single question the operator most wants outside input on.
2. **Scoring model validity.** Multiplicative convergence — sound, or over-engineered? Weights defensible?
3. **Local-incident detection for a specific region.** The first attempt (Google News keyword queries per county) failed — keyword search on a general news index returns the region's whole news firehose, not its cyber incidents. The current plan is curated reliable regional/official sources plus the authoritative state breach registry. Is that the right approach, or is there a better mechanism to catch small-org breaches in a defined geographic area that a working CTI shop would use?
4. **The dedup approach.** Robust, or fragile on generic headlines?
5. **What's missing?** Any obvious source, signal, or step a working CTI shop would include that isn't here?

---

## 7. What this is *not*

- Not a real-time alerting system. Weekly cadence, OSINT-only.
- Not classified or handling sensitive intelligence — all open-source, and the published product is TLP:CLEAR (freely shareable).
- Not automated end-to-end — a human synthesizes and reviews every edition by design.
- Not a commercial or production MSSP — a single analyst's structured workflow.

---

*End of briefing. Critique welcome on the scoring model, the collection strategy, the dedup design, the corpus-volume problem, and anything a fresh set of eyes thinks is wrong, missing, or over-built.*
