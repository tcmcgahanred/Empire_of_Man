# empire_of_man — Master Build Log & Changelog

This document consolidates the full project history: the original
2025 SOCaaS/MSSP-era infrastructure work (R640 + pfSense + Ubuntu, done
via ChatGPT) and the 2026 detection-engineering-focused rebuild (done via
Claude). Cleaned up and de-duplicated from source notes — no content
removed, only reorganized and duplicate sections collapsed.

---

# PART 1 — 2025: Original STC-SOCaaS_v1 / Empire_of_Man Build (R640, pfSense)

## [2025-05-08] Phase 1 — ESXi Deployment + Lab Network Segmentation

### Hardware / Firmware
- Mounted Dell PowerEdge R640 into Vevor open-frame rack
- Service Tag: `GKSH1S2`
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
  Hypervisor, Key `J52V8-8V10M-28PA1-L2RA2-2HY6U`, Expiration: Never.**

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