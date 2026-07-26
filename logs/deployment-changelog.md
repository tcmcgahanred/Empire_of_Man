# empire_of_man — Master Build Log & Changelog

This document consolidates the full project history: the original
2025 SOCaaS/MSSP-era infrastructure work (R640 + pfSense + Ubuntu) and the 2026 detection-engineering-focused rebuild). Cleaned up and de-duplicated from source notes — no content
removed, only reorganized and duplicate sections collapsed.

---

# PART 1 — 2025: Original STC-SOCaaS_v1 / Empire_of_Man Build (R640, pfSense)

## [2025-05-08] Phase 1 — ESXi Deployment + Lab Network Segmentation

### Hardware / Firmware
- Mounted Dell PowerEdge R640 into Vevor open-frame rack
- Service Tag: `[REDACTED — see local notes]`
- iDRAC9 configured via USB — static IP `192.168.4.120/24`, gateway `192.168.4.1`
- Firmware updated via iDRAC:
  - SAS-RAID: `SAS-RAID_Firmware_700GG_WN64_25.5.9.0001_A17_01`
  - iDRAC: `iDRAC-with-Lifecycle-Controller-Firmware_RVDDR_WN64_7.00.00.181_A00`
  - BIOS: `BIOS_J6D53_WN64_2.23.0`
- Created RAID 10 virtual disk across 4 drives using PERC H730P

### ESXi Install
- Installed VMware ESXi 8.0 Update 2 (Dell-custom ISO)
- ESXi host static IP: `192.168.4.40`
- Hostname: `Lionsgate` (https://Lionsgate/)
- DNS: Primary `8.8.8.8`, Alternate `1.1.1.1`
- Created secondary ESXi admin account: `custodian`
- Management network isolated using `vSwitch0` → `vmnic0` → Eero

### vSwitch-palace (Segmented Lab Virtual Switch)
- Created `vSwitch-palace` with no uplinks
- VLAN-tagged port groups created:
  - `PG-VLAN10` (vlan10) — Lab Clients
  - `PG-VLAN20` (vlan20) — Lab Servers
  - `PG-VLAN30` (vlan30) — DMZ
  - `PG-VLAN40` (vlan40) — Red Team
  - `PG-Custodes` (vlan100) — Admin / CustodianNet
- Promiscuous mode, MAC address changes, and forged transmits enabled on VLANs 10–40
- `PG-Custodes` deliberately left locked down (no promiscuous mode)

### pfSense Prep
- Downloaded pfSense CE AMD64 ISO from Netgate (pfsense.org/download)
- Used 7-Zip to extract the `.gz`-compressed installer ISO
- Deployed new VM `Rogal_Dorn` for pfSense
- Initially added 5 NICs (one per port group: VLAN10/20/30/40 + Custodes)
- Attempted interface assignment with `vmx0` (MAC `00:0c:29:40:2b:f8`) but hit installer limitations with this many NICs

---

## [2025-05-09] Rollback to Simplified Lab Core

- Removed unused NICs from `Rogal_Dorn` to simplify — full 5-NIC layout was unworkable at install time
- **Retained 3 NICs:**
  - NIC 1 → `PG-Custodes` (vlan100) → MAC `00:0c:29:40:2b:f8`
  - NIC 2 → `PG-VLAN10` (vlan10) → MAC `00:0c:29:40:2b:02`
  - NIC 3 → `VM Network` (default, vSwitch0) → MAC `00:0c:29:40:2b:0c`
- Rebuilt pfSense with a simplified two-NIC core layout:
  - **WAN** → VM Network (via vSwitch0), MAC `00:0c:29:40:2b:0c`
  - **LAN** → PG-VLAN10 (Lab Clients), MAC `00:0c:29:40:2b:02`
- Completed pfSense CE installation, reached initial configuration wizard
- Skipped Netgate cloud services, proceeded local-only
- Verified LAN connectivity to `192.168.1.1` from VLAN10

### Active Network Configuration (as of 2025-05-09)
**vSwitch0 (Management & WAN)**
- Connected to `vmnic0` (Eero LAN)
- Port groups: `VM Network` (active WAN for pfSense), `PG-WAN` (VLAN 60, reserved for future use)

**vSwitch-palace (Segmented Lab)**
- `PG-VLAN10` → vmx3 → MAC `00:0c:29:40:2b:02`
- `PG-Custodes` → vmx1 → MAC `00:0c:29:40:2b:f8`

### pfSense Interface Assignment (reference)
- WAN: vmx2, v4/DHCP4 → `192.168.4.187/22`
- LAN: vmx1 → `10.0.10.1/24`
- OPT1: vmx0
- Default credentials at this stage: `admin` / `[REDACTED — default pfSense credential, see password manager]`

### Execution Phase Roadmap (established 2025-05-09)
| Phase | Description |
|-------|-------------|
| 0 | Rack and power on server |
| 1 | Install VMware ESXi |
| 2 | Deploy pfSense with basic WAN/LAN setup |
| 3 | Build vSwitches and VLAN port groups |
| 4 | Deploy client/server/DMZ VMs |
| 5 | Deploy IDS and SIEM stack |
| 6 | Build Range Admin VM |
| 7 | Harden and test AWS jump server |
| 8 | Connect cloud jump box to lab |
| 9 | Monitor home network via SPAN |
| 10 | Begin threat emulation + detection testing |
| 11 | Deploy TheHive and Cortex for SOAR |

---

## [2025-05-12] Provisioning of Emperor_of_Mankind (SOCaaS Admin Node)

### Infrastructure Events
- Verified `pg-custodes` port group mapping in ESXi
- Diagnosed initial networking failure: `Rogal_Dorn` simply wasn't powered on
- Corrected VM network segmentation:
  - Reassigned one of `Rogal_Dorn`'s NICs from `pg-vlan10` to `pg-custodes`
  - Reassigned pfSense's LAN interface to this NIC, confirmed set to `10.0.10.1/24`
- Brought `Emperor_of_Mankind` online with static IP `10.0.10.10` via Netplan (modern route syntax)

### Ubuntu Workstation Stabilization
- Resolved black-screen issue post-install using `nomodeset` kernel parameter in GRUB
- Made `nomodeset` permanent for graphical session stability
- Installed `open-vm-tools` and `open-vm-tools-desktop` to restore clipboard/display integration

### Provisioning Script — `provision.sh`
Authored and executed full provisioning/baseline script:
- Updated system packages
- Installed essential tooling: `curl`, `git`, `zsh`, `ufw`, `fail2ban`
- Set hostname to `Emperor_of_Mankind`, updated `/etc/hosts`
- Created hardened admin user `malcador-the-sigillite`
- Disabled root SSH login and password-based auth
- Configured UFW to allow only SSH inbound
- Enabled `fail2ban` for brute-force protection
- Script logs its actions via `tee` to `~/Desktop/hardening_log.txt`

### SSH Key Setup Script — `setup_ssh_key.sh`
Companion script to install an SSH public key for `malcador-the-sigillite`:
- Creates `.ssh` directory
- Sets up `authorized_keys`
- Enforces correct permissions/ownership
- Commented for deferred/later use

### Knowledge Notes
- Ubuntu usernames must follow `NAME_REGEX`: lowercase letters, numbers, and dashes only
- `gateway4` is deprecated in Netplan; replaced by `routes: - to: default via: x.x.x.x`
- `nomodeset` disables GPU driver loading (avoids crashes) but also disables dynamic resolution

### Artifacts Created
- `provision.sh` — full provisioning and hardening script
- `setup_ssh_key.sh` — SSH key installation script for admin account
- `hardening_log.txt` — runtime log of provisioning actions

---

## Cumulative Update — [Through 2025-05-20]

### Infrastructure Changes
- Verified functional ESXi 8.0.2 installation on the R640
- Mounted and configured pfSense VM (`Rogal_Dorn`) with WAN/LAN:
  - WAN: `192.168.4.187` (via VM Network)
  - LAN: `10.0.10.1` (via `pg-custodes`)
- Configured and validated pfSense DHCP, firewall, and interface rules
- Successfully segmented LAN-side traffic via `vSwitch-palace` and `pg-custodes`
- Confirmed `Emperor_of_Mankind` has full IP and DNS reachability via pfSense

### Git & Documentation
- Reorganized GitHub repo (`Empire_of_Man`) with structure:
  - `configs/` (subfolders: Appliances, Networking, VMs)
  - `diagrams/` (`.drawio` and `.png` topology maps)
  - `playbooks/`, `Security/`, `logs/`, `dependencies/`
- Added README structural section describing all directories
- Wrote detailed `README.md` and `configs/README.md` for component tracking
- Created `COMPONENTS.md` and asset tables for: implemented VMs, software appliances, installed blue team tooling on the analyst workstation

### Strategic Decisions
- Chose **not** to route all home traffic through pfSense
- Retained Eero mesh as the primary home network routing layer
- pfSense scoped specifically for lab-side segmentation and future VLAN control only

### Detection & Visibility Direction
- Selected **agent-based telemetry** (Wazuh agents) over passive wire mirroring
- Deferred Security Onion deployment to a later phase
- Wazuh manager planned on an internal VM, agents deployed to `Emperor_of_Mankind` and future test systems / optional external clients
- Telemetry strategy designed to minimize infrastructure disruption

### Launch Automation
- Built PowerShell script `Launch-SOCaaS.ps1` to automate:
  - Opening the Git repo folder
  - Launching VS Code in project context
  - Opening ChatGPT in browser
  - Opening the ESXi host interface (`https://192.168.4.40`)
- Integrated Windows Text-to-Speech voice cue: *"All systems online, Archmagos. The Emperor protects."*
- Created `.vbs` wrapper (`Launch-SOCaaS.vbs`) to silently run the `.ps1` — later reverted in favor of running `.ps1` directly from desktop

### Miscellaneous & Support Tools
- Created draw.io network topology diagram for the environment
- Discussed router upgrade options; deferred Eero replacement
- Clarified port groups vs. VLANs in ESXi
- Validated pfSense routing between `vmx0` and `vmx1`
- Confirmed physical NIC → vSwitch → VM mappings on ESXi

### Status as of 2025-05-20
- Core components active: Dell R640, pfSense (`Rogal_Dorn`), Ubuntu Analyst Node (`Emperor_of_Mankind`)
- Git, VS Code, and workflow automation operational
- Lab telemetry-ready for Wazuh deployment
- System start script tested and functional

---

# PART 2 — 2026: Detection-Engineering Rebuild (Lenovo + R640)

> **Side quest begins here.** Roughly one year after Part 1, the ESXi
> license on the R640 had expired and the project pivoted: descoped from
> SOCaaS/MSSP ambitions to a focused skills-development lab for resume
> and interview material. Work resumed on a Lenovo laptop using VMware
> Workstation Pro before eventually returning to rebuild the R640
> properly later in the timeline.

## [2026-06-17] Session 1 — Pivot to Lenovo, Initial Build

### Session Summary
Pivoted from R640/ESXi (license expired, full rebuild required) to a
local VMware Workstation Pro lab on the Lenovo laptop. Descoped from
SOCaaS/MSSP ambitions to a focused skills-development lab: detection
engineering reps for resume/interview material. Stack simplified to bare
minimum: Wazuh + one Windows target running Atomic Red Team.

### Decisions Made
- **Project purpose re-scoped:** empire_of_man is for skills development
  and resume building, not a production MSSP. Revisit broader SOCaaS
  ambitions in 1+ year if still relevant.
- **R640 status:** ESXi license expired. Full hypervisor rebuild required
  (3-drive RAID, nothing of value to retain — OK to wipe). Deferred, not
  blocking current lab work.
- **Primary build platform:** Lenovo laptop (Windows 11 Pro, Intel Core
  Ultra 5 125U, 32GB RAM, VMware Workstation Pro) instead of R640.
- **Cloud/multi-tenant idea (Wazuh for friends' networks) — rejected.**
  Introduces data-at-rest, retention, and liability concerns that
  reintroduce the MSSP scope creep already deliberately avoided.
- **Splunk Attack Range** — confirmed still active (v5), but local
  deployment is deprecated by Splunk (Ludus recommended instead). Not
  pursued; going with Atomic Red Team locally instead.
- **VPN for remote lab access:** WireGuard recommended over PIA/OpenVPN/
  IPsec/Tailscale/ZeroTier for future remote access into R640/home
  network — lightweight, simple config, pairs well with pfSense
  (`Rogal_Dorn`).

### Minimum Viable Lab — Target Architecture
| VM | Purpose | Specs |
|----|---------|-------|
| Windows 10 Pro (target) | Atomic Red Team victim, Sysmon + Wazuh agent | 2 vCPU, 4GB RAM, 60GB disk, NAT |
| Wazuh (Ubuntu 22.04 Server) | SIEM/HIDS, single-node install | 2 vCPU, 4GB RAM, 50GB disk, NAT |

Planned install order: Wazuh agent → Sysmon (Olaf Hartong config) →
Atomic Red Team → run first technique → validate detection in dashboard.

### Build Progress
- **Windows 10 target VM created** in VMware Workstation Pro:
  - Custom config, UEFI (no Secure Boot — avoids blocking unsigned
    tools/test payloads), 2 vCPU / 1 socket, 4096MB RAM, NAT networking,
    LSI Logic SAS controller, 60GB virtual disk
  - Windows 10 Pro selected (avoided "N" edition)
  - Skipped product key (runs unactivated — cosmetic watermark only, no
    functional limitation for lab use)
  - Clean install ("Custom: Install Windows only")
  - Bypassed Microsoft account via **Offline account** option
  - **Local account created:** Username `horus` / Password `[REDACTED — see password manager]` /
    Security question answers: `[REDACTED — see password manager]`
- Ubuntu 22.04 Server ISO downloaded, queued for the Wazuh VM (not yet
  built as of end of session)

### Notes / Reminders
- Credentials above are for an isolated, NAT'd, non-internet-facing lab
  VM. Low risk as configured. Revisit before any network exposure
  changes.
- Backlog (deferred 1+ year, only if still aligned with goals): Security
  Onion, TheHive, Cortex, OT/ICS target, R640 rebuild/expansion, cloud
  Wazuh for external endpoints.

---

## [2026-06-18] Session 2 — Wazuh VM Build, Indexer Crash

### Summary
Built the Ubuntu Server VM for Wazuh, installed Wazuh single-node, and
confirmed VM-to-VM networking with horus. Hit a blocking issue with the
`wazuh-indexer` service failing after a host reboot; paused mid-
troubleshooting.

### VM Naming
- Wazuh/Ubuntu VM named **Guilliman** (Primarch of the Ultramarines —
  thematically fitting: order/codification, matches what a SIEM does to
  raw log data). Considered Alpharius first, swapped to Guilliman.
- Ultramarines Legion motto for reference: **"Courage and Honour"**
  (longer form: "Courage and honour until the end and past it").

### Ubuntu (Guilliman) Build Steps — v1
- Ubuntu Server 22.04 LTS, full install, DHCP-assigned, no proxy
- Hostname: `guilliman` / Username: `guilliman` / Password: `[REDACTED — see password manager]`
- OpenSSH server installed, password auth allowed
- No featured snaps installed
- **Guilliman IP:** `192.168.76.130` (NAT, broadcast `192.168.76.255`)
- Confirmed ping connectivity both directions with horus

### Wazuh Install
```bash
sudo apt update && sudo apt upgrade -y
curl -O https://packages.wazuh.com/4.9/wazuh-install.sh
sudo bash ./wazuh-install.sh -a -i
```
(`-a` = all-in-one manager+indexer+dashboard; `-i` = ignore OS
compatibility false-positive warning. Note: capital **-O**, not zero —
easy typo.)

Install completed initially; generated admin dashboard credentials
(retrievable via `sudo tar -O -xvf wazuh-install-files.tar wazuh-install-files/wazuh-passwords.txt`).

### Issues Encountered
1. **Clipboard friction on VM console** — couldn't copy/paste the
   generated password from the Ubuntu console into the host browser.
   **Resolution: SSH into Guilliman from a native terminal** instead of
   the VMware console — copy/paste works normally over SSH.
2. **Dashboard login rejected admin credentials** — likely manual
   transcription error given password complexity.
3. **Host VM reset attempted as a fix** — did not resolve the login
   issue, and left `wazuh-indexer` in a failed state on reboot.
4. **`wazuh-indexer` failing to start post-reboot:**
   `Active: failed (Result: exit-code)`, exit status 1.
   - `journalctl -u wazuh-indexer` returned no entries (journal rotated)
   - `wazuh-cluster.log` existed but appeared empty when checked
   - `wazuh-passwords-tool.sh` attempts: first failed ("backup could not
     be created"); second gave mixed result — keystore update succeeded,
     but tool reported `ERR: Seems there is no OpenSearch running on
     localhost` — consistent with indexer being down
   - **Not resolved this session** — paused before checking
     `wazuh-cluster_server.json`

### Lesson Learned
Use SSH from a native terminal for all VM administration going forward,
not the VMware console — avoids clipboard issues entirely.

---

## [2026-06-18] Session 3 — Root Cause Found: Underprovisioned Guilliman

### Root Cause Identified
`wazuh-indexer` was crash-looping because **Guilliman was
underprovisioned**. Original build: 2 vCPU / 4GB RAM / 50GB disk.
Verified against Wazuh's official quickstart hardware table: **minimum
for an all-in-one deployment (up to 25 agents, 90 days history) is 4
CPU, 8GB RAM, 50GB disk.** We were at half the required RAM/CPU —
consistent with the JVM/OpenSearch-based indexer dying on startup.

### Resolution
Deleted the original Guilliman VM entirely and rebuilt clean rather than
continuing to debug an underprovisioned instance. (Windows also flagged
a warning about saving multiple VMs to the same C:\ folder — gave
Guilliman its own dedicated VM folder this time.)

### New Guilliman VM Specs
- **4 vCPUs** (up from 2) / **8GB RAM** (up from 4GB) / **100GB disk**
  (up from 50GB, extra headroom for log retention/scaling)
- LSI Logic SAS controller, NAT networking, dedicated VM folder

### Ubuntu Rebuild
- Same as before: Ubuntu Server 22.04 LTS, username `guilliman` /
  password `[REDACTED — see password manager]`, OpenSSH + password auth, no snaps
- **New Guilliman IP:** `192.168.76.132/24`, broadcast `192.168.76.255`

---

## [2026-06-18] Session 4 — Wazuh Stable, Agent Deployed on Horus

### Wazuh Dashboard Access
- Clean reinstall on properly-sized Guilliman — all services
  (`wazuh-indexer`, `wazuh-manager`, `wazuh-dashboard`) came up
  active/running with no errors.
- Logged into dashboard at `https://192.168.76.132`.
- **Reset dashboard admin password** via SSH:
  ```
  sudo /usr/share/wazuh-indexer/plugins/opensearch-security/tools/wazuh-passwords-tool.sh -u admin -p [REDACTED — see password manager]
  ```
  - Username: `admin` / Password: `[REDACTED — see password manager]`

### Agent Deployment — UI Navigation Note
Wazuh 4.9 dashboard nav for deploying a new agent is **not** under
"Agents management" (older version's label). Correct path: **Server
Management → Endpoint Summary → Deploy new agent**.

### Deploying Wazuh Agent on Horus
- Selected **Windows**, server address did **not** auto-fill — entered
  manually: `192.168.76.132`
- Generated install command:
  ```powershell
  Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.9.2-1.msi -OutFile $env:tmp\wazuh-agent; msiexec.exe /i $env:tmp\wazuh-agent /q WAZUH_MANAGER='192.168.76.132' WAZUH_AGENT_NAME='Horus'
  ```
- **Blocker:** couldn't paste the command into the horus VM console.
  Root cause: **VMware Tools not installed** on horus (clipboard sharing
  requires Tools in-guest, not just the host-side "Enable copy and
  paste" setting, which was already checked but had no effect).
- **Resolution:** Installed VMware Tools on horus (VM menu → Install
  VMware Tools → run setup.exe from mounted virtual CD → reboot).

---

## [2026-06-18] Session 5 — Sysmon + First Detection Validation

### Summary
Resolved clipboard issue via VMware Tools, deployed Sysmon
(SwiftOnSecurity config), and validated the full pipeline end to end:
Sysmon → Wazuh agent → Guilliman manager → indexer → dashboard.

### Wazuh Agent — Completed
- Confirmed **Active** status in dashboard after starting the agent
  service on horus.

### Sysmon Install — SwiftOnSecurity Config
- Chose SwiftOnSecurity over Olaf Hartong (originally planned) —
  simpler, well-documented, good Wazuh decoder compatibility.
- **Gotcha:** first config download was the GitHub *webpage* (HTML), not
  raw XML — caused `Failed to load xml configuration (could not read
  file)`. Confirmed by opening in Notepad and seeing `<!DOCTYPE html>`.
  **Fix:** use the raw URL:
  `https://raw.githubusercontent.com/SwiftOnSecurity/sysmon-config/master/sysmonconfig-export.xml`
- Install command:
  ```powershell
  .\Sysmon64.exe -i "C:\Users\horus\Desktop\sysmonconfig-export.xml" -accepteula
  ```
- Confirmed: `Sysmon64 installed.` / `SysmonDrv started.` / `Sysmon64
  started.` Verified local logging via `Get-WinEvent -LogName
  "Microsoft-Windows-Sysmon/Operational"`.

### Detection Validation — EID 1 Test
- Test trigger: `cmd.exe /c echo malware`
- **Initial result:** confirmed locally in Sysmon's own log, but **not**
  appearing in Wazuh dashboard searches — `agent.name` alone returned
  other Windows logs (Application/Security/System), but Sysmon-specific
  events were absent.
- **Root cause:** the agent's `ossec.conf` had **no `<localfile>` block
  for the Sysmon channel at all.** Confirmed via `ossec.log` tail showing
  the agent only analyzing Application/Security/System.
- **Fix:** manually added to `C:\Program Files (x86)\ossec-agent\ossec.conf`
  (left existing System block untouched, added as a new entry):
  ```xml
  <localfile>
    <location>Microsoft-Windows-Sysmon/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
  ```
  Saved, then `Restart-Service -Name WazuhSvc`.
- Re-ran the test — **EID 1 event successfully appeared in the
  dashboard.** Full pipeline validated end to end.

### Dashboard Notes (UI navigation, v4.9)
- "Deploy new agent" lives under **Server Management → Endpoint
  Summary**.
- Useful search queries:
  ```
  agent.name: Horus
  agent.name: Horus AND data.win.system.eventID: 1
  ```

### Lessons Learned (Session 5)
- Always download configs from raw/direct file URLs, not repo landing
  pages.
- VMware Tools is a prerequisite for clipboard sharing, not just the
  host-side setting — install it early in any new VM build.
- A Wazuh agent does not automatically pick up new Windows Event Log
  channels just because the log source exists on the endpoint — the
  channel must be explicitly added as a `<localfile>` entry in
  `ossec.conf`, even if installed after the agent. Good to remember for
  any future custom log source (PowerShell Operational logs, additional
  ETW providers, etc.).

---

## [2026-06-19] Session 6 — First Validated Detection (Documented)

### Summary
Located and confirmed the first real detection fired by Wazuh's default
ruleset against the `echo malware` Sysmon EID 1 test event. No custom
rule needed — out-of-the-box ruleset correctly identified and
MITRE-mapped the activity.

### Detection Details
- **Trigger:** `cmd.exe /c echo malware` from an elevated PowerShell
  session on horus
- **rule.id:** `92004`
- **rule.description:** "Powershell process spawned Windows command
  shell instance"
- **rule.level:** 4 — **rule.groups:** `sysmon`,
  `sysmon_eid1_detections`, `windows`
- **MITRE mapping:** Technique T1059.003 (Windows Command Shell),
  Tactic: Execution
- **Decoder:** `windows_eventchannel` — **Sysmon EID:** 1 (Process
  Create)
- Key fields confirmed populated: `data.win.eventdata.commandLine`,
  `parentImage` (PowerShell), `image` (cmd.exe), `user`
  (DESKTOP-HTHPCAF\Horus), `hashes` (MD5/SHA256/IMPHASH)

### Dashboard Search Notes
- Correct field for Sysmon process command line:
  `data.win.eventdata.commandLine` (not `data.win.system.message`, which
  holds the full raw rendered text but isn't the structured field).
- Useful query to isolate Sysmon EID 1 specifically (avoids collision
  with Security log events also using `win.system.eventID`):
  ```
  agent.name: Horus AND data.win.system.eventID: 1 AND data.win.system.channel: "Microsoft-Windows-Sysmon/Operational"
  ```
- "Edit Filter" UI expects a single field/operator/value triple, not a
  full DSL string — for compound DSL queries, use the main search bar
  and save via the floppy-disk/save icon. Also: the Edit Filter field
  picker only shows fields already indexed in the index pattern's field
  list (Dashboard Management → Index Patterns → refresh fields icon) —
  a field can be real and fully searchable via DSL while not yet
  appearing there.
- **Saved Queries** feature discovered — preferred over Edit Filter for
  reusable DSL strings.

### Why This Matters (Resume/Interview Value)
Clean, complete detection-engineering narrative: generated a
benign-but-suspicious parent/child process relationship → confirmed
capture at the OS level → diagnosed and fixed a real pipeline gap →
located the resulting alert and read its structured fields → mapped to
the exact MITRE ATT&CK technique/tactic Wazuh's default ruleset already
assigns.

---

## [2026-06-19] Session 7 — Atomic Red Team, Network Detection Planning, Major Architecture Decision

### Atomic Red Team — Installed and First Technique Run
- Initial install via `Install-AtomicRedTeam -getAtomics` appeared to
  succeed but the atomics folder was never actually created —
  `Invoke-AtomicTest T1057` failed with `Resolve-Path` errors. Deleted
  `C:\AtomicRedTeam` and reinstalled clean with `-Force`:
  ```powershell
  IEX (IWR 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing)
  Install-AtomicRedTeam -getAtomics -Force
  ```
  Confirmed `Test-Path "C:\AtomicRedTeam\atomics"` returned `True`.
- Required `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope
  Process -Force` before atomics would run.
- **First real technique run: T1057 (Process Discovery)** — executed
  successfully via `Invoke-AtomicTest T1057`.

### Network/Server-Side Detection — Research & Planning
Discussed long-term goal: writing original detection rules for newly
disclosed CVEs (motivating example: **CVE-2026-10520**, a critical
CVSS 10.0 pre-auth OS command injection in Ivanti Sentry, added to CISA
KEV, public PoC available — confirmed via live web search). Concluded
this class of detection is primarily network/web-layer, not host-layer,
since the lab doesn't run a vulnerable Sentry instance.

**Key architectural clarifications reached this session:**
- **Wazuh is a log-based SIEM/HIDS, not a packet-inspecting NIDS.** No
  native packet sniffing/signature-matching. Can ingest Suricata's
  `eve.json` alerts as a log source (same `<localfile>` pattern as the
  Sysmon fix) — sensible correlation pattern, but Suricata has to do the
  actual detection first.
- **Suricata vs. Zeek:** Suricata = signature-based alerting (smoke
  detector). Zeek = behavioral/metadata logging of all traffic, built
  for retrospective threat hunting (security camera). Real deployments
  run both.
- **Security Onion** is an NSM platform, not strictly a SIEM, despite UI
  overlap. Confirmed current official minimums: Standalone needs **24GB
  RAM / 4 CPU / 200GB** minimum; a lighter **Eval** install type exists
  for homelab use, minimum **12GB RAM**, explicitly not for production
  (drops Logstash/Redis).

### Major Decision — Split Architecture (Lenovo vs. R640)
Walked through alternatives before converging:
- EC2 + VPN tunnel back to Lenovo — rejected: VPN provides routing, not
  traffic mirroring; EC2 Security Onion would only see EC2's own
  traffic.
- EC2 as a deliberately open ("wild") honeypot — real value
  acknowledged, but flagged cost/ToS exposure and incompatibility with
  clean purple-team ground truth if mixed with random internet noise.
- Kali (Lenovo) attacking an IP-locked EC2 target — clean but solves a
  problem the already-owned R640 solves for free.

**Final decision: split the lab across two physical hosts by role:**
- **Lenovo (mobile/disposable)** — attacker tooling, victim/target
  machines, traffic-generating sensors: Horus, future Kali VM, future
  additional targets. Rationale: portable, useful anywhere, keeps attack
  tooling separate from defensive infrastructure.
- **R640 (centralized/persistent)** — Guilliman (Wazuh), Rogal_Dorn
  (pfSense), Security Onion (full Standalone spec), revisit
  TheHive/Cortex later. Rationale: ample headroom (dual Xeon, 64–128GB)
  removes every resource constraint hit on the Lenovo so far.
- **Connectivity:** WireGuard VPN server on Rogal_Dorn for remote
  access — chosen because pfSense has it built in natively AND because
  **pfSense is commonly used by DoW Cyber Protection Teams** (direct
  career relevance, not just convenience).
- Enables a genuine purple-team workflow: Kali on the Lenovo connects
  via WireGuard into the home network and attacks targets/services on
  the R640, while Guilliman and Security Onion observe and alert — clean
  attacker/defender separation with real segmentation (PG-VLAN10,
  PG-Custodes) via Rogal_Dorn.

---

## [2026-06-19] Session 8 — R640 / ESXi Rebuild

### Summary
Successfully reinstalled ESXi 8.0U3e on the R640 via iDRAC virtual
media, after working through several iDRAC/virtual console issues.
Confirmed the host is licensed (free, no expiration) and accessible.
Old VMs (`Rogal_Dorn`, `Emperor_of_Mankind`, `Sanguinius`) and their
datastore contents were intentionally wiped — nothing of value retained,
per prior decision.

### Pre-Wipe Verification
- Single datastore (`datastore1`, non-SSD, 3.37TB capacity, ~98.5GB
  provisioned, VMFS6) — consistent with the 3-drive RAID array
  presenting as one logical volume, separate from whatever small device
  ESXi boots from.
- Confirmed three VMs registered (`Rogal_Dorn`, `Emperor_of_Mankind`,
  `Sanguinius`) — reviewed, deliberately not retained.

### iDRAC Access — Recovered From Notes
- iDRAC had never been physically connected to the network in this
  session's starting state (only the main ESXi NIC was cabled).
- **iDRAC IP recovered from prior personal notes:** `192.168.4.120`
  (matches the original 2025-05-08 configuration — could not be found
  via generic online guidance, only recoverable because previously
  documented).
- iDRAC firmware: `7.00.00.181` (iDRAC9-generation), matching the
  original 2025 firmware update record.
- Credentials retrieved from Keeper vault.

### ISO Acquisition
- Downloaded `VMware-VMvisor-Installer-8.0U3e-24677879.x86_64.iso`
  (618.34 MB / 648,374,272 bytes — verified against official published
  size) from the Broadcom Support Portal.
- **Confirmed via web search:** this specific build is the **Free
  Edition** with the license **embedded directly in the image** — no
  separate key needs to be requested or applied. (A visually similar
  "Evaluation/Paid" build exists under a different build number —
  `24674464` — which does require a separate key; `24677879` does not.)
- Confirmed post-install under Manage → Licensing: **vSphere 8
  Hypervisor, Key `[REDACTED — see password manager]`, Expiration: Never.**

### Boot/Install Troubleshooting (iDRAC Virtual Media)
Root causes, in order discovered:
1. **First download location was inside OneDrive** — moved to a local
   `C:\` path before mounting (cloud-sync placeholder files can cause
   virtual media mount issues).
2. **"Map Device" button was never actually clicked** in earlier
   attempts — the ISO appeared selected but was never truly attached,
   causing "Boot failed" when Virtual Optical Drive was selected.
3. **Stale/orphaned Virtual Media session** — console reported "Virtual
   Media is currently unavailable, a session is in use" with nothing
   visibly mounted anywhere in the UI. **Fix: reset iDRAC itself**
   (iDRAC Settings → Reset iDRAC) — a soft reset of the management
   controller only, does not affect server power state. Mapping
   succeeded cleanly afterward.
4. Confirmed boot mode (System Setup/F2 → System BIOS → Boot Settings)
   was already correctly set to **UEFI**, ruling out a mismatch.
- Successful path: iDRAC Virtual Console → Virtual Media → Connect
  Virtual Media → Map CD/DVD → browse to local ISO → **Map Device**
  (critical step) → reboot (Reset from iDRAC Power menu) → click into
  console for keyboard focus → **F11** during POST → One-shot UEFI Boot
  Menu → **Virtual Optical Drive**.

### Install
- Selected `datastore1` as install target, confirmed overwrite (nothing
  retained).
- Set a root password during install (later determined to likely match
  the existing iDRAC `root` password due to credential reuse — caused
  brief confusion post-install about which password applied to the
  Host Client login; resolved by trying the iDRAC credential, which
  worked).

### Current State
- ESXi 8.0U3e installed, licensed (free, no expiration), accessible via
  Host Client.
- Logged in as `root` (shared credential with iDRAC, by reuse rather
  than design).
- **Backlog item raised:** create a dedicated ESXi local admin account
  (Manage → Security & Users → Users) and reserve root for break-glass
  use only. Not yet done.

### Lessons Learned (Session 8)
- For Dell iDRAC virtual media installs, always explicitly click "Map
  Device" after browsing to the ISO — visual selection in a dialog is
  not the same as attachment.
- If virtual media shows a conflicting/stuck state ("session in use"
  with nothing visibly mounted), resetting iDRAC itself (not the
  server) is a safe, fast fix.
- Avoid mounting ISOs for virtual media directly from cloud-sync
  folders — move to a fully local path first.
- Verify the exact ISO build number, not just the version string —
  Broadcom publishes visually similar "Free Edition" vs.
  "Evaluation/Paid" ISOs for the same version under different build
  numbers; only one has the license embedded.
- Credential reuse across iDRAC and ESXi root can cause confusion
  later — use distinct passwords for distinct credential sets going
  forward, labeled clearly in the password manager (e.g., "ESXi root —
  Lions Gate" vs. "iDRAC — Lions Gate").

---

## Consolidated Open Items / Backlog (as of 2026-06-19)

### R640 (centralized/persistent infrastructure)
- [ ] Create dedicated ESXi admin user account (move off root for daily use)
- [ ] Rebuild Rogal_Dorn (pfSense) on the fresh ESXi host
- [ ] Configure WireGuard on Rogal_Dorn for remote access (DoW CPT tool familiarity)
- [ ] Rebuild/migrate Guilliman (Wazuh) to R640 — full spec, no resource constraints
- [ ] Build Security Onion on R640 (full Standalone spec: 24GB+ RAM, 4+ CPU, 200GB+ storage), segmented behind Rogal_Dorn
- [ ] Revisit TheHive/Cortex backlog (originally part of 2025 architecture)

### Lenovo (mobile/disposable infrastructure)
- [ ] Continue Atomic Red Team technique testing on Horus
- [ ] Build Kali VM (attacker role)
- [ ] Consider additional lightweight target VMs (Linux, vulnerable web app)

### Long-Term / Cross-Cutting
- [ ] Write an original Suricata detection rule for a real disclosed CVE and validate it against self-generated attack traffic from Kali
- [ ] Set up Git repo + VS Code for empire_of_man project tracking
- [ ] Draft `.gitignore` before any public-facing commit (credentials, sensitive configs)
- [ ] OT/ICS target VM (long-deferred backlog item, differentiator given Cal-CSIC CI focus)

### Notes / Reminders (carried forward)
- Lab credentials documented in this log are for isolated, NAT'd,
  non-internet-facing VMs. Low risk as configured — revisit before any
  network exposure changes.
- Project scope is deliberately bounded to skills development and
  resume/interview material, not a production MSSP — re-evaluate broader
  SOCaaS ambitions no sooner than 1+ year from the 2026-06-17 rescope
  decision.

---

## [2026-06-19] Naming Convention Update — Host Designations

Established formal Warhammer 40K-themed names for the two physical
hosts going forward, to keep documentation and conversation consistent:

- **EoM ("Empire of Man")** — the Dell R640. Centralized/persistent
  analytical infrastructure: Guilliman (Wazuh), Rogal_Dorn (pfSense,
  with WireGuard), future Suricata VM, future Security Onion.
- **VS ("Vengeful Spirit")** — the Lenovo laptop. Named for Horus's
  Gloriana-class flagship (confirmed via web search — not to be confused
  with "The Invincible Reason," which is actually Roboute Guilliman's
  flagship). Mobile/disposable infrastructure: Horus (Win10 target),
  future Kali VM, future additional targets.

### Confirmed Next Tasks (carried forward from Session 7/8 decisions)
1. Push analytical solutions (Guilliman, future Suricata VM) to EoM
2. Implement remote access capability via WireGuard on Rogal_Dorn (EoM)
3. Install Kali on VS (Lenovo)

---

## [2026-06-19/20] Session 9 — Kali on VS, Cursor Bug Resolved

### Kali Linux — Installed on VS (Lenovo)
- Downloaded the official **prebuilt Kali VMware image** (kali.org/get-kali
  → Virtual Machines tab) rather than doing a manual ISO install — much
  faster, boots straight to a working desktop with the full standard
  toolset preinstalled (Metasploit, nmap, Burp, etc.)
- Default credentials: `kali` / `kali` — flagged to change via `passwd`
- Ran full system update:
  ```bash
  sudo apt update && sudo apt full-upgrade -y
  ```
- Installed VMware Tools equivalent:
  ```bash
  sudo apt install open-vm-tools open-vm-tools-desktop -y
  ```

### Issue — Invisible Cursor + Severe Lag
- VM cursor was completely invisible (though clicking/input still worked
  — confirmed as a rendering issue, not a true input failure).
- Initial troubleshooting (3D acceleration toggle, display mode switch,
  service status checks, full system upgrade) did not resolve it.
- **Root cause #1 (performance/lag):** the Kali VM was running from a
  **OneDrive-synced folder** rather than local disk — same root cause
  pattern as the ISO-mounting issue hit during the R640/ESXi rebuild
  (Session 8). **Fix:** shut down VM, moved the VM folder to a local
  `C:\` path alongside Horus/Guilliman, unregistered and re-added the VM
  in VMware Workstation from the new location. Resolved the lag.
- **Root cause #2 (invisible cursor, persisted after the OneDrive fix):**
  outdated **virtual hardware compatibility version** on the VM. The
  in-app toggle for "Accelerate 3D graphics" was inaccessible/grayed out,
  which in retrospect was likely a symptom of the same underlying
  compatibility mismatch. **Fix: upgraded the VM's hardware compatibility
  version to the most recent available in VMware Workstation** — this
  fully resolved the cursor issue with no further changes needed.

### Naming Note (carried from prior session)
- Decided to rename the Win10 target VM from **Horus** to **Isstvan III**
  (the planet Horus virus-bombed at the start of the Horus Heresy — a
  better thematic fit for a victim/target machine than Horus itself,
  which is now understood to be better suited to an attacker role).
  Rename not yet executed — flagged as a backlog item, since it requires
  updating the VM label, the Windows hostname, and the Wazuh agent
  registration to stay consistent (currently shows as "Horus" in the
  Guilliman dashboard).

### Lessons Learned (Session 9)
- **Never run a VM's working files from a cloud-sync folder
  (OneDrive/Dropbox/etc.)** — causes severe performance degradation.
  Always store VMs on a local-only path. This is now the second time
  this exact mistake has caused a real problem (previously: ISO mounting
  for the R640 ESXi reinstall in Session 8).
- **An outdated VM hardware compatibility version can manifest as a
  seemingly unrelated display bug** (invisible cursor) rather than an
  obvious compatibility error — when a Linux guest has cursor/SVGA
  rendering issues in VMware Workstation, check/upgrade the hardware
  compatibility version as a primary troubleshooting step, not a last
  resort.

### Open Items / Next Session
- [ ] Change Kali's default password (`passwd`)
- [ ] Note Kali's IP address for future reference
- [ ] Execute the Horus → Isstvan III rename (VM label, Windows hostname,
      Wazuh agent re-registration)
- [ ] Begin Rogal_Dorn (pfSense) rebuild on EoM (R640)
- [ ] Configure WireGuard on Rogal_Dorn once built
- [ ] Migrate/rebuild Guilliman (Wazuh) onto EoM

---

## [2026-06-20] Session 10 — Horus → Isstvan III Rename Completed

### Summary
Completed the full rename from "Horus" to "Isstvan III" across every
layer — VM label, Windows hostname, local user account, and Wazuh agent
registration — resolving the inconsistency flagged in Session 9.

### Steps Completed
1. **VMware Tools installed** on the VM before the rename/reboot pass
   (had not been confirmed installed previously under the old name).
2. **VM label** renamed in VMware Workstation to `Isstvan_III`.
3. **Local Windows user account** renamed:
   ```powershell
   Rename-LocalUser -Name "horus" -NewName "isstvan_3"
   ```
   (Underlying profile folder path unchanged, as expected — cosmetic
   account rename only.)
4. **Windows hostname** renamed via:
   ```powershell
   Rename-Computer -NewName "Isstvan_III" -Restart
   ```
5. **Old Wazuh agent entry removed** from Guilliman via CLI (dashboard
   UI did not expose a delete option in this version/view):
   ```bash
   sudo /var/ossec/bin/manage_agents
   ```
   Selected the interactive "remove an agent" option, removed the old
   "Horus" registration by agent ID.
6. **New Wazuh agent deployed** fresh from the dashboard (Server
   Management → Endpoint Summary → Deploy new agent), this time
   registered as **Isstvan_III**, server address `192.168.76.132`.
   Confirmed **Active** status in the dashboard.

### Keeper Vault
- Updated the corresponding entry: title/labels changed to "Isstvan III
  (formerly Horus)", username field updated to match the renamed local
  account. Password unchanged.

### Current State
- VM, Windows hostname, local user account, and Wazuh agent registration
  are now **fully consistent** under the name **Isstvan III** — no
  remaining references to "Horus" anywhere in active tooling.

### Open Items / Next Session
- [ ] Begin Rogal_Dorn (pfSense) rebuild on EoM (R640)
- [ ] Configure WireGuard on Rogal_Dorn once built
- [ ] Migrate/rebuild Guilliman (Wazuh) onto EoM
- [ ] Change Kali's default password (`passwd`) — still outstanding from Session 9
- [ ] Note Kali's IP address for future reference

## [2026-06-27] Session 11 — ESXi Daily-Driver Account, Rogal_Dorn VM Built, Security Onion Planning

### Summary
Created a non-root daily-driver account on the rebuilt EoM ESXi host.
Built the Rogal_Dorn (pfSense) VM from scratch on EoM with three NICs,
created a new internal vSwitch and two VLAN-tagged port groups, and
wired Rogal_Dorn's NICs to them. Decided Security Onion will be a third
EoM appliance, named **Valdor**, and that it will get its own dedicated
VLAN separate from Guilliman rather than sharing one with it. Also
explored (and deferred) several architectural questions: EC2 as a
WireGuard relay, dedicated pfSense hardware (Netgate 1100), and AD/
BloodHound placement.

### ESXi Daily-Driver Account
- Confirmed the rebuilt EoM ESXi host is reachable at an IP in the
  `192.168.245.x` range (DHCP-assigned post-reinstall) — distinct from
  the old static `192.168.4.40` ("Lionsgate") used pre-wipe.
- Logged in as `root` (password recovered — matched the iDRAC `root`
  credential, consistent with the credential-reuse issue flagged in
  Session 8).
- Created a new non-root local ESXi user via **Manage → Security &
  Users → Users → Add user**, with shell/SSH access enabled at creation
  time (checkbox option present in this ESXi version's "Add user" flow).
- Assigned the new account **Administrator** role at the host level
  (via Manage → Security & Users → Permissions → Add — exact tab/path
  may vary by ESXi build; Tim located it under "Roles"/user-level
  assignment in this version's UI).
- Decision: full Administrator rights for this single daily-driver
  account were judged acceptable for this lab context (single operator,
  no separation-of-duties need), rather than building a more
  least-privilege-scoped role. `root` is reserved for break-glass use
  only going forward, per the Session 8 lesson learned.
- **Backlog item closed:** "Create dedicated ESXi admin user account."

### pfSense ISO Acquisition
- Downloaded pfSense **CE (Community Edition), AMD64** architecture
  from pfsense.org/download (AMD64 is the standard 64-bit x86
  architecture designation, not AMD-specific — covers both AMD and
  Intel CPUs).
- Uploaded to `datastore1` via Host Client (Storage → datastore1 →
  Datastore browser → Upload). Uploaded twice by accident — duplicate
  ISO left in datastore, flagged for later cleanup, no functional impact.

### Rogal_Dorn VM — Created
- **Virtual Machines → Create/Register VM → Create a new virtual
  machine**
- Name: `Rogal_Dorn`
- Guest OS family: Other — Guest OS version: FreeBSD (closest match
  available; current pfSense CE 2.7.x is based on FreeBSD 14, exact
  FreeBSD 14 option may not have been listed in the dropdown)
- Compatibility: **ESXi 8.0 U2 virtual machine** (the available option
  in this ESXi 8.0U3e host's create-VM dropdown; fully compatible with
  the U3e host)
- Memory type: Standard (not Persistent Memory/PMem — PMem is for
  specialized NVDIMM hardware, not applicable here)
- **Virtual hardware:**
  - 2 vCPU
  - 2 GB RAM
  - 20 GB thin-provisioned disk
  - Default SCSI controller
  - CD/DVD Drive: Datastore ISO file → pfSense CE AMD64 ISO on
    `datastore1`
  - **3 network adapters** (all initially defaulted to "VM Network" on
    creation)

### Networking — vSwitch and Port Groups Rebuilt
- Confirmed EoM's `vSwitch0` has two default port groups:
  - **Management Network** — ESXi host management traffic only (what
    the Host Client itself is reached through)
  - **VM Network** — default VM-facing port group, shares the same
    physical uplink (`vmnic0` → Eero) as Management Network, but is
    logically separate and is the correct port group for VM traffic
    needing external connectivity
- Created new internal vSwitch: **`vSwitch-palace`** — no physical
  uplink (internal-only, VM-to-VM traffic exclusively; cannot reach the
  physical network or internet directly).
- Created two VLAN-tagged port groups on `vSwitch-palace`:
  - **`PG-Guilliman`** — VLAN ID 20 — for the Wazuh VM once migrated to
    EoM
  - **`PG-Valdor`** — VLAN ID 30 — for the planned Security Onion VM
    (named Valdor, see below)
- **Decision:** Guilliman and Valdor (Security Onion) will NOT share a
  VLAN. Discussed pros/cons of shared vs. per-appliance VLANs for
  security tooling specifically — concluded that even though both are
  trusted, single-operator-controlled defensive tools, segmenting them
  limits blast radius if either is ever compromised (a documented
  general security-architecture rationale for treating security tooling
  as a high-value target), and demonstrates the stronger-practice
  pattern relevant to Tim's advisory work. Decided in favor of
  separation despite the added complexity, with Rogal_Dorn explicitly
  prioritized to get built and working first.
- **Rogal_Dorn NIC assignments finalized:**
  - NIC 1 (WAN) → `VM Network` (internet/Eero-facing; WireGuard will
    listen here once configured)
  - NIC 2 → `PG-Guilliman` (VLAN 20)
  - NIC 3 → `PG-Valdor` (VLAN 30)
- Explicitly decided **not** to build `PG-VLAN10` (originally planned
  for generic "lab client" VMs) at this time, since none of the three
  currently-planned EoM VMs (Rogal_Dorn, Guilliman, Valdor) are client
  machines. Revisit if/when a client-type VM (e.g., the planned AD DC)
  is placed on EoM.

### Security Onion VM — Named, Not Yet Built
- Decided Security Onion will be the third planned EoM appliance.
- Confirmed (recalling Session 7 notes) that Security Onion bundles
  Suricata and Zeek internally — no separate standalone Suricata
  install needed if Security Onion is deployed.
- **Named: Valdor** (Constantin Valdor, Captain-General of the Adeptus
  Custodes — thematically fits a network-security-monitoring platform
  that watches over the network the way Valdor watches over the
  Emperor). VM not yet built — full Standalone hardware spec (24GB+
  RAM, 4+ CPU, 200GB+ storage) still applies per the original Session 7
  sizing notes.

### Architectural Concepts Clarified This Session
- **vSwitch vs. router:** a vSwitch is Layer 2 only (switching, no
  routing/IP awareness) — Rogal_Dorn (pfSense) is the actual router,
  with a leg in multiple vSwitch/port-group segments at once to bridge
  and firewall between them. ESXi has no native "vRouter" object;
  routing is always done by a VM (here, pfSense) plugged into multiple
  networks.
- **vmnic naming:** `vmnic0`, `vmnic1`, etc. refer to **physical** NICs
  on the R640 as seen from within ESXi — not virtual adapters, despite
  the "vm" prefix. The actually-virtual adapter is the VM's own network
  adapter/vNIC, configured per-VM.
- **VM Network vs. Management Network:** both are port groups on the
  same `vSwitch0`/physical uplink, logically separated for traffic-type
  clarity (host management vs. VM traffic), not separate physical paths
  in this single-NIC-uplink setup.
- **vCenter / vMotion / Distributed vSwitch dependency chain:** vCenter
  is required for both vMotion (live VM migration between hosts) and
  Distributed vSwitches (a vSwitch construct that spans multiple ESXi
  hosts). None of these apply to Tim's current single-host, no-vCenter
  EoM setup. A Standard vSwitch (what EoM uses) is host-local only and
  does not span hosts.
- **Internal vs. external traffic paths confirmed:** VM-to-VM traffic
  between two internal VLANs (e.g., Guilliman ↔ Valdor) stays entirely
  within ESXi, routed only through Rogal_Dorn's internal NICs — it never
  touches `vmnic0`. Only traffic actually entering/leaving EoM's network
  (e.g., internet access, the inbound WireGuard tunnel from VS) uses
  `vmnic0`.
- **Lateral movement / segmentation rationale discussed:** VLAN
  segmentation behind a routing/firewalling chokepoint (Rogal_Dorn) is
  the mitigation for uncontrolled lateral movement, not an instance of
  it — traffic between VLANs must pass through and can be inspected/
  filtered by pfSense, unlike a flat unsegmented network.

### Other Decisions Made This Session
- **EC2 WireGuard relay** — discussed in depth as a way to solve the
  "no inbound access while away from home" chicken-and-egg problem
  (both VS and Rogal_Dorn would dial outbound to a small EC2 instance
  acting as a relay, avoiding any need for port-forwarding on the
  Eero). Real pros: solves the lockout problem permanently, cheap
  ($0–5/mo), adds genuine cloud/AWS security-engineering reps. Real
  cons: third box to patch/maintain/pay for, becomes an internet-facing
  entry point if misconfigured, added WireGuard routing complexity
  (3-peer relay vs. 2-peer direct). **Decision: explicitly deferred**
  until the core on-prem lab (Rogal_Dorn, direct WireGuard, Guilliman
  migration, AD/BloodHound) is stable and working well.
- **Dedicated pfSense hardware (Netgate appliances)** researched via
  Netgate's product page. **Netgate 1100** ($269) selected as the
  appliance of interest: dual-core ARM Cortex-A53 1.2GHz, 1GB DDR4 RAM,
  10.6GB eMMC storage, 3x GbE ports, ~3.48W idle power draw, native
  WireGuard/OpenVPN/IPsec support, 927 Mbps L3 forwarding / 607 Mbps
  firewall throughput / 247 Mbps IPsec VPN throughput per Netgate's
  published performance figures.
  - **Planned placement:** between the Eero and the existing office
    switch (Modem → Eero → Netgate 1100 → switch → EoM/VS), making the
    1100 the new network edge for both hosts rather than Rogal_Dorn
    running as a VM on EoM.
  - **Open items if/when pursued:** decide DHCP vs. static IP handling
    once the 1100 is in place; decide whether to decommission the
    Rogal_Dorn VM entirely or repurpose it as an internal-only VLAN
    router behind the 1100; note that VS would then also pass through
    the 1100 (acting as plain router/switch for VS, not enforcing
    pfSense rules on it specifically unless desired).
  - **Decision: this is a deferred/later-phase item**, not blocking the
    current Rogal_Dorn VM build. Tim explicitly chose to proceed with
    Rogal_Dorn as a VM on EoM now rather than wait for the hardware.
- **Reverse shell / reverse SSH tunnel** discussed as a potential
  WireGuard substitute — concluded reverse shells are one-shot,
  unencrypted attacker payloads with no persistence or multi-host
  routing, not viable infrastructure. Reverse SSH tunnels (`ssh -R`) are
  a legitimate persistent/encrypted alternative, but still require a
  publicly-reachable relay box (i.e., the same EC2 dependency as the
  WireGuard relay option) and are strictly less capable than WireGuard
  for routing whole subnets to multiple internal hosts at once. No
  change to the WireGuard-based plan as a result.
- **PIA (commercial VPN) clarified as unrelated** to home-network remote
  access — PIA uses WireGuard as a protocol but is an outbound-only
  privacy service with no relationship to Rogal_Dorn or EoM; using the
  same protocol does not create a tunnel between unrelated endpoints.
- **AD Domain Controller placement confirmed:** a new, separate Windows
  Server VM (not Isstvan_III, which is Windows 10 Pro and cannot run AD
  DS) will serve as the domain controller, built on **EoM** per Tim's
  stated preference for centralizing "heavy" infrastructure there.
  Isstvan_III will join the domain as a client for BloodHound testing
  purposes. Edition not yet chosen (Windows Server 2022 Evaluation
  suggested as a free option, not yet confirmed).
- **Lord_Commander_Guilliman (current VS instance) confirmed for
  decommission** once Guilliman is rebuilt fresh on EoM — no data on
  the VS instance considered worth preserving.

### VM Naming Corrections (carried into this session)
- Clarified current naming, per Tim: **Horus** = Kali Linux (attacker,
  on VS) — this is the VM that was *originally* going to be renamed to
  Isstvan III per Session 9/10 notes, but Tim's restated mapping this
  session keeps Horus as the Kali VM name. **Isstvan_III** = Win10
  target (on VS). **Lord_Commander_Guilliman** = Ubuntu/Wazuh (currently
  on VS, scheduled for migration/rebuild on EoM).
  - Note: this differs from the Session 10 log, which recorded a
    completed rename of the Win10 target VM from "Horus" to
    "Isstvan_III" (i.e., Horus and Isstvan_III were the same VM,
    renamed). Tim's description this session treats Horus and
    Isstvan_III as two distinct, separate VMs (Kali and Win10
    respectively). This discrepancy has not been independently
    verified or reconciled — flagged here rather than assumed; worth
    confirming actual current VM names/roles on VS directly next time
    they're accessible, rather than relying on changelog history alone.

### Open Items / Next Session
- [ ] Power on Rogal_Dorn and run the pfSense installer (partitioning,
      initial install)
- [ ] Initial pfSense interface assignment (WAN/LAN/OPT1 matching the
      three NICs and their port groups)
- [ ] Configure WireGuard on Rogal_Dorn once pfSense install is complete
- [ ] Delete duplicate pfSense ISO from datastore1
- [ ] Verify/reconcile actual current VM names and roles on VS (Horus /
      Isstvan_III discrepancy noted above)
- [ ] Build Valdor (Security Onion) VM once Rogal_Dorn is stable —
      full Standalone spec, on `PG-Valdor` (VLAN 30)
- [ ] Migrate/rebuild Guilliman onto EoM, on `PG-Guilliman` (VLAN 20)
- [ ] Re-point Isstvan_III's Wazuh agent to new EoM Guilliman IP after
      migration
- [ ] Decommission Lord_Commander_Guilliman on VS once EoM rebuild is
      confirmed working
- [ ] Stand up new Windows Server VM (AD DC) on EoM; join Isstvan_III to
      the domain; run BloodHound from EoM or Horus/Kali against it
- [ ] (Deferred, later phase) Evaluate Netgate 1100 as dedicated pfSense
      hardware, placed between Eero and office switch
- [ ] (Deferred, later phase) EC2 WireGuard relay for remote access when
      away from home with no port-forward path

      Caught a typo in my own draft (line 122 garbled a sentence) — here's the corrected changelog, printed in full:

---

## [2026-06-27] Session 11 (continued) — WireGuard Configured, CGNAT Discovered as Blocker

### Summary
Continued directly from the DNS troubleshooting earlier in Session 11. Built a Kali Linux VM (named **Alpharius**) on EoM specifically to get browser-based GUI access to pfSense (no other device had both network reachability to PG-Guilliman and a working browser). Used the GUI to fix Rogal_Dorn's DNS Resolver. Installed and configured the WireGuard package on Rogal_Dorn (tunnel named **Webway**), set up VS as a peer, configured port forwarding on the Eero, and added a missing WAN firewall rule — but the tunnel still failed to complete a handshake. Root cause identified: Tim's ISP connection is behind **Carrier-Grade NAT (CGNAT)** — the "public" IP visible from whatsmyip.com is not actually a real public IP, making direct inbound WireGuard connectivity to the home network structurally impossible without ISP cooperation, a relay, or IPv6.

### DNS Resolver Fix (Rogal_Dorn)
- Confirmed via direct testing from Rogal_Dorn's own shell that Unbound's default mode (querying root DNS servers directly) was failing with a network error, while direct queries to known public resolvers (8.8.8.8) succeeded.
- **Fix applied:** Services → DNS Resolver → enabled Forwarding Mode; System → General Setup → added DNS servers 8.8.8.8 and 1.1.1.1.
- Confirmed working via Guilliman's `nslookup google.com`.
- **Root cause not independently confirmed** — likely Eero intercepting root-server queries, but inferred, not verified.

### Alpharius VM — Built (Kali Linux, EoM)
- Built to solve a GUI-access gap (Guilliman had reachability, no browser; VS had a browser, no reachability).
- Installed via Kali installer ISO. Specs: 2 vCPU/4GB RAM/40GB disk, 1 NIC on PG-Guilliman.
- Named **Alpharius**. Tim noted **Omegon** as a good name for a possible future second box in this role.
- Open question: keep long-term or decommission once WireGuard works — deferred.

### WireGuard — Configured on Rogal_Dorn, Tunnel Fails to Establish
- Tunnel named **Webway**, address `10.10.10.1/24`. Had to separately enable "Enable WireGuard" under the global Settings tab — distinct from enabling the tunnel itself; flagged as a UI quirk.
- VS peer added: `10.10.10.2/32`, keepalive 25, public key manually retyped (no clipboard sharing between Alpharius's console and the physical Lenovo).
- VS client configured: address `10.10.10.2/24`, endpoint = home public IP:51820, allowed IPs `192.168.1.0/24`.
- Eero port forward: UDP 51820 → `192.168.4.248` — confirmed correctly targeted.
- Added missing WAN firewall rule (only default RFC1918/bogon blocks existed) — Pass, UDP, any source, WAN address, port 51820.
- **Result: still failed.** VS showed ~3 KiB sent, 0 received, no handshake.

### Root Cause Identified: CGNAT
- Ruled out first: WAN IP mismatch, double NAT, missing firewall rule (all checked/fixed, none resolved it).
- Confirmed via modem's own DOCSIS admin page (`192.168.100.1`): WAN/gateway IP reported as `10.34.65.1` / `10.34.64.1` — both private RFC 1918 addresses, not the public IP shown by whatsmyip.com.
- **Conclusion:** Tim's ISP connection sits behind Carrier-Grade NAT. No inbound connection of any kind can reach the home network directly, regardless of port-forwarding/firewall config — this is an ISP-level constraint, not a configuration bug.
- A canyouseeme.org test (TCP/51820) was attempted but is not a valid test for UDP-based WireGuard; its inconclusive result is not cited as supporting evidence. The DOCSIS modem page is the actual confirming evidence.

### Implications / Options Going Forward (undecided)
- **EC2/VPS relay** — previously deferred as a nice-to-have; now likely necessary, since CGNAT only blocks inbound, not outbound, connections.
- **ISP static/public IP add-on** — not yet checked if available.
- **IPv6** — not yet checked if available/passed through; would avoid the relay dependency entirely if viable.
- No option selected yet.

### Open Items / Next Session
- [ ] Decide CGNAT workaround: relay vs. ISP static IP vs. IPv6 (check IPv6 first)
- [ ] If relay: stand up EC2/VPS, configure VS + Rogal_Dorn as outbound peers
- [ ] Decide on keeping/decommissioning Alpharius
- [ ] Delete duplicate pfSense ISO from datastore1
- [ ] Reconcile Horus/Isstvan_III naming discrepancy
- [ ] Build Valdor (Security Onion) VM
- [ ] Install Wazuh on Guilliman (VM built, software not yet installed)
- [ ] Re-point Isstvan_III's Wazuh agent once Wazuh is running on EoM
- [ ] Decommission Lord_Commander_Guilliman on VS
- [ ] Stand up AD DC, join Isstvan_III, run BloodHound
- [ ] (Deferred) Evaluate Netgate 1100 hardware

## [2026-06-27] Session 11 (continued) — Eye_of_Terror EC2 Relay Built, Remote Access Working End-to-End

### Summary
Built a small EC2 instance (**Eye_of_Terror**) to serve as a WireGuard
relay, resolving the CGNAT blocker identified earlier in Session 11.
Reconfigured Rogal_Dorn and VS to dial outbound to the relay instead of
attempting a direct peer-to-peer connection. After several rounds of
troubleshooting (a misconfigured AWS security group, a peer entry
mistakenly pointed at its own public key instead of the relay's, a
missing pfSense interface assignment/firewall rule, and a missing IP
address on the resulting OPT2 interface), confirmed full end-to-end
connectivity: **VS → Eye_of_Terror → Rogal_Dorn → PG-Guilliman**. This
is the first working remote-access path into EoM from outside the home
network.

### Alternatives Considered Before Settling on EC2
- **Tailscale** researched as a no-VPS alternative (built on WireGuard,
  automatic NAT/CGNAT traversal via DERP relays). Confirmed via search
  that Tailscale is not directly interoperable with a standard WireGuard
  peer — it would require replacing the manually-configured WireGuard
  setup entirely with the Tailscale client/daemon on each host, not
  adding to it.
- **NordVPN / commercial consumer VPNs** confirmed not applicable —
  outbound-only privacy services with no mechanism for inbound tunnels
  into a home network, regardless of which protocol they use
  internally.
- **Decision:** proceeded with a self-hosted EC2 relay over Tailscale,
  citing preference for keeping WireGuard (already configured) and
  avoiding a third-party coordination/control-plane service for this
  specific use case, despite Tailscale being the lower-effort option.

### Eye_of_Terror — EC2 Instance Built
- **Instance type:** t3.micro (free-tier eligible), Ubuntu Server 26.04
  LTS, region us-east-2.
- **Named: Eye_of_Terror** (the Warp rift housing the Cadian Gate —
  fits a stable, always-open access point). The WireGuard tunnel itself
  was informally referred to as "the Warp" going forward, alongside its
  existing pfSense-side label of "Webway." Key pair named
  **Ritual_of_Astro_Navigation** (a Navigator rite for plotting warp
  travel coordinates — confirmed via search as a real, accurate lore
  reference, fitting the key's function of "finding the way through").
  Tim noted **Cadian_Gate** as a reserved name for a possible future
  second EC2 instance (a "defender box" concept, not yet built).
- **First launch attempt failed and was discarded:** the initial key
  pair's `.pem` file download silently failed (browser showed an
  incomplete `Unconfirmed####.crdownload` file, easily mistaken for a
  successful download). Since AWS only allows downloading a key pair's
  private key once, at creation, the orphaned key pair was unusable.
  Resolved by terminating the first instance, releasing its Elastic IP,
  and relaunching clean with a new key pair, confirming the `.pem`
  download completed fully before proceeding.
- **Final instance:** Elastic IP allocated and attached:
  **`[REDACTED-PUBLIC-IP — see local notes]`** (replacing the ephemeral default public IP).
- **Security group:** SSH (22) and Custom UDP (51820), both source
  0.0.0.0/0. Decided against IP-restricting SSH given Tim's home
  connection is behind CGNAT (the "public IP" visible to AWS would be
  the ISP's shared NAT gateway, not reliably Tim's alone, and subject to
  change) — relying on SSH key-only authentication as the actual
  security boundary instead.
  - **Mid-session incident:** while adding the UDP/51820 rule, the
    existing SSH rule was accidentally overwritten rather than added
    alongside it (clicked into the existing rule's edit view instead of
    "Add rule"), briefly locking out both SSH and EC2 Instance Connect
    access. Diagnosed by checking the security group's actual rule list
    directly rather than assuming the cause, and resolved by re-adding
    the SSH rule. Both rules confirmed present afterward.
- Connected via standard OpenSSH from Windows PowerShell (`ssh -i
  <path-to-pem> ubuntu@<IP>`) — decided against installing/using PuTTY,
  since OpenSSH ships natively with Windows 10/11, uses the `.pem` file
  directly with no `.ppk` conversion step, and supports the same
  `~/.ssh/config` "saved session" equivalent PuTTY offers via its GUI.

### WireGuard — Reconfigured as a 3-Peer Relay
- Installed WireGuard on Eye_of_Terror (`sudo apt install wireguard`),
  generated its own keypair, and configured `/etc/wireguard/wg0.conf`
  as the relay hub:
  - Interface address: `10.10.10.3/24`, listen port `51820`
  - Peer entries for Rogal_Dorn (`10.10.10.1/32`) and VS (`10.10.10.2/32`)
- Enabled IP forwarding at the OS level (`net.ipv4.ip_forward = 1`,
  persisted in `/etc/sysctl.conf`) — required for Eye_of_Terror to
  actually pass traffic between its two peers rather than just
  terminating its own tunnel traffic.
- **Reconfigured Rogal_Dorn's Webway peer entry** (previously pointed
  directly at VS) to instead peer with Eye_of_Terror:
  - Public Key: Eye_of_Terror's key
  - Endpoint: `[REDACTED-PUBLIC-IP — see local notes]:51820`
  - Allowed IPs: `10.10.10.0/24` (the full tunnel subnet, not a single
    `/32` — necessary so Rogal_Dorn routes anything in that subnet,
    including VS, through this one relay peer)
  - Persistent Keepalive: 25
- **Reconfigured VS's WireGuard client** similarly — peer changed to
  Eye_of_Terror, Endpoint `[REDACTED-PUBLIC-IP — see local notes]:51820`, Allowed IPs
  `10.10.10.0/24,192.168.1.0/24` (tunnel subnet plus PG-Guilliman, so VS
  can reach both the relay and Guilliman through it).
- **Removed the now-unnecessary Eero port-forward rule** (UDP 51820 →
  Rogal_Dorn's WAN IP) — no longer needed once the connection model
  flipped from inbound-to-home to outbound-from-home; confirmed this is
  simply dead config with no functional purpose under the new
  architecture, not something that needed to be replaced with a new
  target.

### Troubleshooting Sequence (in order encountered)
1. **No handshake at all, either peer.** Root cause: AWS security group
   was missing the UDP/51820 inbound rule entirely (only SSH had been
   added at instance launch, despite earlier discussion) — confirmed by
   checking the security group's actual rule list directly rather than
   assuming. Fixed by adding the rule (and accidentally overwriting SSH
   in the process, separately resolved above).
2. **VS ↔ Eye_of_Terror handshake succeeded; VS ↔ Rogal_Dorn still
   failed**, with Eye_of_Terror responding "Destination host
   unreachable" for the Rogal_Dorn tunnel IP. Root cause: Rogal_Dorn's
   peer entry was misconfigured with **its own public key** (ending
   `[REDACTED — see local notes]`) instead of Eye_of_Terror's public key (ending
   `[REDACTED — see local notes]`) — meaning pfSense had never actually been told to talk to
   Eye_of_Terror at all. Also had an incorrect Allowed IPs value
   (`10.10.10.2/32`, a leftover from the original VS-direct peer entry)
   instead of the correct `10.10.10.0/24`. Both corrected; handshakes
   then succeeded on both peers per `wg show` on Eye_of_Terror.
3. **Handshakes up on both peers, but pings from VS to `10.10.10.1` and
   `192.168.1.1` still timed out.** Root cause, identified in two parts:
   - The WireGuard tunnel had never been assigned as a proper pfSense
     interface (Interfaces → Assignments) — added as **OPT2**, renamed
     **WireGuard_Webway**, and enabled.
   - Even after assignment, traffic from OPT2 into LAN was still
     blocked — confirmed via firewall logs that **no blocks were
     logged on OPT2 itself** (ruling out the OPT2 pass rule as the
     issue) while Guilliman → Rogal_Dorn (LAN → tunnel direction) ping
     succeeded fine — isolating the problem specifically to the
     OPT2-into-LAN direction. Default LAN rules (anti-lockout, allow
     LAN-to-any) only cover traffic *sourced from* LAN, not traffic
     *arriving from* another interface destined to LAN — a distinct,
     separate rule was required.
   - **Final root cause:** the OPT2/WireGuard_Webway interface itself
     had no IPv4 address assigned at the interface-configuration level
     (Interfaces → WireGuard_Webway) — the `10.10.10.1/24` address had
     only been set within the WireGuard Tunnel's own Interface
     Configuration page, which is a separate setting from the actual
     OPT2 interface's IP assignment in pfSense. Without it, pfSense had
     no properly configured return path for traffic arriving via that
     interface. **Fix:** set IPv4 Configuration Type to Static, address
     `10.10.10.1/24`, Upstream Gateway: None (not needed for a
     point-to-point tunnel interface). This resolved the issue
     completely.
4. Along the way, also added a Pass rule on the OPT2 interface itself
   (Firewall → Rules → OPT2) allowing traffic through — confirmed not
   to have been the actual blocker once logs showed no OPT2-side blocks,
   but left in place as it's still necessary for OPT2 to pass traffic at
   all (a "default deny" interface with the correct IP but no rules
   would have re-introduced the original problem).

### Result — Confirmed Working
- Full path verified: `ping 10.10.10.1` (Rogal_Dorn tunnel IP) and
  `ping 192.168.1.1` (Rogal_Dorn LAN/PG-Guilliman) both succeed from VS,
  routed through Eye_of_Terror.
- This is the first working remote-access path into EoM from outside
  the home network, resolving the CGNAT blocker identified earlier in
  Session 11.

### Open Items / Next Session
- [ ] Expand VS's Allowed IPs to include `192.168.x.x` (PG-Valdor
      subnet) once Valdor (Security Onion) is built, so remote access
      covers that segment too
- [ ] Consider adding a Pre-Shared Key to the WireGuard peers for
      defense-in-depth (discussed, not configured this session)
- [ ] Decide whether to keep or decommission Alpharius now that VS can
      reach pfSense's GUI directly through the working tunnel
- [ ] Delete duplicate pfSense ISO from datastore1 (carried over)
- [ ] Reconcile Horus/Isstvan_III naming discrepancy (carried over)
- [ ] Build Valdor (Security Onion) VM (carried over)
- [ ] Install Wazuh software on the Guilliman VM (VM built and
      networked; Wazuh itself not yet installed)
- [ ] Re-point Isstvan_III's Wazuh agent to EoM's Guilliman once Wazuh
      is running there
- [ ] Decommission Lord_Commander_Guilliman on VS
- [ ] Stand up AD DC, join Isstvan_III, run BloodHound (carried over)
- [ ] (Deferred) Evaluate Netgate 1100 hardware (carried over) — note
      this would not eliminate the CGNAT problem on its own; the
      relay/Eye_of_Terror approach (or an ISP/IPv6 workaround, both
      confirmed unavailable this session) would still be needed
      regardless of which device terminates the tunnel at home
- [ ] Add Eye_of_Terror's `.pem` key file to Keeper as an attachment
      (currently stored locally under OneDrive sync only)
- [ ] Reserve **Cadian_Gate** as a name for a possible future second
      EC2 instance (defender-box concept, not yet scoped)

      ## [2026-06-29] Session 13 — Rogal_Dorn Rebuild, WireGuard Restored

### Summary
Rogal_Dorn was deleted and rebuilt from scratch using the Netgate
Installer v1.2 (pfSense CE 2.8.1). After a lengthy troubleshooting
process involving DHCP configuration, WireGuard package quirks, and
stale public keys on Eye_of_Terror, full end-to-end connectivity was
restored: VS → Eye_of_Terror → Rogal_Dorn → PG-Guilliman.

### Root Cause of Previous Session's Rogal_Dorn Failure
The original Rogal_Dorn failure (Sessions 11-12) was traced to:
1. **ESXi 4-NIC probe-order instability** — adding a 4th virtual NIC
   to Rogal_Dorn triggered a documented VMware behavior where NIC
   enumeration order becomes unstable past 3 NICs, disrupting existing
   interface assignments silently. Confirmed via forum documentation.
2. **isc-dhcpd failing to start** — a secondary issue that persisted
   through the instability; never fully resolved before the decision to
   rebuild.
3. **Decision:** rebuild Rogal_Dorn fresh rather than continue debugging
   a compromised state. **Lesson learned:** take a VM snapshot before
   any risky NIC/interface change.

### Netgate Installer vs. Legacy pfSense CE ISO
- The Netgate Installer v1.2 is Netgate's current unified installer,
  replacing the standalone pfSense CE ISO. It fetches packages over
  the internet and prompts for CE vs. Plus selection (CE is free, Plus
  requires a paid license).
- During install, the LAN interface configuration wizard pre-configures
  DHCP server settings (static IP, range) — a significant improvement
  over the old installer, which left this entirely to the GUI post-install.
- **Key issue:** the installer retained old `dhcpd.conf` from the
  previous datastore (stale `10.x.x.x` subnet declarations) despite
  being a fresh VM. Required manual editing of
  `/usr/local/etc/dhcpd.conf` to add the correct `192.168.1.0/24`
  subnet declaration.
- isc-dhcpd also required a manual `touch /var/db/dhcpd.leases` before
  it would start (lease database file missing on fresh install).
- **Note:** isc-dhcpd is EOL and will be removed in a future pfSense
  version. Kea is the recommended replacement (System → Advanced →
  Networking). Not yet migrated — deferred.

### pfSense 2.8.1 + WireGuard 0.2.9_6 Known Bug
- A confirmed Netgate forum bug report (April 2026) documents that
  pfSense 2.8.1 + WireGuard package 0.2.9_6 has an issue where
  encrypted WireGuard handshake packets reach pfSense and decrypt
  successfully, but decrypted client data packets never surface on the
  assigned tun_wg interface for routing. Same config worked on 2.7.2.
- This was investigated during troubleshooting but ultimately was NOT
  the root cause of Tim's connectivity failure — the actual cause was
  Eye_of_Terror still having Rogal_Dorn's old public key from the
  previous build (ending `2g=` instead of the new `zE=`). Once
  Eye_of_Terror's wg0.conf was updated and restarted, full connectivity
  was restored on 2.8.1 without downgrading.
- The known bug may still be relevant in other scenarios — flagged for
  awareness.

### WireGuard Interface Assignment — pfSense 2.8.1 Quirk
- `tun_wg0` does not automatically appear in Interfaces → Assignments
  dropdown. It is hidden in the "Available network ports" dropdown which
  defaults to showing `vmx2` — `tun_wg0` must be manually selected from
  that same dropdown before clicking Add. Not a bug, just a non-obvious
  UI behavior.
- Correct sequence confirmed for pfSense 2.8.1:
  1. VPN → WireGuard → Settings → Enable WireGuard → Save → Apply Changes
  2. Create tunnel
  3. Interfaces → Assignments → select `tun_wg0` from dropdown → Add
  4. Enable interface, set static IPv4 `10.10.10.1/24`
  5. Add firewall rule on the new interface (Pass, any/any)

### Other Issues Encountered This Session
- **"Keep Configuration" during WireGuard uninstall** caused stale
  config to persist across reinstalls — always uncheck this before
  removing the package.
- **IPv6/DHCPv6 conflict** — pfSense pre-enabled DHCPv6 and Router
  Advertisements on LAN, which blocked setting a static IPv4 on the
  interface. Fixed by disabling IPv6 entirely: System → Advanced →
  Networking → Disable IPv6.
- **PIA VPN on VS** — confirmed not a cause of WireGuard failures but
  worth disabling before testing tunnel connectivity, since an active
  commercial VPN client can interfere with custom WireGuard configs.

### Current Public Keys (as of this rebuild)
- **Eye_of_Terror**: `YQ0KMayBp9vc4dWoN/t2vp/Whl0iMIbMllWCa7vK4DI=`
- **VS**: `1LPIc3oLVj++TQdQoMYXN7uPwGBmt+vtHtaxPYkVnTY=`
- **Rogal_Dorn (new)**: `9wIVq1f2nQHTMyxBUjuyVOHb+uhBW4omit4OHBOkhzE=`

### Connectivity Confirmed
- VS → Eye_of_Terror → Rogal_Dorn (`ping 10.10.10.1`) ✓
- VS → Eye_of_Terror → Rogal_Dorn → PG-Guilliman (`ping 192.168.1.1`) ✓

### Open Items / Next Session
- [ ] Install Wazuh on Lord_Commander_Guilliman (VM exists, software not
      yet installed)
- [ ] Re-point Isstvan_III's Wazuh agent to Guilliman's EoM IP
      (192.168.1.100) once Wazuh is running
- [ ] Decommission Lord_Commander_Guilliman on VS
- [ ] Migrate/configure DHCP from isc-dhcpd to Kea (deferred)
- [ ] Build Valdor (Security Onion) on PG-Valdor (VLAN 30)
- [ ] Build Alpharius (Kali) on PG-Alpharius (VLAN 40) — requires
      trunking on existing interface, NOT a 4th NIC on Rogal_Dorn
- [ ] Stand up AD DC, join Isstvan_III, run BloodHound
- [ ] Add topology PNG to diagrams/ folder in git repo
- [ ] Add Eye_of_Terror .pem key to Keeper as attachment
- [ ] (Deferred) Netgate 1100 hardware evaluation

## [2026-07-05] Session 14 — Wazuh Installed, Full Pipeline Validated

### Summary
Installed Wazuh 4.14.5 on Lord_Commander_Guilliman (EoM). Re-pointed
Isstvan_III's Wazuh agent from the old VS-side Guilliman IP
(192.168.76.132) to the new EoM IP (192.168.1.100). Validated the full
detection pipeline end to end, including confirmed remote connectivity
via the WireGuard relay with no physical hardline.

### Wazuh Install — Lord_Commander_Guilliman
- Installed Wazuh 4.14.5 (current stable as of 2026-06-29) via the
  official all-in-one installer:
  ```bash
  curl -O https://packages.wazuh.com/4.14/wazuh-install.sh
  sudo bash ./wazuh-install.sh -a -i
  ```
- All three services confirmed running: wazuh-manager, wazuh-indexer,
  wazuh-dashboard
- Dashboard accessible at https://192.168.1.100
- Admin password reset via CLI (GUI blocks admin password changes —
  "admin is reserved"):
  ```bash
  sudo /usr/share/wazuh-indexer/plugins/opensearch-security/tools/wazuh-passwords-tool.sh -u admin -p <password>
  ```
- Credentials saved to Keeper

### Isstvan_III Agent Re-pointed
- Agent config had stale manager IP (192.168.76.132 — old VS Guilliman)
- Updated via PowerShell:
  ```powershell
  (Get-Content "C:\Program Files (x86)\ossec-agent\ossec.conf") -replace '192.168.76.132', '192.168.1.100' | Set-Content "C:\Program Files (x86)\ossec-agent\ossec.conf"
  Restart-Service WazuhSvc
  ```
- Agent registration confirmed in Guilliman's ossec.log:
  `wazuh-authd: INFO: Agent key generated for 'Isstvan_III'`
- Isstvan_III confirmed Active in agent list (ID: 001)

### Sysmon localfile block re-added to ossec.conf
- Added to C:\Program Files (x86)\ossec-agent\ossec.conf:
  ```xml
  <localfile>
    <location>Microsoft-Windows-Sysmon/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
  ```
- WazuhSvc restarted after change

### Detection Validated
- Test: `cmd.exe /c echo malware` from elevated PowerShell on Isstvan_III
- Alert confirmed in dashboard: rule 92004, T1059.003 (Windows Command
  Shell), Tactic: Execution
- Dashboard path: Threat Hunting → Events
- Query used: `agent.name: Isstvan_III AND data.win.system.eventID: 1`

### Remote Connectivity Confirmed
- Physical hardline disconnected from VS — WireGuard relay (Eye_of_Terror)
  maintained connectivity
- Ping to 192.168.1.100 (Guilliman) succeeded remotely
- Full path confirmed: Isstvan_III → Webway → Eye_of_Terror →
  Rogal_Dorn → Guilliman

### Snapshots Taken (known good state)
- Rogal_Dorn — pfSense configured, WireGuard working, DHCP serving
- Lord_Commander_Guilliman — Wazuh 4.14.5 installed, Isstvan_III active
- Isstvan_III — Wazuh agent pointing at 192.168.1.100, Sysmon
  configured, ossec.conf updated

### VS-side Guilliman Decommissioned
- Lord_Commander_Guilliman VM on VS deleted from disk — no longer needed
  now that EoM Guilliman is confirmed working

### Open Items
- [ ] VLAN trunking on vmx2 for PG-Alpharius (VLAN 40) — requires
      dedicated session, no 4th NIC on Rogal_Dorn
- [ ] Build Valdor (Security Onion) on PG-Valdor (VLAN 30)
- [ ] Stand up AD DC, join Isstvan_III, run BloodHound
- [ ] Migrate DHCP from isc-dhcpd to Kea (deferred)
- [ ] Add topology PNG to diagrams/ in git repo

## [2026-07-05] Session 15 — Network Restructure, Security Onion Install in Progress

### Summary
Renamed port groups to match lore conventions, restructured network
addressing to use static IPs throughout, diagnosed and fixed multiple
Layer 2 connectivity issues, and successfully started Security Onion
3.1.0 installation on Valdor. Install was still in progress (downloading
/upgrading packages) at session end.

### Port Group Renames
- `PG-Guilliman` → `PG-Ultramarines` (VLAN 20, 192.168.1.0/24)
- `PG-Valdor` → `PG-Custodes` (VLAN 30, 192.168.2.0/24)
- Naming convention established: port groups named after legions,
  VMs named after primarchs/characters

### New VMs Planned
- **Calth** — victim VM on PG-Ultramarines
- **Hive_Primus** — victim VM on PG-Custodes
- **Valdor** — Security Onion (Constantin_Valdor), on PG-Custodes (management)
  and PG-Ultramarines (sniffing NIC)

### Rogal_Dorn — OPT2 (Custodes) Configured
- vmx2 assigned as OPT2 → interface renamed `Custodes` in pfSense
- Static IP: `192.168.2.1/24`
- DHCP server enabled on Custodes: range `192.168.2.100`-`192.168.2.200`
- Firewall rule added: Pass IPv4 Any/Any on Custodes interface
- **Key issue discovered:** vmx2's "Connected" checkbox in ESXi was
  unchecked, causing "no carrier" on the Custodes interface. This
  silently broke all Layer 2 connectivity on PG-Custodes. Fixed by
  re-checking "Connected" in Rogal_Dorn's VM settings.

### Static IP Migration (away from DHCP on LAN)
- DHCP disabled on LAN (PG-Ultramarines) — all VMs now use static IPs
- **Lord_Commander_Guilliman:** static `192.168.1.100/24` via netplan
- **Alpharius:** two NICs
  - eth0 → PG-Ultramarines: `192.168.1.101/24`, gateway `192.168.1.1`
  - eth1 → PG-Custodes: `192.168.2.101/24`, no gateway (Ultramarines
    owns the default route)
  - Configured via nm-connection-editor (Kali uses NetworkManager, not
    netplan)
  - Key lesson: both NICs having a gateway creates competing default
    routes — only the primary segment's NIC should have a gateway set

### Alpharius — Second NIC Added
- Added second NIC to Alpharius connected to PG-Custodes (eth1,
  192.168.2.101/24) giving it visibility into both segments

### Constantin_Valdor (Security Onion VM) — Setup
- VM specs: 4 vCPU, 24GB RAM, 200GB disk
- Two NICs:
  - NIC 1 → PG-Custodes (management, ens34) — `192.168.2.10/24`
  - NIC 2 → PG-Ultramarines (sniffing, ens37) — no IP
- Hostname: `valdor`
- **SO installer error resolved:** "The IP being routed by Linux is not
  the IP address assigned to the management interface" — caused by ens37
  (sniffing NIC) acquiring a DHCP lease on PG-Ultramarines and creating
  a conflicting default route. Fixed by disabling DHCP on LAN entirely,
  so ens37 gets no IP.
- **Install command:** `sudo /home/valdor/SecurityOnion/setup/so-setup iso`
- **Access range entered:** `192.168.0.0/16`
- Status at session end: downloading/upgrading packages — install in
  progress

### Key Lessons Learned
- ESXi "Connected" checkbox on a VM NIC can be silently unchecked,
  causing "no carrier" on a pfSense interface with no obvious error
  in the pfSense GUI — always verify in Host Client if an interface
  shows no carrier despite appearing configured
- Security Onion requires the sniffing NIC to have NO IP address —
  if it gets a DHCP lease, a conflicting default route is created
  and the installer fails with a routing error
- Kali Linux uses NetworkManager (nmcli/nm-connection-editor), not
  netplan — Ubuntu uses netplan
- When a VM has two NICs on different subnets, only one should have
  a default gateway set to avoid routing conflicts

### Open Items
- [ ] Complete Security Onion install on Valdor (in progress)
- [ ] Verify SO dashboard accessible at https://192.168.2.10
- [ ] Build Calth (victim VM, PG-Ultramarines)
- [ ] Build Hive_Primus (victim VM, PG-Custodes)
- [ ] VLAN trunking for additional segments (deferred)
- [ ] AD DC + BloodHound (deferred)
- [ ] Update topology PNG in diagrams/

## [2026-07-12] Session 16 — iPhone WireGuard, SO Access, Victim VM Planning

### Summary
Added iPhone as a WireGuard peer, resolved Security Onion dashboard
access (403 errors), covered VM file management fundamentals, and
planned victim VM architecture for PG-Custodes and PG-Ultramarines.

### iPhone WireGuard Peer Added
- iOS WireGuard app configured as a new Webway peer
- Tunnel IP: 10.10.10.4/24
- Public key: Tcy0Db4iUpHWtcGY90bY+hKYiBDGI+seVVNkGFyArB8=
- Added as permanent peer on Eye_of_Terror via:
  ```bash
  sudo wg set wg0 peer Tcy0Db4iUpHWtcGY90bY+hKYiBDGI+seVVNkGFyArB8= allowed-ips 10.10.10.4/32
  ```
- Good handshake confirmed
- SO dashboard accessible from iPhone after so-firewall update

### PG-Custodes Added to VS and iPhone AllowedIPs
- Updated VS WireGuard client peer AllowedIPs:
  ```
  10.10.10.0/24, 192.168.1.0/24, 192.168.2.0/24
  ```
- Updated Eye_of_Terror wg0.conf Rogal_Dorn peer AllowedIPs:
  ```
  10.10.10.1/32, 192.168.1.0/24, 192.168.2.0/24
  ```
- VS confirmed pinging 192.168.2.1 and 192.168.2.10

### Security Onion Dashboard Access Resolved
- Initial install set access to only `192.168.2.10` (Valdor's own IP)
- VS (10.10.10.2), Alpharius (192.168.1.101, 192.168.2.101), and iPhone
  (10.10.10.4) all added via:
  ```bash
  sudo so-firewall includehost analyst <IP>
  sudo so-firewall apply
  ```
- Dashboard confirmed accessible from VS, Alpharius, and iPhone at
  https://192.168.2.10

### VM File Management — Key Lessons
- VM files (config .vmx, virtual disk .vmdk, snapshots, logs) are stored
  in a folder per VM at a chosen location
- On VMware Workstation (VS): default path is chosen during wizard,
  typically Documents\Virtual Machines\<VM name>
- On ESXi (EoM): all VMs stored in datastore1 on the R640's RAID 10
  array, managed by ESXi Host Client
- Moving a VM safely: either use VMware Workstation's built-in Move
  function, or move the folder manually then File → Open the .vmx at
  its new location
- Never move individual files within a VM folder separately from the .vmx
- Never store VM files in OneDrive-synced folders (known issue from 2025)
- Horus successfully relocated from Machine_Spirits\ to
  Machine_Spirits\Horus\ using the manual move + re-open approach

### Victim VM Architecture Planned
Naming convention confirmed: port groups named after legions, VMs after
characters/locations. Snapshots to be taken enterprise-wide before any
attack exercises begin.

**PG-Ultramarines (192.168.1.0/24):**
- Calth — Linux victim VM (Metasploitable 3 Ubuntu 14.04), planned

**PG-Custodes (192.168.2.0/24):**
- Hive_Primus — Windows victim VM (Metasploitable 3 Win2008 R2), planned
- TBD name — Linux victim VM (Metasploitable 3 Ubuntu 14.04), planned

**Attack flow envisioned:**
- Horus attacks victims across both segments via Webway
- Lateral movement between segments (Custodes → Ultramarines) is
  deliberately possible for realistic kill chain exercises
- Valdor (Security Onion) monitors network traffic on PG-Ultramarines
  (sniffing NIC, ens37, no IP)
- Guilliman (Wazuh) catches host-based telemetry from agents
- Snapshots on all VMs = reset button after each exercise

### Metasploitable 3 Research
- Windows Server 2008 R2 version: no pre-built OVA exists due to
  Microsoft licensing restrictions — must be built via Vagrant + Packer
  (downloads Windows evaluation copy from Microsoft during build)
- Ubuntu 14.04 version: pre-built OVA available on SourceForge
- Vagrant current support status: to be confirmed next session
- Decision deferred: evaluating Vagrant + VirtualBox build vs.
  custom Windows Server victim vs. OVA-based Linux victim

### Open Items
- [ ] Confirm Vagrant support/EOL status before committing to that path
- [ ] Build Hive_Primus (Windows victim, PG-Custodes)
- [ ] Build Linux victim on PG-Custodes (name TBD)
- [ ] Build Calth (Linux victim, PG-Ultramarines) — deferred
- [ ] Add iPhone peer permanently to Eye_of_Terror wg0.conf
- [ ] Update SENSITIVE_LOCAL_ONLY.txt with iPhone public key
- [ ] Enterprise-wide snapshots before attack exercises
- [ ] Update topology PNG in diagrams/
- [ ] Full README update (deferred)
- [ ] Terraform setup for multi-VM provisioning (future session)
---

## [2026-07-25] Session 17 — Eye_of_Terror Logging, Docker Host Build, Vulhub

### Summary
Closed out host-level Wazuh logging on Eye_of_Terror, made final decisions
on victim VM architecture (Docker/Vulhub for Linux, full VMs for Windows —
no container path exists for Windows), built and provisioned the first
Docker host (`Hive_Secundus`), and cloned Vulhub. Also updated the topology
diagram and README.

### Eye_of_Terror — Wazuh Agent Renamed
- Agent had auto-registered under its AWS hostname (`ip-172-31-37-109`)
  instead of a readable name
- **Key lesson confirmed:** Wazuh does not support renaming an agent in
  place, via CLI or GUI — the only supported path is remove + re-register
- Removed via `manage_agents` (R, agent ID 002) on Guilliman
- Re-registered from Eye_of_Terror with explicit name:
  ```bash
  sudo systemctl stop wazuh-agent
  sudo /var/ossec/bin/agent-auth -m 192.168.1.100 -A Eye_of_Terror
  sudo systemctl start wazuh-agent
  ```
- Confirmed showing as `Eye_of_Terror`, Active, in Guilliman's dashboard

### Eye_of_Terror — Host Log Sources Added
- Added to `/var/ossec/etc/ossec.conf` (alongside existing default
  `<localfile>` blocks, including default `journald` coverage already
  present):
  ```xml
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/syslog</location>
  </localfile>
  ```
- Restarted agent, confirmed `active (running)`, all subprocesses up
- **Validated end-to-end:** deliberate failed SSH login
  (`ssh nonexistentuser@<Eye_of_Terror IP>`) confirmed visible in
  Guilliman's dashboard within ~30-60s
- **Deferred (not implemented):** WireGuard handshake-polling script
  (peer liveness monitoring) and iptables drop logging — judged
  non-standard/high-effort relative to value right now; revisit after
  the range is further built out. Rationale: Wazuh's rule engine
  reacts to events as they arrive, it doesn't natively evaluate log
  timestamp age, so alerting on stale handshakes would require the
  polling script itself to calculate staleness and emit a distinctly
  matchable log line — real but nontrivial custom logic.

### Victim VM Architecture — Decisions Finalized
- **Linux targets:** Docker + Vulhub on a dedicated Ubuntu Server host,
  **default bridge networking** (not macvlan) — containers differentiated
  by port on the host's single IP, not by distinct per-container IPs
  - Reasoning: macvlan requires ESXi's Forged Transmits vSwitch policy
    to be set to Accept (unconfirmed/untested); bridge mode sidesteps
    that entirely and was judged sufficient for CVE-specific
    exploit-and-detect exercises given time/resources aren't the binding
    constraint
  - 1:many reverse-proxy routing (nginx/Traefik, hostname-based instead
    of port-based) identified as a future upgrade path, not needed now
- **Windows targets:** confirmed no container path exists — Vulhub/Docker
  only support Linux containers (x86 only, no ARM). Windows Server and
  Windows Desktop targets require full VMs, no shortcut
- **Windows Server 2008 R2 (original Metasploitable3 Windows target)
  sourcing dead-ended:**
  - Microsoft's official evaluation download for 2008 R2 x64 (id=11093)
    now redirects to the Itanium-only page (id=22077) — x64 evaluation
    has been pulled from Microsoft's site entirely
  - Only remaining source is unofficial Internet Archive re-uploads —
    rejected in favor of pivoting to a modern Windows Server version
- **Pivoted to modern Windows Server (2019/2022)** — both confirmed
  still live on Microsoft's official Evaluation Center, 180-day eval
  - Licensing/lifespan resolved: `slmgr /rearm` allows up to 6 resets of
    the 180-day evaluation clock without reinstalling or losing
    configuration — approx. 3 years total runway on a single install
  - Trade-off accepted deliberately: loses EternalBlue/MS17-010-specific
    practice, gains realistic modern attack surface (PrintNightmare,
    Zerologon, etc. — specific CVE choice deferred, judged premature/
    narrow-scoping to lock in one CVE before the VM even exists)
  - Still not yet built — remains an open item

### Docker Host VM Built — Hive_Secundus
- **Naming:** `Hive_Primus` (original name for the PG-Custodes Windows
  victim slot per the 2026-07-12 plan) reserved for the future Windows
  Server target. New Docker/Linux host named **Hive_Secundus** instead.
- **Specs:** 2 vCPU, 4096 MB RAM, 40-60GB thin-provisioned disk, network
  adapter on PG-Custodes port group
- **OS:** Ubuntu Server 26.04 LTS (standard install, not minimized —
  deliberate choice to keep full default tooling available)
- Installer offered **Ubuntu Server** vs **Ubuntu Server (minimized)** —
  went with standard
- **Network — DHCP anomaly flagged:** installer auto-assigned
  `192.168.2.104/24` via DHCP despite PG-Custodes being documented as
  DHCP-disabled/static-only. Switched to manual/static configuration
  as planned, but the underlying cause (DHCP apparently active on
  PG-Custodes) was not investigated this session — **open item to
  check Rogal_Dorn's DHCP config on PG-Custodes**
- **Final static config:**
  - Address: `192.168.2.104/24`
  - Gateway: `192.168.2.1`
  - Interface: `ens34`
- Hostname: `hivesecundus`; username: `magus`
- OpenSSH server installed during setup
- Skipped all featured snaps (explicitly declined Docker-via-snap and
  microk8s) — Docker installed via official apt repo instead;
  microk8s judged out of scope (full orchestration platform, not
  needed for single-host manual `docker compose up/down` workflow)
- **Password note:** deliberately left as a weak/simple credential.
  Rationale discussed and accepted: PG-Custodes is not internet-facing
  (only Eye_of_Terror has a public IP), password-complexity practice
  has no offensive-skill training value once credential attacks are
  already understood, and the real training value of this range lives
  in exploitation + detection engineering, not in cracking the host's
  own login. Accepted risk: Alpharius (Kali) sits on the same segment,
  so a weak credential here is only safe under disciplined, deliberate
  targeting — not if broad/untargeted scans of PG-Custodes become part
  of future exercises.

### Docker Engine Installed (Official Repo Method)
Followed Docker's official Ubuntu install docs
(docs.docker.com/engine/install/ubuntu/) exactly:
```bash
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
- **Confirmed:** Docker's repo already has full support for Ubuntu 26.04's
  codename (`resolute`) — no fallback/pinning needed
- **Transient failure encountered:** first `docker run hello-world` pull
  failed with a DNS resolution error on
  `production.cloudfront.docker.com` (`no such host` via
  `127.0.0.53`). Diagnosed as transient, not a real config problem —
  `resolvectl status` confirmed correct DNS server (192.168.2.1),
  `nslookup` on the same domain succeeded moments later, and a retry of
  `docker run hello-world` completed successfully (image pulled, test
  container ran). Theory noted but unconfirmed: the domain resolves
  both A and AAAA records, and this host has no IPv6 configured — a
  first-attempt IPv6 lookup timeout could explain a one-off failure
  like this, but it wasn't proven, only worked around by retrying.
- **Docker Engine confirmed working** via successful `hello-world` run

### Vulhub Cloned
```bash
git clone https://github.com/vulhub/vulhub.git
cd vulhub
```
- Confirmed present: a folder for **CVE-2026-63030 / CVE-2026-60137
  ("wp2shell")** — the critical unauthenticated WordPress Core RCE
  chain disclosed 2026-07-17, actively exploited in the wild as of
  2026-07-18 through 2026-07-20. Not yet stood up — README review and
  `docker compose up` deferred to next session.

### Topology Diagram (`diagrams/empire_of_man_topology.drawio`) Updated
- Added confirmed OS/version detail: Rogal_Dorn ("pfSense,
  FreeBSD-based"), Guilliman ("Ubuntu Server 26.04 LTS", "Wazuh manager
  4.14.6" — corrected from previously recorded 4.14.5), Eye_of_Terror
  ("Ubuntu LTS")
- Added `whiteSpace=wrap;html=1;` to all node styles — text was
  overflowing box boundaries before this fix
- Increased vertical spacing throughout (VS → Eye_of_Terror → Rogal_Dorn
  → vSwitch-palace → PG segments → legend) — previously cramped, with
  vSwitch-palace nearly touching the PG segment containers
- Confirmed via local XML validation (`xml.etree.ElementTree`) after
  every edit — no malformed XML introduced

### README.md Updated
- Added new `## 🗺️ Topology` section referencing the diagram
- Fixed a recurring problem: embedding images via GitHub's
  `user-attachments` one-time upload links (created by pasting an
  image directly into the GitHub web editor) doesn't work for updates —
  those links are content-addressed and permanent, not reusable. Fixed
  by switching to a relative repo path (`diagrams/topology_<name>.png`)
  instead, so future diagram updates only require overwriting the PNG
  at that path, not re-editing the README
- Moved Security Onion from "Planned" to "Current Capabilities"; checked
  off the corresponding roadmap item; updated "Current Scope" to name
  both VLANs and Security Onion's role explicitly

### Key Lessons Learned
- Wazuh agent names cannot be changed once registered, on any Wazuh
  version, via CLI or GUI — remove and re-register is the only path
  (acceptable since a new agent has no meaningful log history to lose)
- Windows evaluation media sourcing degrades over time as Microsoft
  retires old evaluation download pages — don't assume an older OS
  eval ISO will remain officially available; verify before committing
  a build plan to it
- Windows Server evaluation `rearm` (up to 6 resets) provides ~3 years
  of runway on a single install without reinstalling — this fully
  resolves "the eval period is too short" concerns for a lab context
- Vulhub and Docker in general have zero Windows-container support —
  this is a hard architectural boundary, not a configuration gap to
  work around
- GitHub's `user-attachments` image links (from pasting an image into
  the web editor) are one-time/permanent — never reusable for updating
  a diagram in place. Always reference a real file path in the repo
  instead.
- A DHCP lease appearing on a segment documented as DHCP-disabled is
  worth investigating even if a workaround (manual static config) is
  applied in the moment — root cause not yet confirmed on PG-Custodes

### Open Items
- [ ] Investigate why PG-Custodes handed out a DHCP lease
      (`192.168.2.104`) despite being documented as DHCP-disabled
- [ ] Stand up wp2shell (CVE-2026-63030 / CVE-2026-60137) on
      Hive_Secundus via `docker compose up`, validate exploitation
- [ ] Extend Security Onion (Valdor) visibility to PG-Custodes — sniffing
      NIC currently only covers PG-Ultramarines; needs either a second
      sniffing interface on Valdor or a port-mirror/SPAN config on
      `vSwitch-palace`. Whether free-tier ESXi's vSwitch even supports
      port mirroring is unconfirmed.
- [ ] Configure Wazuh `docker-listener` wodule on Hive_Secundus (host
      level) to capture container lifecycle events; configure Docker
      logging driver or volume-mounted logs so Vulhub app-level logs
      (e.g. HTTP access logs for wp2shell) reach Wazuh/Suricata
- [ ] Build Windows Server VM (2019 or 2022 eval) on PG-Custodes —
      Hive_Primus name reserved for this
- [ ] Deferred: WireGuard handshake-polling script and iptables drop
      logging on Eye_of_Terror
- [ ] Deferred: Docker/Vulhub host provisioning automation (Packer +
      Ubuntu autoinstall) — judged worth revisiting only after seeing
      how the manual Hive_Secundus workflow plays out in practice
- [ ] Export and commit updated topology PNG; verify README image
      renders correctly on GitHub


# empire_of_man — Master Build Log & Changelog

This document consolidates the full project history: the original
2025 SOCaaS/MSSP-era infrastructure work (R640 + pfSense + Ubuntu) and the 2026 detection-engineering-focused rebuild). Cleaned up and de-duplicated from source notes — no content
removed, only reorganized and duplicate sections collapsed.

---

# PART 1 — 2025: Original STC-SOCaaS_v1 / Empire_of_Man Build (R640, pfSense)

## [2025-05-08] Phase 1 — ESXi Deployment + Lab Network Segmentation

### Hardware / Firmware
- Mounted Dell PowerEdge R640 into Vevor open-frame rack
- Service Tag: `[REDACTED — see local notes]`
- iDRAC9 configured via USB — static IP `192.168.4.120/24`, gateway `192.168.4.1`
- Firmware updated via iDRAC:
  - SAS-RAID: `SAS-RAID_Firmware_700GG_WN64_25.5.9.0001_A17_01`
  - iDRAC: `iDRAC-with-Lifecycle-Controller-Firmware_RVDDR_WN64_7.00.00.181_A00`
  - BIOS: `BIOS_J6D53_WN64_2.23.0`
- Created RAID 10 virtual disk across 4 drives using PERC H730P

### ESXi Install
- Installed VMware ESXi 8.0 Update 2 (Dell-custom ISO)
- ESXi host static IP: `192.168.4.40`
- Hostname: `Lionsgate` (https://Lionsgate/)
- DNS: Primary `8.8.8.8`, Alternate `1.1.1.1`
- Created secondary ESXi admin account: `custodian`
- Management network isolated using `vSwitch0` → `vmnic0` → Eero

### vSwitch-palace (Segmented Lab Virtual Switch)
- Created `vSwitch-palace` with no uplinks
- VLAN-tagged port groups created:
  - `PG-VLAN10` (vlan10) — Lab Clients
  - `PG-VLAN20` (vlan20) — Lab Servers
  - `PG-VLAN30` (vlan30) — DMZ
  - `PG-VLAN40` (vlan40) — Red Team
  - `PG-Custodes` (vlan100) — Admin / CustodianNet
- Promiscuous mode, MAC address changes, and forged transmits enabled on VLANs 10–40
- `PG-Custodes` deliberately left locked down (no promiscuous mode)

### pfSense Prep
- Downloaded pfSense CE AMD64 ISO from Netgate (pfsense.org/download)
- Used 7-Zip to extract the `.gz`-compressed installer ISO
- Deployed new VM `Rogal_Dorn` for pfSense
- Initially added 5 NICs (one per port group: VLAN10/20/30/40 + Custodes)
- Attempted interface assignment with `vmx0` (MAC `00:0c:29:40:2b:f8`) but hit installer limitations with this many NICs

---

## [2025-05-09] Rollback to Simplified Lab Core

- Removed unused NICs from `Rogal_Dorn` to simplify — full 5-NIC layout was unworkable at install time
- **Retained 3 NICs:**
  - NIC 1 → `PG-Custodes` (vlan100) → MAC `00:0c:29:40:2b:f8`
  - NIC 2 → `PG-VLAN10` (vlan10) → MAC `00:0c:29:40:2b:02`
  - NIC 3 → `VM Network` (default, vSwitch0) → MAC `00:0c:29:40:2b:0c`
- Rebuilt pfSense with a simplified two-NIC core layout:
  - **WAN** → VM Network (via vSwitch0), MAC `00:0c:29:40:2b:0c`
  - **LAN** → PG-VLAN10 (Lab Clients), MAC `00:0c:29:40:2b:02`
- Completed pfSense CE installation, reached initial configuration wizard
- Skipped Netgate cloud services, proceeded local-only
- Verified LAN connectivity to `192.168.1.1` from VLAN10

### Active Network Configuration (as of 2025-05-09)
**vSwitch0 (Management & WAN)**
- Connected to `vmnic0` (Eero LAN)
- Port groups: `VM Network` (active WAN for pfSense), `PG-WAN` (VLAN 60, reserved for future use)

**vSwitch-palace (Segmented Lab)**
- `PG-VLAN10` → vmx3 → MAC `00:0c:29:40:2b:02`
- `PG-Custodes` → vmx1 → MAC `00:0c:29:40:2b:f8`

### pfSense Interface Assignment (reference)
- WAN: vmx2, v4/DHCP4 → `192.168.4.187/22`
- LAN: vmx1 → `10.0.10.1/24`
- OPT1: vmx0
- Default credentials at this stage: `admin` / `[REDACTED — default pfSense credential, see password manager]`

### Execution Phase Roadmap (established 2025-05-09)
| Phase | Description |
|-------|-------------|
| 0 | Rack and power on server |
| 1 | Install VMware ESXi |
| 2 | Deploy pfSense with basic WAN/LAN setup |
| 3 | Build vSwitches and VLAN port groups |
| 4 | Deploy client/server/DMZ VMs |
| 5 | Deploy IDS and SIEM stack |
| 6 | Build Range Admin VM |
| 7 | Harden and test AWS jump server |
| 8 | Connect cloud jump box to lab |
| 9 | Monitor home network via SPAN |
| 10 | Begin threat emulation + detection testing |
| 11 | Deploy TheHive and Cortex for SOAR |

---

## [2025-05-12] Provisioning of Emperor_of_Mankind (SOCaaS Admin Node)

### Infrastructure Events
- Verified `pg-custodes` port group mapping in ESXi
- Diagnosed initial networking failure: `Rogal_Dorn` simply wasn't powered on
- Corrected VM network segmentation:
  - Reassigned one of `Rogal_Dorn`'s NICs from `pg-vlan10` to `pg-custodes`
  - Reassigned pfSense's LAN interface to this NIC, confirmed set to `10.0.10.1/24`
- Brought `Emperor_of_Mankind` online with static IP `10.0.10.10` via Netplan (modern route syntax)

### Ubuntu Workstation Stabilization
- Resolved black-screen issue post-install using `nomodeset` kernel parameter in GRUB
- Made `nomodeset` permanent for graphical session stability
- Installed `open-vm-tools` and `open-vm-tools-desktop` to restore clipboard/display integration

### Provisioning Script — `provision.sh`
Authored and executed full provisioning/baseline script:
- Updated system packages
- Installed essential tooling: `curl`, `git`, `zsh`, `ufw`, `fail2ban`
- Set hostname to `Emperor_of_Mankind`, updated `/etc/hosts`
- Created hardened admin user `malcador-the-sigillite`
- Disabled root SSH login and password-based auth
- Configured UFW to allow only SSH inbound
- Enabled `fail2ban` for brute-force protection
- Script logs its actions via `tee` to `~/Desktop/hardening_log.txt`

### SSH Key Setup Script — `setup_ssh_key.sh`
Companion script to install an SSH public key for `malcador-the-sigillite`:
- Creates `.ssh` directory
- Sets up `authorized_keys`
- Enforces correct permissions/ownership
- Commented for deferred/later use

### Knowledge Notes
- Ubuntu usernames must follow `NAME_REGEX`: lowercase letters, numbers, and dashes only
- `gateway4` is deprecated in Netplan; replaced by `routes: - to: default via: x.x.x.x`
- `nomodeset` disables GPU driver loading (avoids crashes) but also disables dynamic resolution

### Artifacts Created
- `provision.sh` — full provisioning and hardening script
- `setup_ssh_key.sh` — SSH key installation script for admin account
- `hardening_log.txt` — runtime log of provisioning actions

---

## Cumulative Update — [Through 2025-05-20]

### Infrastructure Changes
- Verified functional ESXi 8.0.2 installation on the R640
- Mounted and configured pfSense VM (`Rogal_Dorn`) with WAN/LAN:
  - WAN: `192.168.4.187` (via VM Network)
  - LAN: `10.0.10.1` (via `pg-custodes`)
- Configured and validated pfSense DHCP, firewall, and interface rules
- Successfully segmented LAN-side traffic via `vSwitch-palace` and `pg-custodes`
- Confirmed `Emperor_of_Mankind` has full IP and DNS reachability via pfSense

### Git & Documentation
- Reorganized GitHub repo (`Empire_of_Man`) with structure:
  - `configs/` (subfolders: Appliances, Networking, VMs)
  - `diagrams/` (`.drawio` and `.png` topology maps)
  - `playbooks/`, `Security/`, `logs/`, `dependencies/`
- Added README structural section describing all directories
- Wrote detailed `README.md` and `configs/README.md` for component tracking
- Created `COMPONENTS.md` and asset tables for: implemented VMs, software appliances, installed blue team tooling on the analyst workstation

### Strategic Decisions
- Chose **not** to route all home traffic through pfSense
- Retained Eero mesh as the primary home network routing layer
- pfSense scoped specifically for lab-side segmentation and future VLAN control only

### Detection & Visibility Direction
- Selected **agent-based telemetry** (Wazuh agents) over passive wire mirroring
- Deferred Security Onion deployment to a later phase
- Wazuh manager planned on an internal VM, agents deployed to `Emperor_of_Mankind` and future test systems / optional external clients
- Telemetry strategy designed to minimize infrastructure disruption

### Launch Automation
- Built PowerShell script `Launch-SOCaaS.ps1` to automate:
  - Opening the Git repo folder
  - Launching VS Code in project context
  - Opening ChatGPT in browser
  - Opening the ESXi host interface (`https://192.168.4.40`)
- Integrated Windows Text-to-Speech voice cue: *"All systems online, Archmagos. The Emperor protects."*
- Created `.vbs` wrapper (`Launch-SOCaaS.vbs`) to silently run the `.ps1` — later reverted in favor of running `.ps1` directly from desktop

### Miscellaneous & Support Tools
- Created draw.io network topology diagram for the environment
- Discussed router upgrade options; deferred Eero replacement
- Clarified port groups vs. VLANs in ESXi
- Validated pfSense routing between `vmx0` and `vmx1`
- Confirmed physical NIC → vSwitch → VM mappings on ESXi

### Status as of 2025-05-20
- Core components active: Dell R640, pfSense (`Rogal_Dorn`), Ubuntu Analyst Node (`Emperor_of_Mankind`)
- Git, VS Code, and workflow automation operational
- Lab telemetry-ready for Wazuh deployment
- System start script tested and functional

---

# PART 2 — 2026: Detection-Engineering Rebuild (Lenovo + R640)

> **Side quest begins here.** Roughly one year after Part 1, the ESXi
> license on the R640 had expired and the project pivoted: descoped from
> SOCaaS/MSSP ambitions to a focused skills-development lab for resume
> and interview material. Work resumed on a Lenovo laptop using VMware
> Workstation Pro before eventually returning to rebuild the R640
> properly later in the timeline.

## [2026-06-17] Session 1 — Pivot to Lenovo, Initial Build

### Session Summary
Pivoted from R640/ESXi (license expired, full rebuild required) to a
local VMware Workstation Pro lab on the Lenovo laptop. Descoped from
SOCaaS/MSSP ambitions to a focused skills-development lab: detection
engineering reps for resume/interview material. Stack simplified to bare
minimum: Wazuh + one Windows target running Atomic Red Team.

### Decisions Made
- **Project purpose re-scoped:** empire_of_man is for skills development
  and resume building, not a production MSSP. Revisit broader SOCaaS
  ambitions in 1+ year if still relevant.
- **R640 status:** ESXi license expired. Full hypervisor rebuild required
  (3-drive RAID, nothing of value to retain — OK to wipe). Deferred, not
  blocking current lab work.
- **Primary build platform:** Lenovo laptop (Windows 11 Pro, Intel Core
  Ultra 5 125U, 32GB RAM, VMware Workstation Pro) instead of R640.
- **Cloud/multi-tenant idea (Wazuh for friends' networks) — rejected.**
  Introduces data-at-rest, retention, and liability concerns that
  reintroduce the MSSP scope creep already deliberately avoided.
- **Splunk Attack Range** — confirmed still active (v5), but local
  deployment is deprecated by Splunk (Ludus recommended instead). Not
  pursued; going with Atomic Red Team locally instead.
- **VPN for remote lab access:** WireGuard recommended over PIA/OpenVPN/
  IPsec/Tailscale/ZeroTier for future remote access into R640/home
  network — lightweight, simple config, pairs well with pfSense
  (`Rogal_Dorn`).

### Minimum Viable Lab — Target Architecture
| VM | Purpose | Specs |
|----|---------|-------|
| Windows 10 Pro (target) | Atomic Red Team victim, Sysmon + Wazuh agent | 2 vCPU, 4GB RAM, 60GB disk, NAT |
| Wazuh (Ubuntu 22.04 Server) | SIEM/HIDS, single-node install | 2 vCPU, 4GB RAM, 50GB disk, NAT |

Planned install order: Wazuh agent → Sysmon (Olaf Hartong config) →
Atomic Red Team → run first technique → validate detection in dashboard.

### Build Progress
- **Windows 10 target VM created** in VMware Workstation Pro:
  - Custom config, UEFI (no Secure Boot — avoids blocking unsigned
    tools/test payloads), 2 vCPU / 1 socket, 4096MB RAM, NAT networking,
    LSI Logic SAS controller, 60GB virtual disk
  - Windows 10 Pro selected (avoided "N" edition)
  - Skipped product key (runs unactivated — cosmetic watermark only, no
    functional limitation for lab use)
  - Clean install ("Custom: Install Windows only")
  - Bypassed Microsoft account via **Offline account** option
  - **Local account created:** Username `horus` / Password `[REDACTED — see password manager]` /
    Security question answers: `[REDACTED — see password manager]`
- Ubuntu 22.04 Server ISO downloaded, queued for the Wazuh VM (not yet
  built as of end of session)

### Notes / Reminders
- Credentials above are for an isolated, NAT'd, non-internet-facing lab
  VM. Low risk as configured. Revisit before any network exposure
  changes.
- Backlog (deferred 1+ year, only if still aligned with goals): Security
  Onion, TheHive, Cortex, OT/ICS target, R640 rebuild/expansion, cloud
  Wazuh for external endpoints.

---

## [2026-06-18] Session 2 — Wazuh VM Build, Indexer Crash

### Summary
Built the Ubuntu Server VM for Wazuh, installed Wazuh single-node, and
confirmed VM-to-VM networking with horus. Hit a blocking issue with the
`wazuh-indexer` service failing after a host reboot; paused mid-
troubleshooting.

### VM Naming
- Wazuh/Ubuntu VM named **Guilliman** (Primarch of the Ultramarines —
  thematically fitting: order/codification, matches what a SIEM does to
  raw log data). Considered Alpharius first, swapped to Guilliman.
- Ultramarines Legion motto for reference: **"Courage and Honour"**
  (longer form: "Courage and honour until the end and past it").

### Ubuntu (Guilliman) Build Steps — v1
- Ubuntu Server 22.04 LTS, full install, DHCP-assigned, no proxy
- Hostname: `guilliman` / Username: `guilliman` / Password: `[REDACTED — see password manager]`
- OpenSSH server installed, password auth allowed
- No featured snaps installed
- **Guilliman IP:** `192.168.76.130` (NAT, broadcast `192.168.76.255`)
- Confirmed ping connectivity both directions with horus

### Wazuh Install
```bash
sudo apt update && sudo apt upgrade -y
curl -O https://packages.wazuh.com/4.9/wazuh-install.sh
sudo bash ./wazuh-install.sh -a -i
```
(`-a` = all-in-one manager+indexer+dashboard; `-i` = ignore OS
compatibility false-positive warning. Note: capital **-O**, not zero —
easy typo.)

Install completed initially; generated admin dashboard credentials
(retrievable via `sudo tar -O -xvf wazuh-install-files.tar wazuh-install-files/wazuh-passwords.txt`).

### Issues Encountered
1. **Clipboard friction on VM console** — couldn't copy/paste the
   generated password from the Ubuntu console into the host browser.
   **Resolution: SSH into Guilliman from a native terminal** instead of
   the VMware console — copy/paste works normally over SSH.
2. **Dashboard login rejected admin credentials** — likely manual
   transcription error given password complexity.
3. **Host VM reset attempted as a fix** — did not resolve the login
   issue, and left `wazuh-indexer` in a failed state on reboot.
4. **`wazuh-indexer` failing to start post-reboot:**
   `Active: failed (Result: exit-code)`, exit status 1.
   - `journalctl -u wazuh-indexer` returned no entries (journal rotated)
   - `wazuh-cluster.log` existed but appeared empty when checked
   - `wazuh-passwords-tool.sh` attempts: first failed ("backup could not
     be created"); second gave mixed result — keystore update succeeded,
     but tool reported `ERR: Seems there is no OpenSearch running on
     localhost` — consistent with indexer being down
   - **Not resolved this session** — paused before checking
     `wazuh-cluster_server.json`

### Lesson Learned
Use SSH from a native terminal for all VM administration going forward,
not the VMware console — avoids clipboard issues entirely.

---

## [2026-06-18] Session 3 — Root Cause Found: Underprovisioned Guilliman

### Root Cause Identified
`wazuh-indexer` was crash-looping because **Guilliman was
underprovisioned**. Original build: 2 vCPU / 4GB RAM / 50GB disk.
Verified against Wazuh's official quickstart hardware table: **minimum
for an all-in-one deployment (up to 25 agents, 90 days history) is 4
CPU, 8GB RAM, 50GB disk.** We were at half the required RAM/CPU —
consistent with the JVM/OpenSearch-based indexer dying on startup.

### Resolution
Deleted the original Guilliman VM entirely and rebuilt clean rather than
continuing to debug an underprovisioned instance. (Windows also flagged
a warning about saving multiple VMs to the same C:\ folder — gave
Guilliman its own dedicated VM folder this time.)

### New Guilliman VM Specs
- **4 vCPUs** (up from 2) / **8GB RAM** (up from 4GB) / **100GB disk**
  (up from 50GB, extra headroom for log retention/scaling)
- LSI Logic SAS controller, NAT networking, dedicated VM folder

### Ubuntu Rebuild
- Same as before: Ubuntu Server 22.04 LTS, username `guilliman` /
  password `[REDACTED — see password manager]`, OpenSSH + password auth, no snaps
- **New Guilliman IP:** `192.168.76.132/24`, broadcast `192.168.76.255`

---

## [2026-06-18] Session 4 — Wazuh Stable, Agent Deployed on Horus

### Wazuh Dashboard Access
- Clean reinstall on properly-sized Guilliman — all services
  (`wazuh-indexer`, `wazuh-manager`, `wazuh-dashboard`) came up
  active/running with no errors.
- Logged into dashboard at `https://192.168.76.132`.
- **Reset dashboard admin password** via SSH:
  ```
  sudo /usr/share/wazuh-indexer/plugins/opensearch-security/tools/wazuh-passwords-tool.sh -u admin -p [REDACTED — see password manager]
  ```
  - Username: `admin` / Password: `[REDACTED — see password manager]`

### Agent Deployment — UI Navigation Note
Wazuh 4.9 dashboard nav for deploying a new agent is **not** under
"Agents management" (older version's label). Correct path: **Server
Management → Endpoint Summary → Deploy new agent**.

### Deploying Wazuh Agent on Horus
- Selected **Windows**, server address did **not** auto-fill — entered
  manually: `192.168.76.132`
- Generated install command:
  ```powershell
  Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.9.2-1.msi -OutFile $env:tmp\wazuh-agent; msiexec.exe /i $env:tmp\wazuh-agent /q WAZUH_MANAGER='192.168.76.132' WAZUH_AGENT_NAME='Horus'
  ```
- **Blocker:** couldn't paste the command into the horus VM console.
  Root cause: **VMware Tools not installed** on horus (clipboard sharing
  requires Tools in-guest, not just the host-side "Enable copy and
  paste" setting, which was already checked but had no effect).
- **Resolution:** Installed VMware Tools on horus (VM menu → Install
  VMware Tools → run setup.exe from mounted virtual CD → reboot).

---

## [2026-06-18] Session 5 — Sysmon + First Detection Validation

### Summary
Resolved clipboard issue via VMware Tools, deployed Sysmon
(SwiftOnSecurity config), and validated the full pipeline end to end:
Sysmon → Wazuh agent → Guilliman manager → indexer → dashboard.

### Wazuh Agent — Completed
- Confirmed **Active** status in dashboard after starting the agent
  service on horus.

### Sysmon Install — SwiftOnSecurity Config
- Chose SwiftOnSecurity over Olaf Hartong (originally planned) —
  simpler, well-documented, good Wazuh decoder compatibility.
- **Gotcha:** first config download was the GitHub *webpage* (HTML), not
  raw XML — caused `Failed to load xml configuration (could not read
  file)`. Confirmed by opening in Notepad and seeing `<!DOCTYPE html>`.
  **Fix:** use the raw URL:
  `https://raw.githubusercontent.com/SwiftOnSecurity/sysmon-config/master/sysmonconfig-export.xml`
- Install command:
  ```powershell
  .\Sysmon64.exe -i "C:\Users\horus\Desktop\sysmonconfig-export.xml" -accepteula
  ```
- Confirmed: `Sysmon64 installed.` / `SysmonDrv started.` / `Sysmon64
  started.` Verified local logging via `Get-WinEvent -LogName
  "Microsoft-Windows-Sysmon/Operational"`.

### Detection Validation — EID 1 Test
- Test trigger: `cmd.exe /c echo malware`
- **Initial result:** confirmed locally in Sysmon's own log, but **not**
  appearing in Wazuh dashboard searches — `agent.name` alone returned
  other Windows logs (Application/Security/System), but Sysmon-specific
  events were absent.
- **Root cause:** the agent's `ossec.conf` had **no `<localfile>` block
  for the Sysmon channel at all.** Confirmed via `ossec.log` tail showing
  the agent only analyzing Application/Security/System.
- **Fix:** manually added to `C:\Program Files (x86)\ossec-agent\ossec.conf`
  (left existing System block untouched, added as a new entry):
  ```xml
  <localfile>
    <location>Microsoft-Windows-Sysmon/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
  ```
  Saved, then `Restart-Service -Name WazuhSvc`.
- Re-ran the test — **EID 1 event successfully appeared in the
  dashboard.** Full pipeline validated end to end.

### Dashboard Notes (UI navigation, v4.9)
- "Deploy new agent" lives under **Server Management → Endpoint
  Summary**.
- Useful search queries:
  ```
  agent.name: Horus
  agent.name: Horus AND data.win.system.eventID: 1
  ```

### Lessons Learned (Session 5)
- Always download configs from raw/direct file URLs, not repo landing
  pages.
- VMware Tools is a prerequisite for clipboard sharing, not just the
  host-side setting — install it early in any new VM build.
- A Wazuh agent does not automatically pick up new Windows Event Log
  channels just because the log source exists on the endpoint — the
  channel must be explicitly added as a `<localfile>` entry in
  `ossec.conf`, even if installed after the agent. Good to remember for
  any future custom log source (PowerShell Operational logs, additional
  ETW providers, etc.).

---

## [2026-06-19] Session 6 — First Validated Detection (Documented)

### Summary
Located and confirmed the first real detection fired by Wazuh's default
ruleset against the `echo malware` Sysmon EID 1 test event. No custom
rule needed — out-of-the-box ruleset correctly identified and
MITRE-mapped the activity.

### Detection Details
- **Trigger:** `cmd.exe /c echo malware` from an elevated PowerShell
  session on horus
- **rule.id:** `92004`
- **rule.description:** "Powershell process spawned Windows command
  shell instance"
- **rule.level:** 4 — **rule.groups:** `sysmon`,
  `sysmon_eid1_detections`, `windows`
- **MITRE mapping:** Technique T1059.003 (Windows Command Shell),
  Tactic: Execution
- **Decoder:** `windows_eventchannel` — **Sysmon EID:** 1 (Process
  Create)
- Key fields confirmed populated: `data.win.eventdata.commandLine`,
  `parentImage` (PowerShell), `image` (cmd.exe), `user`
  (DESKTOP-HTHPCAF\Horus), `hashes` (MD5/SHA256/IMPHASH)

### Dashboard Search Notes
- Correct field for Sysmon process command line:
  `data.win.eventdata.commandLine` (not `data.win.system.message`, which
  holds the full raw rendered text but isn't the structured field).
- Useful query to isolate Sysmon EID 1 specifically (avoids collision
  with Security log events also using `win.system.eventID`):
  ```
  agent.name: Horus AND data.win.system.eventID: 1 AND data.win.system.channel: "Microsoft-Windows-Sysmon/Operational"
  ```
- "Edit Filter" UI expects a single field/operator/value triple, not a
  full DSL string — for compound DSL queries, use the main search bar
  and save via the floppy-disk/save icon. Also: the Edit Filter field
  picker only shows fields already indexed in the index pattern's field
  list (Dashboard Management → Index Patterns → refresh fields icon) —
  a field can be real and fully searchable via DSL while not yet
  appearing there.
- **Saved Queries** feature discovered — preferred over Edit Filter for
  reusable DSL strings.

### Why This Matters (Resume/Interview Value)
Clean, complete detection-engineering narrative: generated a
benign-but-suspicious parent/child process relationship → confirmed
capture at the OS level → diagnosed and fixed a real pipeline gap →
located the resulting alert and read its structured fields → mapped to
the exact MITRE ATT&CK technique/tactic Wazuh's default ruleset already
assigns.

---

## [2026-06-19] Session 7 — Atomic Red Team, Network Detection Planning, Major Architecture Decision

### Atomic Red Team — Installed and First Technique Run
- Initial install via `Install-AtomicRedTeam -getAtomics` appeared to
  succeed but the atomics folder was never actually created —
  `Invoke-AtomicTest T1057` failed with `Resolve-Path` errors. Deleted
  `C:\AtomicRedTeam` and reinstalled clean with `-Force`:
  ```powershell
  IEX (IWR 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing)
  Install-AtomicRedTeam -getAtomics -Force
  ```
  Confirmed `Test-Path "C:\AtomicRedTeam\atomics"` returned `True`.
- Required `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope
  Process -Force` before atomics would run.
- **First real technique run: T1057 (Process Discovery)** — executed
  successfully via `Invoke-AtomicTest T1057`.

### Network/Server-Side Detection — Research & Planning
Discussed long-term goal: writing original detection rules for newly
disclosed CVEs (motivating example: **CVE-2026-10520**, a critical
CVSS 10.0 pre-auth OS command injection in Ivanti Sentry, added to CISA
KEV, public PoC available — confirmed via live web search). Concluded
this class of detection is primarily network/web-layer, not host-layer,
since the lab doesn't run a vulnerable Sentry instance.

**Key architectural clarifications reached this session:**
- **Wazuh is a log-based SIEM/HIDS, not a packet-inspecting NIDS.** No
  native packet sniffing/signature-matching. Can ingest Suricata's
  `eve.json` alerts as a log source (same `<localfile>` pattern as the
  Sysmon fix) — sensible correlation pattern, but Suricata has to do the
  actual detection first.
- **Suricata vs. Zeek:** Suricata = signature-based alerting (smoke
  detector). Zeek = behavioral/metadata logging of all traffic, built
  for retrospective threat hunting (security camera). Real deployments
  run both.
- **Security Onion** is an NSM platform, not strictly a SIEM, despite UI
  overlap. Confirmed current official minimums: Standalone needs **24GB
  RAM / 4 CPU / 200GB** minimum; a lighter **Eval** install type exists
  for homelab use, minimum **12GB RAM**, explicitly not for production
  (drops Logstash/Redis).

### Major Decision — Split Architecture (Lenovo vs. R640)
Walked through alternatives before converging:
- EC2 + VPN tunnel back to Lenovo — rejected: VPN provides routing, not
  traffic mirroring; EC2 Security Onion would only see EC2's own
  traffic.
- EC2 as a deliberately open ("wild") honeypot — real value
  acknowledged, but flagged cost/ToS exposure and incompatibility with
  clean purple-team ground truth if mixed with random internet noise.
- Kali (Lenovo) attacking an IP-locked EC2 target — clean but solves a
  problem the already-owned R640 solves for free.

**Final decision: split the lab across two physical hosts by role:**
- **Lenovo (mobile/disposable)** — attacker tooling, victim/target
  machines, traffic-generating sensors: Horus, future Kali VM, future
  additional targets. Rationale: portable, useful anywhere, keeps attack
  tooling separate from defensive infrastructure.
- **R640 (centralized/persistent)** — Guilliman (Wazuh), Rogal_Dorn
  (pfSense), Security Onion (full Standalone spec), revisit
  TheHive/Cortex later. Rationale: ample headroom (dual Xeon, 64–128GB)
  removes every resource constraint hit on the Lenovo so far.
- **Connectivity:** WireGuard VPN server on Rogal_Dorn for remote
  access — chosen because pfSense has it built in natively AND because
  **pfSense is commonly used by DoW Cyber Protection Teams** (direct
  career relevance, not just convenience).
- Enables a genuine purple-team workflow: Kali on the Lenovo connects
  via WireGuard into the home network and attacks targets/services on
  the R640, while Guilliman and Security Onion observe and alert — clean
  attacker/defender separation with real segmentation (PG-VLAN10,
  PG-Custodes) via Rogal_Dorn.

---

## [2026-06-19] Session 8 — R640 / ESXi Rebuild

### Summary
Successfully reinstalled ESXi 8.0U3e on the R640 via iDRAC virtual
media, after working through several iDRAC/virtual console issues.
Confirmed the host is licensed (free, no expiration) and accessible.
Old VMs (`Rogal_Dorn`, `Emperor_of_Mankind`, `Sanguinius`) and their
datastore contents were intentionally wiped — nothing of value retained,
per prior decision.

### Pre-Wipe Verification
- Single datastore (`datastore1`, non-SSD, 3.37TB capacity, ~98.5GB
  provisioned, VMFS6) — consistent with the 3-drive RAID array
  presenting as one logical volume, separate from whatever small device
  ESXi boots from.
- Confirmed three VMs registered (`Rogal_Dorn`, `Emperor_of_Mankind`,
  `Sanguinius`) — reviewed, deliberately not retained.

### iDRAC Access — Recovered From Notes
- iDRAC had never been physically connected to the network in this
  session's starting state (only the main ESXi NIC was cabled).
- **iDRAC IP recovered from prior personal notes:** `192.168.4.120`
  (matches the original 2025-05-08 configuration — could not be found
  via generic online guidance, only recoverable because previously
  documented).
- iDRAC firmware: `7.00.00.181` (iDRAC9-generation), matching the
  original 2025 firmware update record.
- Credentials retrieved from Keeper vault.

### ISO Acquisition
- Downloaded `VMware-VMvisor-Installer-8.0U3e-24677879.x86_64.iso`
  (618.34 MB / 648,374,272 bytes — verified against official published
  size) from the Broadcom Support Portal.
- **Confirmed via web search:** this specific build is the **Free
  Edition** with the license **embedded directly in the image** — no
  separate key needs to be requested or applied. (A visually similar
  "Evaluation/Paid" build exists under a different build number —
  `24674464` — which does require a separate key; `24677879` does not.)
- Confirmed post-install under Manage → Licensing: **vSphere 8
  Hypervisor, Key `[REDACTED — see password manager]`, Expiration: Never.**

### Boot/Install Troubleshooting (iDRAC Virtual Media)
Root causes, in order discovered:
1. **First download location was inside OneDrive** — moved to a local
   `C:\` path before mounting (cloud-sync placeholder files can cause
   virtual media mount issues).
2. **"Map Device" button was never actually clicked** in earlier
   attempts — the ISO appeared selected but was never truly attached,
   causing "Boot failed" when Virtual Optical Drive was selected.
3. **Stale/orphaned Virtual Media session** — console reported "Virtual
   Media is currently unavailable, a session is in use" with nothing
   visibly mounted anywhere in the UI. **Fix: reset iDRAC itself**
   (iDRAC Settings → Reset iDRAC) — a soft reset of the management
   controller only, does not affect server power state. Mapping
   succeeded cleanly afterward.
4. Confirmed boot mode (System Setup/F2 → System BIOS → Boot Settings)
   was already correctly set to **UEFI**, ruling out a mismatch.
- Successful path: iDRAC Virtual Console → Virtual Media → Connect
  Virtual Media → Map CD/DVD → browse to local ISO → **Map Device**
  (critical step) → reboot (Reset from iDRAC Power menu) → click into
  console for keyboard focus → **F11** during POST → One-shot UEFI Boot
  Menu → **Virtual Optical Drive**.

### Install
- Selected `datastore1` as install target, confirmed overwrite (nothing
  retained).
- Set a root password during install (later determined to likely match
  the existing iDRAC `root` password due to credential reuse — caused
  brief confusion post-install about which password applied to the
  Host Client login; resolved by trying the iDRAC credential, which
  worked).

### Current State
- ESXi 8.0U3e installed, licensed (free, no expiration), accessible via
  Host Client.
- Logged in as `root` (shared credential with iDRAC, by reuse rather
  than design).
- **Backlog item raised:** create a dedicated ESXi local admin account
  (Manage → Security & Users → Users) and reserve root for break-glass
  use only. Not yet done.

### Lessons Learned (Session 8)
- For Dell iDRAC virtual media installs, always explicitly click "Map
  Device" after browsing to the ISO — visual selection in a dialog is
  not the same as attachment.
- If virtual media shows a conflicting/stuck state ("session in use"
  with nothing visibly mounted), resetting iDRAC itself (not the
  server) is a safe, fast fix.
- Avoid mounting ISOs for virtual media directly from cloud-sync
  folders — move to a fully local path first.
- Verify the exact ISO build number, not just the version string —
  Broadcom publishes visually similar "Free Edition" vs.
  "Evaluation/Paid" ISOs for the same version under different build
  numbers; only one has the license embedded.
- Credential reuse across iDRAC and ESXi root can cause confusion
  later — use distinct passwords for distinct credential sets going
  forward, labeled clearly in the password manager (e.g., "ESXi root —
  Lions Gate" vs. "iDRAC — Lions Gate").

---

## Consolidated Open Items / Backlog (as of 2026-06-19)

### R640 (centralized/persistent infrastructure)
- [ ] Create dedicated ESXi admin user account (move off root for daily use)
- [ ] Rebuild Rogal_Dorn (pfSense) on the fresh ESXi host
- [ ] Configure WireGuard on Rogal_Dorn for remote access (DoW CPT tool familiarity)
- [ ] Rebuild/migrate Guilliman (Wazuh) to R640 — full spec, no resource constraints
- [ ] Build Security Onion on R640 (full Standalone spec: 24GB+ RAM, 4+ CPU, 200GB+ storage), segmented behind Rogal_Dorn
- [ ] Revisit TheHive/Cortex backlog (originally part of 2025 architecture)

### Lenovo (mobile/disposable infrastructure)
- [ ] Continue Atomic Red Team technique testing on Horus
- [ ] Build Kali VM (attacker role)
- [ ] Consider additional lightweight target VMs (Linux, vulnerable web app)

### Long-Term / Cross-Cutting
- [ ] Write an original Suricata detection rule for a real disclosed CVE and validate it against self-generated attack traffic from Kali
- [ ] Set up Git repo + VS Code for empire_of_man project tracking
- [ ] Draft `.gitignore` before any public-facing commit (credentials, sensitive configs)
- [ ] OT/ICS target VM (long-deferred backlog item, differentiator given Cal-CSIC CI focus)

### Notes / Reminders (carried forward)
- Lab credentials documented in this log are for isolated, NAT'd,
  non-internet-facing VMs. Low risk as configured — revisit before any
  network exposure changes.
- Project scope is deliberately bounded to skills development and
  resume/interview material, not a production MSSP — re-evaluate broader
  SOCaaS ambitions no sooner than 1+ year from the 2026-06-17 rescope
  decision.

---

## [2026-06-19] Naming Convention Update — Host Designations

Established formal Warhammer 40K-themed names for the two physical
hosts going forward, to keep documentation and conversation consistent:

- **EoM ("Empire of Man")** — the Dell R640. Centralized/persistent
  analytical infrastructure: Guilliman (Wazuh), Rogal_Dorn (pfSense,
  with WireGuard), future Suricata VM, future Security Onion.
- **VS ("Vengeful Spirit")** — the Lenovo laptop. Named for Horus's
  Gloriana-class flagship (confirmed via web search — not to be confused
  with "The Invincible Reason," which is actually Roboute Guilliman's
  flagship). Mobile/disposable infrastructure: Horus (Win10 target),
  future Kali VM, future additional targets.

### Confirmed Next Tasks (carried forward from Session 7/8 decisions)
1. Push analytical solutions (Guilliman, future Suricata VM) to EoM
2. Implement remote access capability via WireGuard on Rogal_Dorn (EoM)
3. Install Kali on VS (Lenovo)

---

## [2026-06-19/20] Session 9 — Kali on VS, Cursor Bug Resolved

### Kali Linux — Installed on VS (Lenovo)
- Downloaded the official **prebuilt Kali VMware image** (kali.org/get-kali
  → Virtual Machines tab) rather than doing a manual ISO install — much
  faster, boots straight to a working desktop with the full standard
  toolset preinstalled (Metasploit, nmap, Burp, etc.)
- Default credentials: `kali` / `kali` — flagged to change via `passwd`
- Ran full system update:
  ```bash
  sudo apt update && sudo apt full-upgrade -y
  ```
- Installed VMware Tools equivalent:
  ```bash
  sudo apt install open-vm-tools open-vm-tools-desktop -y
  ```

### Issue — Invisible Cursor + Severe Lag
- VM cursor was completely invisible (though clicking/input still worked
  — confirmed as a rendering issue, not a true input failure).
- Initial troubleshooting (3D acceleration toggle, display mode switch,
  service status checks, full system upgrade) did not resolve it.
- **Root cause #1 (performance/lag):** the Kali VM was running from a
  **OneDrive-synced folder** rather than local disk — same root cause
  pattern as the ISO-mounting issue hit during the R640/ESXi rebuild
  (Session 8). **Fix:** shut down VM, moved the VM folder to a local
  `C:\` path alongside Horus/Guilliman, unregistered and re-added the VM
  in VMware Workstation from the new location. Resolved the lag.
- **Root cause #2 (invisible cursor, persisted after the OneDrive fix):**
  outdated **virtual hardware compatibility version** on the VM. The
  in-app toggle for "Accelerate 3D graphics" was inaccessible/grayed out,
  which in retrospect was likely a symptom of the same underlying
  compatibility mismatch. **Fix: upgraded the VM's hardware compatibility
  version to the most recent available in VMware Workstation** — this
  fully resolved the cursor issue with no further changes needed.

### Naming Note (carried from prior session)
- Decided to rename the Win10 target VM from **Horus** to **Isstvan III**
  (the planet Horus virus-bombed at the start of the Horus Heresy — a
  better thematic fit for a victim/target machine than Horus itself,
  which is now understood to be better suited to an attacker role).
  Rename not yet executed — flagged as a backlog item, since it requires
  updating the VM label, the Windows hostname, and the Wazuh agent
  registration to stay consistent (currently shows as "Horus" in the
  Guilliman dashboard).

### Lessons Learned (Session 9)
- **Never run a VM's working files from a cloud-sync folder
  (OneDrive/Dropbox/etc.)** — causes severe performance degradation.
  Always store VMs on a local-only path. This is now the second time
  this exact mistake has caused a real problem (previously: ISO mounting
  for the R640 ESXi reinstall in Session 8).
- **An outdated VM hardware compatibility version can manifest as a
  seemingly unrelated display bug** (invisible cursor) rather than an
  obvious compatibility error — when a Linux guest has cursor/SVGA
  rendering issues in VMware Workstation, check/upgrade the hardware
  compatibility version as a primary troubleshooting step, not a last
  resort.

### Open Items / Next Session
- [ ] Change Kali's default password (`passwd`)
- [ ] Note Kali's IP address for future reference
- [ ] Execute the Horus → Isstvan III rename (VM label, Windows hostname,
      Wazuh agent re-registration)
- [ ] Begin Rogal_Dorn (pfSense) rebuild on EoM (R640)
- [ ] Configure WireGuard on Rogal_Dorn once built
- [ ] Migrate/rebuild Guilliman (Wazuh) onto EoM

---

## [2026-06-20] Session 10 — Horus → Isstvan III Rename Completed

### Summary
Completed the full rename from "Horus" to "Isstvan III" across every
layer — VM label, Windows hostname, local user account, and Wazuh agent
registration — resolving the inconsistency flagged in Session 9.

### Steps Completed
1. **VMware Tools installed** on the VM before the rename/reboot pass
   (had not been confirmed installed previously under the old name).
2. **VM label** renamed in VMware Workstation to `Isstvan_III`.
3. **Local Windows user account** renamed:
   ```powershell
   Rename-LocalUser -Name "horus" -NewName "isstvan_3"
   ```
   (Underlying profile folder path unchanged, as expected — cosmetic
   account rename only.)
4. **Windows hostname** renamed via:
   ```powershell
   Rename-Computer -NewName "Isstvan_III" -Restart
   ```
5. **Old Wazuh agent entry removed** from Guilliman via CLI (dashboard
   UI did not expose a delete option in this version/view):
   ```bash
   sudo /var/ossec/bin/manage_agents
   ```
   Selected the interactive "remove an agent" option, removed the old
   "Horus" registration by agent ID.
6. **New Wazuh agent deployed** fresh from the dashboard (Server
   Management → Endpoint Summary → Deploy new agent), this time
   registered as **Isstvan_III**, server address `192.168.76.132`.
   Confirmed **Active** status in the dashboard.

### Keeper Vault
- Updated the corresponding entry: title/labels changed to "Isstvan III
  (formerly Horus)", username field updated to match the renamed local
  account. Password unchanged.

### Current State
- VM, Windows hostname, local user account, and Wazuh agent registration
  are now **fully consistent** under the name **Isstvan III** — no
  remaining references to "Horus" anywhere in active tooling.

### Open Items / Next Session
- [ ] Begin Rogal_Dorn (pfSense) rebuild on EoM (R640)
- [ ] Configure WireGuard on Rogal_Dorn once built
- [ ] Migrate/rebuild Guilliman (Wazuh) onto EoM
- [ ] Change Kali's default password (`passwd`) — still outstanding from Session 9
- [ ] Note Kali's IP address for future reference

## [2026-06-27] Session 11 — ESXi Daily-Driver Account, Rogal_Dorn VM Built, Security Onion Planning

### Summary
Created a non-root daily-driver account on the rebuilt EoM ESXi host.
Built the Rogal_Dorn (pfSense) VM from scratch on EoM with three NICs,
created a new internal vSwitch and two VLAN-tagged port groups, and
wired Rogal_Dorn's NICs to them. Decided Security Onion will be a third
EoM appliance, named **Valdor**, and that it will get its own dedicated
VLAN separate from Guilliman rather than sharing one with it. Also
explored (and deferred) several architectural questions: EC2 as a
WireGuard relay, dedicated pfSense hardware (Netgate 1100), and AD/
BloodHound placement.

### ESXi Daily-Driver Account
- Confirmed the rebuilt EoM ESXi host is reachable at an IP in the
  `192.168.245.x` range (DHCP-assigned post-reinstall) — distinct from
  the old static `192.168.4.40` ("Lionsgate") used pre-wipe.
- Logged in as `root` (password recovered — matched the iDRAC `root`
  credential, consistent with the credential-reuse issue flagged in
  Session 8).
- Created a new non-root local ESXi user via **Manage → Security &
  Users → Users → Add user**, with shell/SSH access enabled at creation
  time (checkbox option present in this ESXi version's "Add user" flow).
- Assigned the new account **Administrator** role at the host level
  (via Manage → Security & Users → Permissions → Add — exact tab/path
  may vary by ESXi build; Tim located it under "Roles"/user-level
  assignment in this version's UI).
- Decision: full Administrator rights for this single daily-driver
  account were judged acceptable for this lab context (single operator,
  no separation-of-duties need), rather than building a more
  least-privilege-scoped role. `root` is reserved for break-glass use
  only going forward, per the Session 8 lesson learned.
- **Backlog item closed:** "Create dedicated ESXi admin user account."

### pfSense ISO Acquisition
- Downloaded pfSense **CE (Community Edition), AMD64** architecture
  from pfsense.org/download (AMD64 is the standard 64-bit x86
  architecture designation, not AMD-specific — covers both AMD and
  Intel CPUs).
- Uploaded to `datastore1` via Host Client (Storage → datastore1 →
  Datastore browser → Upload). Uploaded twice by accident — duplicate
  ISO left in datastore, flagged for later cleanup, no functional impact.

### Rogal_Dorn VM — Created
- **Virtual Machines → Create/Register VM → Create a new virtual
  machine**
- Name: `Rogal_Dorn`
- Guest OS family: Other — Guest OS version: FreeBSD (closest match
  available; current pfSense CE 2.7.x is based on FreeBSD 14, exact
  FreeBSD 14 option may not have been listed in the dropdown)
- Compatibility: **ESXi 8.0 U2 virtual machine** (the available option
  in this ESXi 8.0U3e host's create-VM dropdown; fully compatible with
  the U3e host)
- Memory type: Standard (not Persistent Memory/PMem — PMem is for
  specialized NVDIMM hardware, not applicable here)
- **Virtual hardware:**
  - 2 vCPU
  - 2 GB RAM
  - 20 GB thin-provisioned disk
  - Default SCSI controller
  - CD/DVD Drive: Datastore ISO file → pfSense CE AMD64 ISO on
    `datastore1`
  - **3 network adapters** (all initially defaulted to "VM Network" on
    creation)

### Networking — vSwitch and Port Groups Rebuilt
- Confirmed EoM's `vSwitch0` has two default port groups:
  - **Management Network** — ESXi host management traffic only (what
    the Host Client itself is reached through)
  - **VM Network** — default VM-facing port group, shares the same
    physical uplink (`vmnic0` → Eero) as Management Network, but is
    logically separate and is the correct port group for VM traffic
    needing external connectivity
- Created new internal vSwitch: **`vSwitch-palace`** — no physical
  uplink (internal-only, VM-to-VM traffic exclusively; cannot reach the
  physical network or internet directly).
- Created two VLAN-tagged port groups on `vSwitch-palace`:
  - **`PG-Guilliman`** — VLAN ID 20 — for the Wazuh VM once migrated to
    EoM
  - **`PG-Valdor`** — VLAN ID 30 — for the planned Security Onion VM
    (named Valdor, see below)
- **Decision:** Guilliman and Valdor (Security Onion) will NOT share a
  VLAN. Discussed pros/cons of shared vs. per-appliance VLANs for
  security tooling specifically — concluded that even though both are
  trusted, single-operator-controlled defensive tools, segmenting them
  limits blast radius if either is ever compromised (a documented
  general security-architecture rationale for treating security tooling
  as a high-value target), and demonstrates the stronger-practice
  pattern relevant to Tim's advisory work. Decided in favor of
  separation despite the added complexity, with Rogal_Dorn explicitly
  prioritized to get built and working first.
- **Rogal_Dorn NIC assignments finalized:**
  - NIC 1 (WAN) → `VM Network` (internet/Eero-facing; WireGuard will
    listen here once configured)
  - NIC 2 → `PG-Guilliman` (VLAN 20)
  - NIC 3 → `PG-Valdor` (VLAN 30)
- Explicitly decided **not** to build `PG-VLAN10` (originally planned
  for generic "lab client" VMs) at this time, since none of the three
  currently-planned EoM VMs (Rogal_Dorn, Guilliman, Valdor) are client
  machines. Revisit if/when a client-type VM (e.g., the planned AD DC)
  is placed on EoM.

### Security Onion VM — Named, Not Yet Built
- Decided Security Onion will be the third planned EoM appliance.
- Confirmed (recalling Session 7 notes) that Security Onion bundles
  Suricata and Zeek internally — no separate standalone Suricata
  install needed if Security Onion is deployed.
- **Named: Valdor** (Constantin Valdor, Captain-General of the Adeptus
  Custodes — thematically fits a network-security-monitoring platform
  that watches over the network the way Valdor watches over the
  Emperor). VM not yet built — full Standalone hardware spec (24GB+
  RAM, 4+ CPU, 200GB+ storage) still applies per the original Session 7
  sizing notes.

### Architectural Concepts Clarified This Session
- **vSwitch vs. router:** a vSwitch is Layer 2 only (switching, no
  routing/IP awareness) — Rogal_Dorn (pfSense) is the actual router,
  with a leg in multiple vSwitch/port-group segments at once to bridge
  and firewall between them. ESXi has no native "vRouter" object;
  routing is always done by a VM (here, pfSense) plugged into multiple
  networks.
- **vmnic naming:** `vmnic0`, `vmnic1`, etc. refer to **physical** NICs
  on the R640 as seen from within ESXi — not virtual adapters, despite
  the "vm" prefix. The actually-virtual adapter is the VM's own network
  adapter/vNIC, configured per-VM.
- **VM Network vs. Management Network:** both are port groups on the
  same `vSwitch0`/physical uplink, logically separated for traffic-type
  clarity (host management vs. VM traffic), not separate physical paths
  in this single-NIC-uplink setup.
- **vCenter / vMotion / Distributed vSwitch dependency chain:** vCenter
  is required for both vMotion (live VM migration between hosts) and
  Distributed vSwitches (a vSwitch construct that spans multiple ESXi
  hosts). None of these apply to Tim's current single-host, no-vCenter
  EoM setup. A Standard vSwitch (what EoM uses) is host-local only and
  does not span hosts.
- **Internal vs. external traffic paths confirmed:** VM-to-VM traffic
  between two internal VLANs (e.g., Guilliman ↔ Valdor) stays entirely
  within ESXi, routed only through Rogal_Dorn's internal NICs — it never
  touches `vmnic0`. Only traffic actually entering/leaving EoM's network
  (e.g., internet access, the inbound WireGuard tunnel from VS) uses
  `vmnic0`.
- **Lateral movement / segmentation rationale discussed:** VLAN
  segmentation behind a routing/firewalling chokepoint (Rogal_Dorn) is
  the mitigation for uncontrolled lateral movement, not an instance of
  it — traffic between VLANs must pass through and can be inspected/
  filtered by pfSense, unlike a flat unsegmented network.

### Other Decisions Made This Session
- **EC2 WireGuard relay** — discussed in depth as a way to solve the
  "no inbound access while away from home" chicken-and-egg problem
  (both VS and Rogal_Dorn would dial outbound to a small EC2 instance
  acting as a relay, avoiding any need for port-forwarding on the
  Eero). Real pros: solves the lockout problem permanently, cheap
  ($0–5/mo), adds genuine cloud/AWS security-engineering reps. Real
  cons: third box to patch/maintain/pay for, becomes an internet-facing
  entry point if misconfigured, added WireGuard routing complexity
  (3-peer relay vs. 2-peer direct). **Decision: explicitly deferred**
  until the core on-prem lab (Rogal_Dorn, direct WireGuard, Guilliman
  migration, AD/BloodHound) is stable and working well.
- **Dedicated pfSense hardware (Netgate appliances)** researched via
  Netgate's product page. **Netgate 1100** ($269) selected as the
  appliance of interest: dual-core ARM Cortex-A53 1.2GHz, 1GB DDR4 RAM,
  10.6GB eMMC storage, 3x GbE ports, ~3.48W idle power draw, native
  WireGuard/OpenVPN/IPsec support, 927 Mbps L3 forwarding / 607 Mbps
  firewall throughput / 247 Mbps IPsec VPN throughput per Netgate's
  published performance figures.
  - **Planned placement:** between the Eero and the existing office
    switch (Modem → Eero → Netgate 1100 → switch → EoM/VS), making the
    1100 the new network edge for both hosts rather than Rogal_Dorn
    running as a VM on EoM.
  - **Open items if/when pursued:** decide DHCP vs. static IP handling
    once the 1100 is in place; decide whether to decommission the
    Rogal_Dorn VM entirely or repurpose it as an internal-only VLAN
    router behind the 1100; note that VS would then also pass through
    the 1100 (acting as plain router/switch for VS, not enforcing
    pfSense rules on it specifically unless desired).
  - **Decision: this is a deferred/later-phase item**, not blocking the
    current Rogal_Dorn VM build. Tim explicitly chose to proceed with
    Rogal_Dorn as a VM on EoM now rather than wait for the hardware.
- **Reverse shell / reverse SSH tunnel** discussed as a potential
  WireGuard substitute — concluded reverse shells are one-shot,
  unencrypted attacker payloads with no persistence or multi-host
  routing, not viable infrastructure. Reverse SSH tunnels (`ssh -R`) are
  a legitimate persistent/encrypted alternative, but still require a
  publicly-reachable relay box (i.e., the same EC2 dependency as the
  WireGuard relay option) and are strictly less capable than WireGuard
  for routing whole subnets to multiple internal hosts at once. No
  change to the WireGuard-based plan as a result.
- **PIA (commercial VPN) clarified as unrelated** to home-network remote
  access — PIA uses WireGuard as a protocol but is an outbound-only
  privacy service with no relationship to Rogal_Dorn or EoM; using the
  same protocol does not create a tunnel between unrelated endpoints.
- **AD Domain Controller placement confirmed:** a new, separate Windows
  Server VM (not Isstvan_III, which is Windows 10 Pro and cannot run AD
  DS) will serve as the domain controller, built on **EoM** per Tim's
  stated preference for centralizing "heavy" infrastructure there.
  Isstvan_III will join the domain as a client for BloodHound testing
  purposes. Edition not yet chosen (Windows Server 2022 Evaluation
  suggested as a free option, not yet confirmed).
- **Lord_Commander_Guilliman (current VS instance) confirmed for
  decommission** once Guilliman is rebuilt fresh on EoM — no data on
  the VS instance considered worth preserving.

### VM Naming Corrections (carried into this session)
- Clarified current naming, per Tim: **Horus** = Kali Linux (attacker,
  on VS) — this is the VM that was *originally* going to be renamed to
  Isstvan III per Session 9/10 notes, but Tim's restated mapping this
  session keeps Horus as the Kali VM name. **Isstvan_III** = Win10
  target (on VS). **Lord_Commander_Guilliman** = Ubuntu/Wazuh (currently
  on VS, scheduled for migration/rebuild on EoM).
  - Note: this differs from the Session 10 log, which recorded a
    completed rename of the Win10 target VM from "Horus" to
    "Isstvan_III" (i.e., Horus and Isstvan_III were the same VM,
    renamed). Tim's description this session treats Horus and
    Isstvan_III as two distinct, separate VMs (Kali and Win10
    respectively). This discrepancy has not been independently
    verified or reconciled — flagged here rather than assumed; worth
    confirming actual current VM names/roles on VS directly next time
    they're accessible, rather than relying on changelog history alone.

### Open Items / Next Session
- [ ] Power on Rogal_Dorn and run the pfSense installer (partitioning,
      initial install)
- [ ] Initial pfSense interface assignment (WAN/LAN/OPT1 matching the
      three NICs and their port groups)
- [ ] Configure WireGuard on Rogal_Dorn once pfSense install is complete
- [ ] Delete duplicate pfSense ISO from datastore1
- [ ] Verify/reconcile actual current VM names and roles on VS (Horus /
      Isstvan_III discrepancy noted above)
- [ ] Build Valdor (Security Onion) VM once Rogal_Dorn is stable —
      full Standalone spec, on `PG-Valdor` (VLAN 30)
- [ ] Migrate/rebuild Guilliman onto EoM, on `PG-Guilliman` (VLAN 20)
- [ ] Re-point Isstvan_III's Wazuh agent to new EoM Guilliman IP after
      migration
- [ ] Decommission Lord_Commander_Guilliman on VS once EoM rebuild is
      confirmed working
- [ ] Stand up new Windows Server VM (AD DC) on EoM; join Isstvan_III to
      the domain; run BloodHound from EoM or Horus/Kali against it
- [ ] (Deferred, later phase) Evaluate Netgate 1100 as dedicated pfSense
      hardware, placed between Eero and office switch
- [ ] (Deferred, later phase) EC2 WireGuard relay for remote access when
      away from home with no port-forward path

      Caught a typo in my own draft (line 122 garbled a sentence) — here's the corrected changelog, printed in full:

---

## [2026-06-27] Session 11 (continued) — WireGuard Configured, CGNAT Discovered as Blocker

### Summary
Continued directly from the DNS troubleshooting earlier in Session 11. Built a Kali Linux VM (named **Alpharius**) on EoM specifically to get browser-based GUI access to pfSense (no other device had both network reachability to PG-Guilliman and a working browser). Used the GUI to fix Rogal_Dorn's DNS Resolver. Installed and configured the WireGuard package on Rogal_Dorn (tunnel named **Webway**), set up VS as a peer, configured port forwarding on the Eero, and added a missing WAN firewall rule — but the tunnel still failed to complete a handshake. Root cause identified: Tim's ISP connection is behind **Carrier-Grade NAT (CGNAT)** — the "public" IP visible from whatsmyip.com is not actually a real public IP, making direct inbound WireGuard connectivity to the home network structurally impossible without ISP cooperation, a relay, or IPv6.

### DNS Resolver Fix (Rogal_Dorn)
- Confirmed via direct testing from Rogal_Dorn's own shell that Unbound's default mode (querying root DNS servers directly) was failing with a network error, while direct queries to known public resolvers (8.8.8.8) succeeded.
- **Fix applied:** Services → DNS Resolver → enabled Forwarding Mode; System → General Setup → added DNS servers 8.8.8.8 and 1.1.1.1.
- Confirmed working via Guilliman's `nslookup google.com`.
- **Root cause not independently confirmed** — likely Eero intercepting root-server queries, but inferred, not verified.

### Alpharius VM — Built (Kali Linux, EoM)
- Built to solve a GUI-access gap (Guilliman had reachability, no browser; VS had a browser, no reachability).
- Installed via Kali installer ISO. Specs: 2 vCPU/4GB RAM/40GB disk, 1 NIC on PG-Guilliman.
- Named **Alpharius**. Tim noted **Omegon** as a good name for a possible future second box in this role.
- Open question: keep long-term or decommission once WireGuard works — deferred.

### WireGuard — Configured on Rogal_Dorn, Tunnel Fails to Establish
- Tunnel named **Webway**, address `10.10.10.1/24`. Had to separately enable "Enable WireGuard" under the global Settings tab — distinct from enabling the tunnel itself; flagged as a UI quirk.
- VS peer added: `10.10.10.2/32`, keepalive 25, public key manually retyped (no clipboard sharing between Alpharius's console and the physical Lenovo).
- VS client configured: address `10.10.10.2/24`, endpoint = home public IP:51820, allowed IPs `192.168.1.0/24`.
- Eero port forward: UDP 51820 → `192.168.4.248` — confirmed correctly targeted.
- Added missing WAN firewall rule (only default RFC1918/bogon blocks existed) — Pass, UDP, any source, WAN address, port 51820.
- **Result: still failed.** VS showed ~3 KiB sent, 0 received, no handshake.

### Root Cause Identified: CGNAT
- Ruled out first: WAN IP mismatch, double NAT, missing firewall rule (all checked/fixed, none resolved it).
- Confirmed via modem's own DOCSIS admin page (`192.168.100.1`): WAN/gateway IP reported as `10.34.65.1` / `10.34.64.1` — both private RFC 1918 addresses, not the public IP shown by whatsmyip.com.
- **Conclusion:** Tim's ISP connection sits behind Carrier-Grade NAT. No inbound connection of any kind can reach the home network directly, regardless of port-forwarding/firewall config — this is an ISP-level constraint, not a configuration bug.
- A canyouseeme.org test (TCP/51820) was attempted but is not a valid test for UDP-based WireGuard; its inconclusive result is not cited as supporting evidence. The DOCSIS modem page is the actual confirming evidence.

### Implications / Options Going Forward (undecided)
- **EC2/VPS relay** — previously deferred as a nice-to-have; now likely necessary, since CGNAT only blocks inbound, not outbound, connections.
- **ISP static/public IP add-on** — not yet checked if available.
- **IPv6** — not yet checked if available/passed through; would avoid the relay dependency entirely if viable.
- No option selected yet.

### Open Items / Next Session
- [ ] Decide CGNAT workaround: relay vs. ISP static IP vs. IPv6 (check IPv6 first)
- [ ] If relay: stand up EC2/VPS, configure VS + Rogal_Dorn as outbound peers
- [ ] Decide on keeping/decommissioning Alpharius
- [ ] Delete duplicate pfSense ISO from datastore1
- [ ] Reconcile Horus/Isstvan_III naming discrepancy
- [ ] Build Valdor (Security Onion) VM
- [ ] Install Wazuh on Guilliman (VM built, software not yet installed)
- [ ] Re-point Isstvan_III's Wazuh agent once Wazuh is running on EoM
- [ ] Decommission Lord_Commander_Guilliman on VS
- [ ] Stand up AD DC, join Isstvan_III, run BloodHound
- [ ] (Deferred) Evaluate Netgate 1100 hardware

## [2026-06-27] Session 11 (continued) — Eye_of_Terror EC2 Relay Built, Remote Access Working End-to-End

### Summary
Built a small EC2 instance (**Eye_of_Terror**) to serve as a WireGuard
relay, resolving the CGNAT blocker identified earlier in Session 11.
Reconfigured Rogal_Dorn and VS to dial outbound to the relay instead of
attempting a direct peer-to-peer connection. After several rounds of
troubleshooting (a misconfigured AWS security group, a peer entry
mistakenly pointed at its own public key instead of the relay's, a
missing pfSense interface assignment/firewall rule, and a missing IP
address on the resulting OPT2 interface), confirmed full end-to-end
connectivity: **VS → Eye_of_Terror → Rogal_Dorn → PG-Guilliman**. This
is the first working remote-access path into EoM from outside the home
network.

### Alternatives Considered Before Settling on EC2
- **Tailscale** researched as a no-VPS alternative (built on WireGuard,
  automatic NAT/CGNAT traversal via DERP relays). Confirmed via search
  that Tailscale is not directly interoperable with a standard WireGuard
  peer — it would require replacing the manually-configured WireGuard
  setup entirely with the Tailscale client/daemon on each host, not
  adding to it.
- **NordVPN / commercial consumer VPNs** confirmed not applicable —
  outbound-only privacy services with no mechanism for inbound tunnels
  into a home network, regardless of which protocol they use
  internally.
- **Decision:** proceeded with a self-hosted EC2 relay over Tailscale,
  citing preference for keeping WireGuard (already configured) and
  avoiding a third-party coordination/control-plane service for this
  specific use case, despite Tailscale being the lower-effort option.

### Eye_of_Terror — EC2 Instance Built
- **Instance type:** t3.micro (free-tier eligible), Ubuntu Server 26.04
  LTS, region us-east-2.
- **Named: Eye_of_Terror** (the Warp rift housing the Cadian Gate —
  fits a stable, always-open access point). The WireGuard tunnel itself
  was informally referred to as "the Warp" going forward, alongside its
  existing pfSense-side label of "Webway." Key pair named
  **Ritual_of_Astro_Navigation** (a Navigator rite for plotting warp
  travel coordinates — confirmed via search as a real, accurate lore
  reference, fitting the key's function of "finding the way through").
  Tim noted **Cadian_Gate** as a reserved name for a possible future
  second EC2 instance (a "defender box" concept, not yet built).
- **First launch attempt failed and was discarded:** the initial key
  pair's `.pem` file download silently failed (browser showed an
  incomplete `Unconfirmed####.crdownload` file, easily mistaken for a
  successful download). Since AWS only allows downloading a key pair's
  private key once, at creation, the orphaned key pair was unusable.
  Resolved by terminating the first instance, releasing its Elastic IP,
  and relaunching clean with a new key pair, confirming the `.pem`
  download completed fully before proceeding.
- **Final instance:** Elastic IP allocated and attached:
  **`[REDACTED-PUBLIC-IP — see local notes]`** (replacing the ephemeral default public IP).
- **Security group:** SSH (22) and Custom UDP (51820), both source
  0.0.0.0/0. Decided against IP-restricting SSH given Tim's home
  connection is behind CGNAT (the "public IP" visible to AWS would be
  the ISP's shared NAT gateway, not reliably Tim's alone, and subject to
  change) — relying on SSH key-only authentication as the actual
  security boundary instead.
  - **Mid-session incident:** while adding the UDP/51820 rule, the
    existing SSH rule was accidentally overwritten rather than added
    alongside it (clicked into the existing rule's edit view instead of
    "Add rule"), briefly locking out both SSH and EC2 Instance Connect
    access. Diagnosed by checking the security group's actual rule list
    directly rather than assuming the cause, and resolved by re-adding
    the SSH rule. Both rules confirmed present afterward.
- Connected via standard OpenSSH from Windows PowerShell (`ssh -i
  <path-to-pem> ubuntu@<IP>`) — decided against installing/using PuTTY,
  since OpenSSH ships natively with Windows 10/11, uses the `.pem` file
  directly with no `.ppk` conversion step, and supports the same
  `~/.ssh/config` "saved session" equivalent PuTTY offers via its GUI.

### WireGuard — Reconfigured as a 3-Peer Relay
- Installed WireGuard on Eye_of_Terror (`sudo apt install wireguard`),
  generated its own keypair, and configured `/etc/wireguard/wg0.conf`
  as the relay hub:
  - Interface address: `10.10.10.3/24`, listen port `51820`
  - Peer entries for Rogal_Dorn (`10.10.10.1/32`) and VS (`10.10.10.2/32`)
- Enabled IP forwarding at the OS level (`net.ipv4.ip_forward = 1`,
  persisted in `/etc/sysctl.conf`) — required for Eye_of_Terror to
  actually pass traffic between its two peers rather than just
  terminating its own tunnel traffic.
- **Reconfigured Rogal_Dorn's Webway peer entry** (previously pointed
  directly at VS) to instead peer with Eye_of_Terror:
  - Public Key: Eye_of_Terror's key
  - Endpoint: `[REDACTED-PUBLIC-IP — see local notes]:51820`
  - Allowed IPs: `10.10.10.0/24` (the full tunnel subnet, not a single
    `/32` — necessary so Rogal_Dorn routes anything in that subnet,
    including VS, through this one relay peer)
  - Persistent Keepalive: 25
- **Reconfigured VS's WireGuard client** similarly — peer changed to
  Eye_of_Terror, Endpoint `[REDACTED-PUBLIC-IP — see local notes]:51820`, Allowed IPs
  `10.10.10.0/24,192.168.1.0/24` (tunnel subnet plus PG-Guilliman, so VS
  can reach both the relay and Guilliman through it).
- **Removed the now-unnecessary Eero port-forward rule** (UDP 51820 →
  Rogal_Dorn's WAN IP) — no longer needed once the connection model
  flipped from inbound-to-home to outbound-from-home; confirmed this is
  simply dead config with no functional purpose under the new
  architecture, not something that needed to be replaced with a new
  target.

### Troubleshooting Sequence (in order encountered)
1. **No handshake at all, either peer.** Root cause: AWS security group
   was missing the UDP/51820 inbound rule entirely (only SSH had been
   added at instance launch, despite earlier discussion) — confirmed by
   checking the security group's actual rule list directly rather than
   assuming. Fixed by adding the rule (and accidentally overwriting SSH
   in the process, separately resolved above).
2. **VS ↔ Eye_of_Terror handshake succeeded; VS ↔ Rogal_Dorn still
   failed**, with Eye_of_Terror responding "Destination host
   unreachable" for the Rogal_Dorn tunnel IP. Root cause: Rogal_Dorn's
   peer entry was misconfigured with **its own public key** (ending
   `[REDACTED — see local notes]`) instead of Eye_of_Terror's public key (ending
   `[REDACTED — see local notes]`) — meaning pfSense had never actually been told to talk to
   Eye_of_Terror at all. Also had an incorrect Allowed IPs value
   (`10.10.10.2/32`, a leftover from the original VS-direct peer entry)
   instead of the correct `10.10.10.0/24`. Both corrected; handshakes
   then succeeded on both peers per `wg show` on Eye_of_Terror.
3. **Handshakes up on both peers, but pings from VS to `10.10.10.1` and
   `192.168.1.1` still timed out.** Root cause, identified in two parts:
   - The WireGuard tunnel had never been assigned as a proper pfSense
     interface (Interfaces → Assignments) — added as **OPT2**, renamed
     **WireGuard_Webway**, and enabled.
   - Even after assignment, traffic from OPT2 into LAN was still
     blocked — confirmed via firewall logs that **no blocks were
     logged on OPT2 itself** (ruling out the OPT2 pass rule as the
     issue) while Guilliman → Rogal_Dorn (LAN → tunnel direction) ping
     succeeded fine — isolating the problem specifically to the
     OPT2-into-LAN direction. Default LAN rules (anti-lockout, allow
     LAN-to-any) only cover traffic *sourced from* LAN, not traffic
     *arriving from* another interface destined to LAN — a distinct,
     separate rule was required.
   - **Final root cause:** the OPT2/WireGuard_Webway interface itself
     had no IPv4 address assigned at the interface-configuration level
     (Interfaces → WireGuard_Webway) — the `10.10.10.1/24` address had
     only been set within the WireGuard Tunnel's own Interface
     Configuration page, which is a separate setting from the actual
     OPT2 interface's IP assignment in pfSense. Without it, pfSense had
     no properly configured return path for traffic arriving via that
     interface. **Fix:** set IPv4 Configuration Type to Static, address
     `10.10.10.1/24`, Upstream Gateway: None (not needed for a
     point-to-point tunnel interface). This resolved the issue
     completely.
4. Along the way, also added a Pass rule on the OPT2 interface itself
   (Firewall → Rules → OPT2) allowing traffic through — confirmed not
   to have been the actual blocker once logs showed no OPT2-side blocks,
   but left in place as it's still necessary for OPT2 to pass traffic at
   all (a "default deny" interface with the correct IP but no rules
   would have re-introduced the original problem).

### Result — Confirmed Working
- Full path verified: `ping 10.10.10.1` (Rogal_Dorn tunnel IP) and
  `ping 192.168.1.1` (Rogal_Dorn LAN/PG-Guilliman) both succeed from VS,
  routed through Eye_of_Terror.
- This is the first working remote-access path into EoM from outside
  the home network, resolving the CGNAT blocker identified earlier in
  Session 11.

### Open Items / Next Session
- [ ] Expand VS's Allowed IPs to include `192.168.x.x` (PG-Valdor
      subnet) once Valdor (Security Onion) is built, so remote access
      covers that segment too
- [ ] Consider adding a Pre-Shared Key to the WireGuard peers for
      defense-in-depth (discussed, not configured this session)
- [ ] Decide whether to keep or decommission Alpharius now that VS can
      reach pfSense's GUI directly through the working tunnel
- [ ] Delete duplicate pfSense ISO from datastore1 (carried over)
- [ ] Reconcile Horus/Isstvan_III naming discrepancy (carried over)
- [ ] Build Valdor (Security Onion) VM (carried over)
- [ ] Install Wazuh software on the Guilliman VM (VM built and
      networked; Wazuh itself not yet installed)
- [ ] Re-point Isstvan_III's Wazuh agent to EoM's Guilliman once Wazuh
      is running there
- [ ] Decommission Lord_Commander_Guilliman on VS
- [ ] Stand up AD DC, join Isstvan_III, run BloodHound (carried over)
- [ ] (Deferred) Evaluate Netgate 1100 hardware (carried over) — note
      this would not eliminate the CGNAT problem on its own; the
      relay/Eye_of_Terror approach (or an ISP/IPv6 workaround, both
      confirmed unavailable this session) would still be needed
      regardless of which device terminates the tunnel at home
- [ ] Add Eye_of_Terror's `.pem` key file to Keeper as an attachment
      (currently stored locally under OneDrive sync only)
- [ ] Reserve **Cadian_Gate** as a name for a possible future second
      EC2 instance (defender-box concept, not yet scoped)

      ## [2026-06-29] Session 13 — Rogal_Dorn Rebuild, WireGuard Restored

### Summary
Rogal_Dorn was deleted and rebuilt from scratch using the Netgate
Installer v1.2 (pfSense CE 2.8.1). After a lengthy troubleshooting
process involving DHCP configuration, WireGuard package quirks, and
stale public keys on Eye_of_Terror, full end-to-end connectivity was
restored: VS → Eye_of_Terror → Rogal_Dorn → PG-Guilliman.

### Root Cause of Previous Session's Rogal_Dorn Failure
The original Rogal_Dorn failure (Sessions 11-12) was traced to:
1. **ESXi 4-NIC probe-order instability** — adding a 4th virtual NIC
   to Rogal_Dorn triggered a documented VMware behavior where NIC
   enumeration order becomes unstable past 3 NICs, disrupting existing
   interface assignments silently. Confirmed via forum documentation.
2. **isc-dhcpd failing to start** — a secondary issue that persisted
   through the instability; never fully resolved before the decision to
   rebuild.
3. **Decision:** rebuild Rogal_Dorn fresh rather than continue debugging
   a compromised state. **Lesson learned:** take a VM snapshot before
   any risky NIC/interface change.

### Netgate Installer vs. Legacy pfSense CE ISO
- The Netgate Installer v1.2 is Netgate's current unified installer,
  replacing the standalone pfSense CE ISO. It fetches packages over
  the internet and prompts for CE vs. Plus selection (CE is free, Plus
  requires a paid license).
- During install, the LAN interface configuration wizard pre-configures
  DHCP server settings (static IP, range) — a significant improvement
  over the old installer, which left this entirely to the GUI post-install.
- **Key issue:** the installer retained old `dhcpd.conf` from the
  previous datastore (stale `10.x.x.x` subnet declarations) despite
  being a fresh VM. Required manual editing of
  `/usr/local/etc/dhcpd.conf` to add the correct `192.168.1.0/24`
  subnet declaration.
- isc-dhcpd also required a manual `touch /var/db/dhcpd.leases` before
  it would start (lease database file missing on fresh install).
- **Note:** isc-dhcpd is EOL and will be removed in a future pfSense
  version. Kea is the recommended replacement (System → Advanced →
  Networking). Not yet migrated — deferred.

### pfSense 2.8.1 + WireGuard 0.2.9_6 Known Bug
- A confirmed Netgate forum bug report (April 2026) documents that
  pfSense 2.8.1 + WireGuard package 0.2.9_6 has an issue where
  encrypted WireGuard handshake packets reach pfSense and decrypt
  successfully, but decrypted client data packets never surface on the
  assigned tun_wg interface for routing. Same config worked on 2.7.2.
- This was investigated during troubleshooting but ultimately was NOT
  the root cause of Tim's connectivity failure — the actual cause was
  Eye_of_Terror still having Rogal_Dorn's old public key from the
  previous build (ending `2g=` instead of the new `zE=`). Once
  Eye_of_Terror's wg0.conf was updated and restarted, full connectivity
  was restored on 2.8.1 without downgrading.
- The known bug may still be relevant in other scenarios — flagged for
  awareness.

### WireGuard Interface Assignment — pfSense 2.8.1 Quirk
- `tun_wg0` does not automatically appear in Interfaces → Assignments
  dropdown. It is hidden in the "Available network ports" dropdown which
  defaults to showing `vmx2` — `tun_wg0` must be manually selected from
  that same dropdown before clicking Add. Not a bug, just a non-obvious
  UI behavior.
- Correct sequence confirmed for pfSense 2.8.1:
  1. VPN → WireGuard → Settings → Enable WireGuard → Save → Apply Changes
  2. Create tunnel
  3. Interfaces → Assignments → select `tun_wg0` from dropdown → Add
  4. Enable interface, set static IPv4 `10.10.10.1/24`
  5. Add firewall rule on the new interface (Pass, any/any)

### Other Issues Encountered This Session
- **"Keep Configuration" during WireGuard uninstall** caused stale
  config to persist across reinstalls — always uncheck this before
  removing the package.
- **IPv6/DHCPv6 conflict** — pfSense pre-enabled DHCPv6 and Router
  Advertisements on LAN, which blocked setting a static IPv4 on the
  interface. Fixed by disabling IPv6 entirely: System → Advanced →
  Networking → Disable IPv6.
- **PIA VPN on VS** — confirmed not a cause of WireGuard failures but
  worth disabling before testing tunnel connectivity, since an active
  commercial VPN client can interfere with custom WireGuard configs.

### Current Public Keys (as of this rebuild)
- **Eye_of_Terror**: `YQ0KMayBp9vc4dWoN/t2vp/Whl0iMIbMllWCa7vK4DI=`
- **VS**: `1LPIc3oLVj++TQdQoMYXN7uPwGBmt+vtHtaxPYkVnTY=`
- **Rogal_Dorn (new)**: `9wIVq1f2nQHTMyxBUjuyVOHb+uhBW4omit4OHBOkhzE=`

### Connectivity Confirmed
- VS → Eye_of_Terror → Rogal_Dorn (`ping 10.10.10.1`) ✓
- VS → Eye_of_Terror → Rogal_Dorn → PG-Guilliman (`ping 192.168.1.1`) ✓

### Open Items / Next Session
- [ ] Install Wazuh on Lord_Commander_Guilliman (VM exists, software not
      yet installed)
- [ ] Re-point Isstvan_III's Wazuh agent to Guilliman's EoM IP
      (192.168.1.100) once Wazuh is running
- [ ] Decommission Lord_Commander_Guilliman on VS
- [ ] Migrate/configure DHCP from isc-dhcpd to Kea (deferred)
- [ ] Build Valdor (Security Onion) on PG-Valdor (VLAN 30)
- [ ] Build Alpharius (Kali) on PG-Alpharius (VLAN 40) — requires
      trunking on existing interface, NOT a 4th NIC on Rogal_Dorn
- [ ] Stand up AD DC, join Isstvan_III, run BloodHound
- [ ] Add topology PNG to diagrams/ folder in git repo
- [ ] Add Eye_of_Terror .pem key to Keeper as attachment
- [ ] (Deferred) Netgate 1100 hardware evaluation

## [2026-07-05] Session 14 — Wazuh Installed, Full Pipeline Validated

### Summary
Installed Wazuh 4.14.5 on Lord_Commander_Guilliman (EoM). Re-pointed
Isstvan_III's Wazuh agent from the old VS-side Guilliman IP
(192.168.76.132) to the new EoM IP (192.168.1.100). Validated the full
detection pipeline end to end, including confirmed remote connectivity
via the WireGuard relay with no physical hardline.

### Wazuh Install — Lord_Commander_Guilliman
- Installed Wazuh 4.14.5 (current stable as of 2026-06-29) via the
  official all-in-one installer:
  ```bash
  curl -O https://packages.wazuh.com/4.14/wazuh-install.sh
  sudo bash ./wazuh-install.sh -a -i
  ```
- All three services confirmed running: wazuh-manager, wazuh-indexer,
  wazuh-dashboard
- Dashboard accessible at https://192.168.1.100
- Admin password reset via CLI (GUI blocks admin password changes —
  "admin is reserved"):
  ```bash
  sudo /usr/share/wazuh-indexer/plugins/opensearch-security/tools/wazuh-passwords-tool.sh -u admin -p <password>
  ```
- Credentials saved to Keeper

### Isstvan_III Agent Re-pointed
- Agent config had stale manager IP (192.168.76.132 — old VS Guilliman)
- Updated via PowerShell:
  ```powershell
  (Get-Content "C:\Program Files (x86)\ossec-agent\ossec.conf") -replace '192.168.76.132', '192.168.1.100' | Set-Content "C:\Program Files (x86)\ossec-agent\ossec.conf"
  Restart-Service WazuhSvc
  ```
- Agent registration confirmed in Guilliman's ossec.log:
  `wazuh-authd: INFO: Agent key generated for 'Isstvan_III'`
- Isstvan_III confirmed Active in agent list (ID: 001)

### Sysmon localfile block re-added to ossec.conf
- Added to C:\Program Files (x86)\ossec-agent\ossec.conf:
  ```xml
  <localfile>
    <location>Microsoft-Windows-Sysmon/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
  ```
- WazuhSvc restarted after change

### Detection Validated
- Test: `cmd.exe /c echo malware` from elevated PowerShell on Isstvan_III
- Alert confirmed in dashboard: rule 92004, T1059.003 (Windows Command
  Shell), Tactic: Execution
- Dashboard path: Threat Hunting → Events
- Query used: `agent.name: Isstvan_III AND data.win.system.eventID: 1`

### Remote Connectivity Confirmed
- Physical hardline disconnected from VS — WireGuard relay (Eye_of_Terror)
  maintained connectivity
- Ping to 192.168.1.100 (Guilliman) succeeded remotely
- Full path confirmed: Isstvan_III → Webway → Eye_of_Terror →
  Rogal_Dorn → Guilliman

### Snapshots Taken (known good state)
- Rogal_Dorn — pfSense configured, WireGuard working, DHCP serving
- Lord_Commander_Guilliman — Wazuh 4.14.5 installed, Isstvan_III active
- Isstvan_III — Wazuh agent pointing at 192.168.1.100, Sysmon
  configured, ossec.conf updated

### VS-side Guilliman Decommissioned
- Lord_Commander_Guilliman VM on VS deleted from disk — no longer needed
  now that EoM Guilliman is confirmed working

### Open Items
- [ ] VLAN trunking on vmx2 for PG-Alpharius (VLAN 40) — requires
      dedicated session, no 4th NIC on Rogal_Dorn
- [ ] Build Valdor (Security Onion) on PG-Valdor (VLAN 30)
- [ ] Stand up AD DC, join Isstvan_III, run BloodHound
- [ ] Migrate DHCP from isc-dhcpd to Kea (deferred)
- [ ] Add topology PNG to diagrams/ in git repo

## [2026-07-05] Session 15 — Network Restructure, Security Onion Install in Progress

### Summary
Renamed port groups to match lore conventions, restructured network
addressing to use static IPs throughout, diagnosed and fixed multiple
Layer 2 connectivity issues, and successfully started Security Onion
3.1.0 installation on Valdor. Install was still in progress (downloading
/upgrading packages) at session end.

### Port Group Renames
- `PG-Guilliman` → `PG-Ultramarines` (VLAN 20, 192.168.1.0/24)
- `PG-Valdor` → `PG-Custodes` (VLAN 30, 192.168.2.0/24)
- Naming convention established: port groups named after legions,
  VMs named after primarchs/characters

### New VMs Planned
- **Calth** — victim VM on PG-Ultramarines
- **Hive_Primus** — victim VM on PG-Custodes
- **Valdor** — Security Onion (Constantin_Valdor), on PG-Custodes (management)
  and PG-Ultramarines (sniffing NIC)

### Rogal_Dorn — OPT2 (Custodes) Configured
- vmx2 assigned as OPT2 → interface renamed `Custodes` in pfSense
- Static IP: `192.168.2.1/24`
- DHCP server enabled on Custodes: range `192.168.2.100`-`192.168.2.200`
- Firewall rule added: Pass IPv4 Any/Any on Custodes interface
- **Key issue discovered:** vmx2's "Connected" checkbox in ESXi was
  unchecked, causing "no carrier" on the Custodes interface. This
  silently broke all Layer 2 connectivity on PG-Custodes. Fixed by
  re-checking "Connected" in Rogal_Dorn's VM settings.

### Static IP Migration (away from DHCP on LAN)
- DHCP disabled on LAN (PG-Ultramarines) — all VMs now use static IPs
- **Lord_Commander_Guilliman:** static `192.168.1.100/24` via netplan
- **Alpharius:** two NICs
  - eth0 → PG-Ultramarines: `192.168.1.101/24`, gateway `192.168.1.1`
  - eth1 → PG-Custodes: `192.168.2.101/24`, no gateway (Ultramarines
    owns the default route)
  - Configured via nm-connection-editor (Kali uses NetworkManager, not
    netplan)
  - Key lesson: both NICs having a gateway creates competing default
    routes — only the primary segment's NIC should have a gateway set

### Alpharius — Second NIC Added
- Added second NIC to Alpharius connected to PG-Custodes (eth1,
  192.168.2.101/24) giving it visibility into both segments

### Constantin_Valdor (Security Onion VM) — Setup
- VM specs: 4 vCPU, 24GB RAM, 200GB disk
- Two NICs:
  - NIC 1 → PG-Custodes (management, ens34) — `192.168.2.10/24`
  - NIC 2 → PG-Ultramarines (sniffing, ens37) — no IP
- Hostname: `valdor`
- **SO installer error resolved:** "The IP being routed by Linux is not
  the IP address assigned to the management interface" — caused by ens37
  (sniffing NIC) acquiring a DHCP lease on PG-Ultramarines and creating
  a conflicting default route. Fixed by disabling DHCP on LAN entirely,
  so ens37 gets no IP.
- **Install command:** `sudo /home/valdor/SecurityOnion/setup/so-setup iso`
- **Access range entered:** `192.168.0.0/16`
- Status at session end: downloading/upgrading packages — install in
  progress

### Key Lessons Learned
- ESXi "Connected" checkbox on a VM NIC can be silently unchecked,
  causing "no carrier" on a pfSense interface with no obvious error
  in the pfSense GUI — always verify in Host Client if an interface
  shows no carrier despite appearing configured
- Security Onion requires the sniffing NIC to have NO IP address —
  if it gets a DHCP lease, a conflicting default route is created
  and the installer fails with a routing error
- Kali Linux uses NetworkManager (nmcli/nm-connection-editor), not
  netplan — Ubuntu uses netplan
- When a VM has two NICs on different subnets, only one should have
  a default gateway set to avoid routing conflicts

### Open Items
- [ ] Complete Security Onion install on Valdor (in progress)
- [ ] Verify SO dashboard accessible at https://192.168.2.10
- [ ] Build Calth (victim VM, PG-Ultramarines)
- [ ] Build Hive_Primus (victim VM, PG-Custodes)
- [ ] VLAN trunking for additional segments (deferred)
- [ ] AD DC + BloodHound (deferred)
- [ ] Update topology PNG in diagrams/

## [2026-07-12] Session 16 — iPhone WireGuard, SO Access, Victim VM Planning

### Summary
Added iPhone as a WireGuard peer, resolved Security Onion dashboard
access (403 errors), covered VM file management fundamentals, and
planned victim VM architecture for PG-Custodes and PG-Ultramarines.

### iPhone WireGuard Peer Added
- iOS WireGuard app configured as a new Webway peer
- Tunnel IP: 10.10.10.4/24
- Public key: Tcy0Db4iUpHWtcGY90bY+hKYiBDGI+seVVNkGFyArB8=
- Added as permanent peer on Eye_of_Terror via:
  ```bash
  sudo wg set wg0 peer Tcy0Db4iUpHWtcGY90bY+hKYiBDGI+seVVNkGFyArB8= allowed-ips 10.10.10.4/32
  ```
- Good handshake confirmed
- SO dashboard accessible from iPhone after so-firewall update

### PG-Custodes Added to VS and iPhone AllowedIPs
- Updated VS WireGuard client peer AllowedIPs:
  ```
  10.10.10.0/24, 192.168.1.0/24, 192.168.2.0/24
  ```
- Updated Eye_of_Terror wg0.conf Rogal_Dorn peer AllowedIPs:
  ```
  10.10.10.1/32, 192.168.1.0/24, 192.168.2.0/24
  ```
- VS confirmed pinging 192.168.2.1 and 192.168.2.10

### Security Onion Dashboard Access Resolved
- Initial install set access to only `192.168.2.10` (Valdor's own IP)
- VS (10.10.10.2), Alpharius (192.168.1.101, 192.168.2.101), and iPhone
  (10.10.10.4) all added via:
  ```bash
  sudo so-firewall includehost analyst <IP>
  sudo so-firewall apply
  ```
- Dashboard confirmed accessible from VS, Alpharius, and iPhone at
  https://192.168.2.10

### VM File Management — Key Lessons
- VM files (config .vmx, virtual disk .vmdk, snapshots, logs) are stored
  in a folder per VM at a chosen location
- On VMware Workstation (VS): default path is chosen during wizard,
  typically Documents\Virtual Machines\<VM name>
- On ESXi (EoM): all VMs stored in datastore1 on the R640's RAID 10
  array, managed by ESXi Host Client
- Moving a VM safely: either use VMware Workstation's built-in Move
  function, or move the folder manually then File → Open the .vmx at
  its new location
- Never move individual files within a VM folder separately from the .vmx
- Never store VM files in OneDrive-synced folders (known issue from 2025)
- Horus successfully relocated from Machine_Spirits\ to
  Machine_Spirits\Horus\ using the manual move + re-open approach

### Victim VM Architecture Planned
Naming convention confirmed: port groups named after legions, VMs after
characters/locations. Snapshots to be taken enterprise-wide before any
attack exercises begin.

**PG-Ultramarines (192.168.1.0/24):**
- Calth — Linux victim VM (Metasploitable 3 Ubuntu 14.04), planned

**PG-Custodes (192.168.2.0/24):**
- Hive_Primus — Windows victim VM (Metasploitable 3 Win2008 R2), planned
- TBD name — Linux victim VM (Metasploitable 3 Ubuntu 14.04), planned

**Attack flow envisioned:**
- Horus attacks victims across both segments via Webway
- Lateral movement between segments (Custodes → Ultramarines) is
  deliberately possible for realistic kill chain exercises
- Valdor (Security Onion) monitors network traffic on PG-Ultramarines
  (sniffing NIC, ens37, no IP)
- Guilliman (Wazuh) catches host-based telemetry from agents
- Snapshots on all VMs = reset button after each exercise

### Metasploitable 3 Research
- Windows Server 2008 R2 version: no pre-built OVA exists due to
  Microsoft licensing restrictions — must be built via Vagrant + Packer
  (downloads Windows evaluation copy from Microsoft during build)
- Ubuntu 14.04 version: pre-built OVA available on SourceForge
- Vagrant current support status: to be confirmed next session
- Decision deferred: evaluating Vagrant + VirtualBox build vs.
  custom Windows Server victim vs. OVA-based Linux victim

### Open Items
- [ ] Confirm Vagrant support/EOL status before committing to that path
- [ ] Build Hive_Primus (Windows victim, PG-Custodes)
- [ ] Build Linux victim on PG-Custodes (name TBD)
- [ ] Build Calth (Linux victim, PG-Ultramarines) — deferred
- [ ] Add iPhone peer permanently to Eye_of_Terror wg0.conf
- [ ] Update SENSITIVE_LOCAL_ONLY.txt with iPhone public key
- [ ] Enterprise-wide snapshots before attack exercises
- [ ] Update topology PNG in diagrams/
- [ ] Full README update (deferred)
- [ ] Terraform setup for multi-VM provisioning (future session)
---

## [2026-07-25] Session 17 — Eye_of_Terror Logging, Docker Host Build, Vulhub

### Summary
Closed out host-level Wazuh logging on Eye_of_Terror, made final decisions
on victim VM architecture (Docker/Vulhub for Linux, full VMs for Windows —
no container path exists for Windows), built and provisioned the first
Docker host (`Hive_Secundus`), and cloned Vulhub. Also updated the topology
diagram and README.

### Eye_of_Terror — Wazuh Agent Renamed
- Agent had auto-registered under its AWS hostname (`ip-172-31-37-109`)
  instead of a readable name
- **Key lesson confirmed:** Wazuh does not support renaming an agent in
  place, via CLI or GUI — the only supported path is remove + re-register
- Removed via `manage_agents` (R, agent ID 002) on Guilliman
- Re-registered from Eye_of_Terror with explicit name:
  ```bash
  sudo systemctl stop wazuh-agent
  sudo /var/ossec/bin/agent-auth -m 192.168.1.100 -A Eye_of_Terror
  sudo systemctl start wazuh-agent
  ```
- Confirmed showing as `Eye_of_Terror`, Active, in Guilliman's dashboard

### Eye_of_Terror — Host Log Sources Added
- Added to `/var/ossec/etc/ossec.conf` (alongside existing default
  `<localfile>` blocks, including default `journald` coverage already
  present):
  ```xml
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/syslog</location>
  </localfile>
  ```
- Restarted agent, confirmed `active (running)`, all subprocesses up
- **Validated end-to-end:** deliberate failed SSH login
  (`ssh nonexistentuser@<Eye_of_Terror IP>`) confirmed visible in
  Guilliman's dashboard within ~30-60s
- **Deferred (not implemented):** WireGuard handshake-polling script
  (peer liveness monitoring) and iptables drop logging — judged
  non-standard/high-effort relative to value right now; revisit after
  the range is further built out. Rationale: Wazuh's rule engine
  reacts to events as they arrive, it doesn't natively evaluate log
  timestamp age, so alerting on stale handshakes would require the
  polling script itself to calculate staleness and emit a distinctly
  matchable log line — real but nontrivial custom logic.

### Victim VM Architecture — Decisions Finalized
- **Linux targets:** Docker + Vulhub on a dedicated Ubuntu Server host,
  **default bridge networking** (not macvlan) — containers differentiated
  by port on the host's single IP, not by distinct per-container IPs
  - Reasoning: macvlan requires ESXi's Forged Transmits vSwitch policy
    to be set to Accept (unconfirmed/untested); bridge mode sidesteps
    that entirely and was judged sufficient for CVE-specific
    exploit-and-detect exercises given time/resources aren't the binding
    constraint
  - 1:many reverse-proxy routing (nginx/Traefik, hostname-based instead
    of port-based) identified as a future upgrade path, not needed now
- **Windows targets:** confirmed no container path exists — Vulhub/Docker
  only support Linux containers (x86 only, no ARM). Windows Server and
  Windows Desktop targets require full VMs, no shortcut
- **Windows Server 2008 R2 (original Metasploitable3 Windows target)
  sourcing dead-ended:**
  - Microsoft's official evaluation download for 2008 R2 x64 (id=11093)
    now redirects to the Itanium-only page (id=22077) — x64 evaluation
    has been pulled from Microsoft's site entirely
  - Only remaining source is unofficial Internet Archive re-uploads —
    rejected in favor of pivoting to a modern Windows Server version
- **Pivoted to modern Windows Server (2019/2022)** — both confirmed
  still live on Microsoft's official Evaluation Center, 180-day eval
  - Licensing/lifespan resolved: `slmgr /rearm` allows up to 6 resets of
    the 180-day evaluation clock without reinstalling or losing
    configuration — approx. 3 years total runway on a single install
  - Trade-off accepted deliberately: loses EternalBlue/MS17-010-specific
    practice, gains realistic modern attack surface (PrintNightmare,
    Zerologon, etc. — specific CVE choice deferred, judged premature/
    narrow-scoping to lock in one CVE before the VM even exists)
  - Still not yet built — remains an open item

### Docker Host VM Built — Hive_Secundus
- **Naming:** `Hive_Primus` (original name for the PG-Custodes Windows
  victim slot per the 2026-07-12 plan) reserved for the future Windows
  Server target. New Docker/Linux host named **Hive_Secundus** instead.
- **Specs:** 2 vCPU, 4096 MB RAM, 40-60GB thin-provisioned disk, network
  adapter on PG-Custodes port group
- **OS:** Ubuntu Server 26.04 LTS (standard install, not minimized —
  deliberate choice to keep full default tooling available)
- Installer offered **Ubuntu Server** vs **Ubuntu Server (minimized)** —
  went with standard
- **Network — DHCP anomaly flagged:** installer auto-assigned
  `192.168.2.104/24` via DHCP despite PG-Custodes being documented as
  DHCP-disabled/static-only. Switched to manual/static configuration
  as planned, but the underlying cause (DHCP apparently active on
  PG-Custodes) was not investigated this session — **open item to
  check Rogal_Dorn's DHCP config on PG-Custodes**
- **Final static config:**
  - Address: `192.168.2.104/24`
  - Gateway: `192.168.2.1`
  - Interface: `ens34`
- Hostname: `hivesecundus`; username: `magus`
- OpenSSH server installed during setup
- Skipped all featured snaps (explicitly declined Docker-via-snap and
  microk8s) — Docker installed via official apt repo instead;
  microk8s judged out of scope (full orchestration platform, not
  needed for single-host manual `docker compose up/down` workflow)
- **Password note:** deliberately left as a weak/simple credential.
  Rationale discussed and accepted: PG-Custodes is not internet-facing
  (only Eye_of_Terror has a public IP), password-complexity practice
  has no offensive-skill training value once credential attacks are
  already understood, and the real training value of this range lives
  in exploitation + detection engineering, not in cracking the host's
  own login. Accepted risk: Alpharius (Kali) sits on the same segment,
  so a weak credential here is only safe under disciplined, deliberate
  targeting — not if broad/untargeted scans of PG-Custodes become part
  of future exercises.

### Docker Engine Installed (Official Repo Method)
Followed Docker's official Ubuntu install docs
(docs.docker.com/engine/install/ubuntu/) exactly:
```bash
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
- **Confirmed:** Docker's repo already has full support for Ubuntu 26.04's
  codename (`resolute`) — no fallback/pinning needed
- **Transient failure encountered:** first `docker run hello-world` pull
  failed with a DNS resolution error on
  `production.cloudfront.docker.com` (`no such host` via
  `127.0.0.53`). Diagnosed as transient, not a real config problem —
  `resolvectl status` confirmed correct DNS server (192.168.2.1),
  `nslookup` on the same domain succeeded moments later, and a retry of
  `docker run hello-world` completed successfully (image pulled, test
  container ran). Theory noted but unconfirmed: the domain resolves
  both A and AAAA records, and this host has no IPv6 configured — a
  first-attempt IPv6 lookup timeout could explain a one-off failure
  like this, but it wasn't proven, only worked around by retrying.
- **Docker Engine confirmed working** via successful `hello-world` run

### Vulhub Cloned
```bash
git clone https://github.com/vulhub/vulhub.git
cd vulhub
```
- Confirmed present: a folder for **CVE-2026-63030 / CVE-2026-60137
  ("wp2shell")** — the critical unauthenticated WordPress Core RCE
  chain disclosed 2026-07-17, actively exploited in the wild as of
  2026-07-18 through 2026-07-20. Not yet stood up — README review and
  `docker compose up` deferred to next session.

### Topology Diagram (`diagrams/empire_of_man_topology.drawio`) Updated
- Added confirmed OS/version detail: Rogal_Dorn ("pfSense,
  FreeBSD-based"), Guilliman ("Ubuntu Server 26.04 LTS", "Wazuh manager
  4.14.6" — corrected from previously recorded 4.14.5), Eye_of_Terror
  ("Ubuntu LTS")
- Added `whiteSpace=wrap;html=1;` to all node styles — text was
  overflowing box boundaries before this fix
- Increased vertical spacing throughout (VS → Eye_of_Terror → Rogal_Dorn
  → vSwitch-palace → PG segments → legend) — previously cramped, with
  vSwitch-palace nearly touching the PG segment containers
- Confirmed via local XML validation (`xml.etree.ElementTree`) after
  every edit — no malformed XML introduced

### README.md Updated
- Added new `## 🗺️ Topology` section referencing the diagram
- Fixed a recurring problem: embedding images via GitHub's
  `user-attachments` one-time upload links (created by pasting an
  image directly into the GitHub web editor) doesn't work for updates —
  those links are content-addressed and permanent, not reusable. Fixed
  by switching to a relative repo path (`diagrams/topology_<name>.png`)
  instead, so future diagram updates only require overwriting the PNG
  at that path, not re-editing the README
- Moved Security Onion from "Planned" to "Current Capabilities"; checked
  off the corresponding roadmap item; updated "Current Scope" to name
  both VLANs and Security Onion's role explicitly

### Key Lessons Learned
- Wazuh agent names cannot be changed once registered, on any Wazuh
  version, via CLI or GUI — remove and re-register is the only path
  (acceptable since a new agent has no meaningful log history to lose)
- Windows evaluation media sourcing degrades over time as Microsoft
  retires old evaluation download pages — don't assume an older OS
  eval ISO will remain officially available; verify before committing
  a build plan to it
- Windows Server evaluation `rearm` (up to 6 resets) provides ~3 years
  of runway on a single install without reinstalling — this fully
  resolves "the eval period is too short" concerns for a lab context
- Vulhub and Docker in general have zero Windows-container support —
  this is a hard architectural boundary, not a configuration gap to
  work around
- GitHub's `user-attachments` image links (from pasting an image into
  the web editor) are one-time/permanent — never reusable for updating
  a diagram in place. Always reference a real file path in the repo
  instead.
- A DHCP lease appearing on a segment documented as DHCP-disabled is
  worth investigating even if a workaround (manual static config) is
  applied in the moment — root cause not yet confirmed on PG-Custodes

### Open Items
- [ ] Investigate why PG-Custodes handed out a DHCP lease
      (`192.168.2.104`) despite being documented as DHCP-disabled
- [ ] Stand up wp2shell (CVE-2026-63030 / CVE-2026-60137) on
      Hive_Secundus via `docker compose up`, validate exploitation
- [ ] Extend Security Onion (Valdor) visibility to PG-Custodes — sniffing
      NIC currently only covers PG-Ultramarines; needs either a second
      sniffing interface on Valdor or a port-mirror/SPAN config on
      `vSwitch-palace`. Whether free-tier ESXi's vSwitch even supports
      port mirroring is unconfirmed.
- [ ] Configure Wazuh `docker-listener` wodule on Hive_Secundus (host
      level) to capture container lifecycle events; configure Docker
      logging driver or volume-mounted logs so Vulhub app-level logs
      (e.g. HTTP access logs for wp2shell) reach Wazuh/Suricata
- [ ] Build Windows Server VM (2019 or 2022 eval) on PG-Custodes —
      Hive_Primus name reserved for this
- [ ] Deferred: WireGuard handshake-polling script and iptables drop
      logging on Eye_of_Terror
- [ ] Deferred: Docker/Vulhub host provisioning automation (Packer +
      Ubuntu autoinstall) — judged worth revisiting only after seeing
      how the manual Hive_Secundus workflow plays out in practice
- [ ] Export and commit updated topology PNG; verify README image
      renders correctly on GitHub

---

## [2026-07-25] Session 18 — Valdor PG-Custodes Visibility, wp2shell Exploited & Detected

### Summary
Closed the Security Onion / PG-Custodes visibility gap flagged in Session
17, then validated the full detection pipeline end-to-end: benign
traffic, an nmap scan, and a live exploit run of CVE-2026-63030/60137
(wp2shell) against Hive_Secundus — all confirmed visible in Kibana, with
Suricata's ET ruleset firing a purpose-built signature for the exploit
itself.

### Valdor — PG-Custodes Sniffing Coverage Added
- **Root cause of the gap:** Valdor's sniffing NIC (`ens37`) was only ever
  bonded to cover PG-Ultramarines; PG-Custodes had no sensor visibility
  at all since Valdor was first built (Session 15)
- **ESXi-side check:** confirmed `vSwitch-palace` has Promiscuous Mode set
  to Accept (inherited by all port groups, including PG-Custodes) — no
  vSwitch config change needed, this was already correct
- **Added a second NIC to Valdor** in ESXi, connected to PG-Custodes,
  after taking a snapshot first
- On first boot, the new NIC (`ens38`) auto-configured via DHCP under a
  generic "Wired connection 1" profile — **second confirmed instance**
  of DHCP being active on PG-Custodes despite it being documented as
  DHCP-disabled/static-only (first instance: Hive_Secundus's install in
  Session 17). Root cause still not investigated — open item, worth
  checking Rogal_Dorn's DHCP config directly next time.
- **Key finding: Security Onion runs on a RHEL-family base (Oracle Linux
  9), not Ubuntu** — no netplan present; network config is via
  NetworkManager/`nmcli`, unlike every other Ubuntu-based host in the lab
- **Fix applied:**
  ```bash
  sudo nmcli connection delete "Wired connection 1"
  sudo nmcli connection add type ethernet slave-type bond con-name bond0-slave-ens38 ifname ens38 master bond0
  sudo nmcli connection up bond0-slave-ens38
  ```
- Confirmed via `/proc/net/bonding/bond0`: both `ens37` and `ens38` now
  active slave interfaces, `ens38` has no IP (`NOARP,PROMISC,SLAVE` flags
  match `ens37`'s existing pattern)
- Ran `sudo so-monitor-add ens38` (SO's dedicated tool for this) as a
  belt-and-suspenders step after the manual `nmcli` bond join — produced
  no output and no detectable config change in `/opt/so/conf/` or
  `/opt/so/saltstack/local/pillar/`, consistent with the interface
  already being correctly bonded
- **Confirmed via running process** that Suricata was already watching
  the whole bond, not individual member NICs:
  ```
  /opt/suricata/bin/suricata -c /etc/suricata/suricata.yaml --af-packet=bond0 ...
  ```
  This meant no Suricata/Zeek config change was needed at all — adding a
  NIC to `bond0` was sufficient on its own for both sensors to start
  seeing PG-Custodes traffic

### Detection Validated — Three Escalating Tests
1. **Benign traffic:** `curl` from Alpharius to Hive_Secundus
   (`192.168.2.104:8080`) — confirmed visible in Kibana Discover,
   including a `zeek.file` entry (Zeek's file-extraction log correctly
   analyzing the HTTP response body)
2. **nmap scan:** `nmap -sV 192.168.2.0/24` run from Horus — traffic
   confirmed showing up under `source.ip: "10.10.10.2"` (VS's WireGuard
   tunnel IP), **not** Horus's real internal IP
   (`192.168.76.133`, a VMware Workstation NAT address that gets
   translated/NAT'd through VS before reaching the lab network — noted
   as an important detail for any future attempt to correlate source IPs
   back to a specific attacker VM). Confirmed a genuine Suricata alert:
   **"ET SCAN Suspicious inbound to mySQL port 3306"** — built-in ET
   ruleset caught the scan without any custom rule work.
3. **Live exploit — wp2shell (CVE-2026-63030/60137) against
   Hive_Secundus:**
   - Check-only mode (`--check`) run from Horus first: confirmed
     vulnerable (SQL injection timing oracle calibrated successfully)
   - **Full exploit chain failed when run from Horus** at the
     data-extraction stage (`could not recover a valid WordPress posts
     table`) — timing oracle calibration succeeded but bit-by-bit blind
     SQLi extraction did not
   - **Full exploit chain succeeded cleanly when re-run from Alpharius**
     (same LAN segment as Hive_Secundus, no tunnel hop) — created a new
     unauthenticated administrator account
     (`w2s_4e3dadd55679`) via the full oEmbed-cache-poisoning /
     forged-changeset chain described in Vulhub's README
   - **Working theory (untested further, but consistent with observed
     timing values):** Horus's baseline latency was much higher than
     Alpharius's (Horus's path traverses VS → WireGuard tunnel →
     Rogal_Dorn → Hive_Secundus, vs. Alpharius's single-hop LAN path —
     Alpharius's calibration baseline was 0.027s vs. Horus's much higher
     figure). Timing-based blind SQL injection depends on precisely
     measuring small delay differences: consistent with the theory that
     network jitter over the tunnel path corrupted individual bit
     extractions even though the initial timing oracle calibration
     (a coarser measurement) still succeeded.
   - **Suricata fired a purpose-built ET signature** on the successful
     Alpharius run — `sid:2071234`,
     "ET WEB_SPECIFIC_APPS WordPress Core wp2shell Remote Code Execution
     (CVE-2026-63030 & CVE-2026-60137) M2", created 2026-07-20 (3 days
     after public disclosure). Rule matches the literal
     `rest_route=/batch/v1` URI pattern plus `author_exclude=` in the
     request body plus a broad SQLi-syntax regex. Includes MITRE ATT&CK
     mapping: `T1190 Exploit_Public_Facing_Application`,
     `TA0001 Initial_Access`, `confidence High`, `severity Major`.

### Key Lessons Learned
- Security Onion's sensors (Suricata/Zeek) are configured to watch the
  Linux bonding interface (`bond0`) as a whole, not individual member
  NICs by name — adding a new NIC to an existing sensor bond is
  sufficient on its own to extend visibility to a new segment; no
  separate Suricata/Zeek config change is needed
- Security Onion 3.1.0 runs on Oracle Linux (RHEL-family), not Ubuntu —
  network configuration is via NetworkManager/`nmcli`, not netplan. This
  is the only host in the lab that differs from the otherwise
  Ubuntu-standardized fleet.
- Traffic originating from a nested VM (Horus, running inside VS) shows
  up on the wire under VS's own WireGuard tunnel IP (`10.10.10.2`), not
  the nested VM's actual internal IP — NAT translation happens
  transparently at the VS host layer. Any future Suricata rule or
  investigation that tries to attribute traffic to a specific attacker
  VM needs to account for this.
- Timing-based blind SQL injection is sensitive to network latency
  consistency — a working exploit over a low-latency LAN path can fail
  at the data-extraction stage over a higher-latency/tunneled path, even
  though the initial timing-oracle calibration still succeeds. Not yet
  root-caused with certainty, but the pattern is consistent with jitter
  corrupting fine-grained timing measurements specifically.
- Existing default/community rulesets (Suricata ET rules) already
  provide real, working detection coverage for both generic scan
  behavior and — remarkably fast, within days of disclosure — a brand
  new named CVE chain. Confirms that the highest-value custom Suricata
  rule work (per the roadmap) is likely to be rules targeting things
  *not* already covered by ET, rather than duplicating existing
  scan/exploit-signature coverage.

### Open Items
- [ ] Investigate root cause of DHCP being active on PG-Custodes —
      now confirmed twice (Hive_Secundus, Valdor's `ens38`) despite the
      segment being documented as static-only/DHCP-disabled
- [ ] Confirm the tunnel-latency theory for the Horus wp2shell failure,
      if further investigation is ever wanted (not required — Alpharius
      run is a fully validated, sufficient success)
- [ ] Wazuh agent + container-level logging still not installed on
      Hive_Secundus (host-level telemetry layer, secondary to the
      network-layer visibility fixed this session)
- [ ] Carried forward from Session 17: build Windows Server VM
      (Hive_Primus), extend logging (WireGuard handshake polling,
      iptables drop logging on Eye_of_Terror), Docker/Vulhub host
      provisioning automation (deferred, revisit after more manual reps)
- [ ] Export/commit updated topology PNG reflecting Hive_Secundus and
      the wp2shell container as built/live (already updated in the
      `.drawio` source this session)