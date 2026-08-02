# empire_of_man — 2025 Build Archive (STC-SOCaaS_v1)

**Status: ARCHIVED. This file is historical and is not updated.**

This covers the original 2025 SOCaaS/MSSP-era infrastructure work
(R640 + pfSense + Ubuntu) that preceded the 2026 pivot to a
detection-engineering-focused lab. Preserved for reference/continuity
only. For active build history, see `deployment-changelog-2026.md`.

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
