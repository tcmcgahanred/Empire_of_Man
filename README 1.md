**Security Notice:**

> This documentation references internal-only, non-routable IP addresses and placeholder configurations. No credentials, license keys, or other directly-usable secrets are included in this repository. Where a real public IP or comparable identifier is operationally relevant, it has been redacted or generalized.

# 🔱 Empire_of_Man

> *Detection Engineering & Cybersecurity Skills Lab*
> *Originally conceived as STC-SOCaaS_v1, a SOC-as-a-Service prototype. Rescoped in 2026 to a focused, hands-on detection-engineering lab for skills development and portfolio/resume building.*

---

## 📜 Mission

Empire_of_Man is a homelab built to develop hands-on cybersecurity skills — detection engineering, network segmentation, purple-team exercises, and infrastructure administration — through direct practice rather than theory alone.

The project originally set out to become a SOC-as-a-Service (SOCaaS) platform for underserved organizations (small businesses, nonprofits, schools, 501(c)(3)s). That ambition hasn't been abandoned, but it has been deliberately **descoped and deferred** in favor of a narrower, more achievable goal: build real detection-engineering reps, document the process thoroughly, and revisit the broader MSSP/SOCaaS vision later if it still aligns with longer-term goals.

---

## 🛡️ Inspiration & Thematic Alignment

This project draws inspiration from the lore and aesthetic of Warhammer 40,000, aligning each system, VM, and security component with the roles and responsibilities of the Imperium of Man and its allies and enemies. Naming conventions — Rogal_Dorn, Lord_Commander_Guilliman, Alpharius, Eye_of_Terror — reflect a deliberate mapping between cybersecurity infrastructure and the eternal vigilance (and occasional treachery) of the 41st millennium.

"In the grim darkness of the far future, there is only war."

---

## 🧠 Philosophy

> This platform is a **skills-development lab**, not a production service.
> Its current mission is to build real, demonstrable detection-engineering and infrastructure capability — one validated technique, one fixed misconfiguration, one documented root cause at a time.

*"In vigilance, we serve. In segmentation, we shield. In automation, we strike."*
*— STC-SOCaaS_v1 Primer, Machine-Verified*

---

## 🧱 Infrastructure Overview

The lab is split across two physical hosts by role, plus a small cloud relay that solves a real-world connectivity constraint (CGNAT) rather than serving as a design choice for its own sake.

### EoM — "Empire of Man" (centralized, persistent)

| Element       | Value                              |
|---------------|-------------------------------------|
| Chassis       | Dell PowerEdge R640                 |
| Hypervisor    | VMware ESXi 8.0U3e (free, no expiration) |
| Role          | Defensive infrastructure: firewall, SIEM, future NSM |

### VS — "Vengeful Spirit" (mobile, disposable)

| Element       | Value                              |
|---------------|-------------------------------------|
| Platform      | Lenovo laptop, Windows 11 Pro, VMware Workstation Pro |
| Role          | Attacker tooling and victim/target machines |

### Remote Access — "Eye_of_Terror" (AWS EC2)

| Element       | Value                              |
|---------------|-------------------------------------|
| Instance      | AWS EC2, t3.micro, Ubuntu LTS       |
| Role          | WireGuard relay, solving inbound connectivity behind Carrier-Grade NAT (CGNAT) |

Both EoM (`Rogal_Dorn`) and VS dial **outbound** to this relay rather than accepting inbound connections directly — CGNAT on the home ISP connection makes direct inbound access structurally impossible without this (or a comparable) workaround.

---

## 🛠️ Core Capabilities (Current)

- pfSense firewall/router (`Rogal_Dorn`) with VLAN-segmented internal networks
- WireGuard-based remote access, relayed through a small EC2 instance to work around CGNAT
- Wazuh SIEM (`Lord_Commander_Guilliman`) with Sysmon-based Windows endpoint telemetry
- Kali Linux attacker tooling on both hosts (`Horus` on VS, `Alpharius` on EoM)
- Detection validation against MITRE ATT&CK-mapped techniques using Atomic Red Team

## 🛠️ Capabilities (Planned)

- Security Onion (`Valdor`) for network security monitoring (Suricata + Zeek)
- Active Directory domain controller + BloodHound for attack-path analysis
- Original Suricata detection rules validated against real, disclosed CVEs
- TheHive/Cortex for SOAR-style case management (longer-term, if MSSP scope is revisited)

---

## 📦 Current Scope

- Dell R640 running ESXi 8.0U3e, segmented via `vSwitch-palace`
- pfSense firewall VM (`Rogal_Dorn`) providing routing, DHCP, segmentation, and WireGuard
- VLAN-segmented port groups for SIEM and future NSM/attacker tooling
- Wazuh SIEM (`Lord_Commander_Guilliman`) ingesting Sysmon telemetry from a Windows target
- WireGuard remote access via a self-hosted EC2 relay (`Eye_of_Terror`), CGNAT-safe by design
- Lab credentials managed exclusively in a password manager — never committed to this repository

---

## 📁 Project Structure (Empire_of_Man/)

- `configs/` — System configuration files for VMs, appliances, and networking
  - `Appliances/pfsense/` — pfSense configuration and interface assignments
  - `VMs/` — Provisioning scripts, netplan configs, and host settings
  - `Networking/` — Topology definitions, port group mappings, VLAN plans
- `diagrams/` — Topology maps and architectural diagrams
- `logs/` — Build logs and recorded test activity (master changelog)
- `playbooks/` — Incident response procedures and detection engineering documentation
- `scripts/` — Shell scripts for provisioning, hardening, and admin automation

---

## 🚀 Roadmap

- [x] Segment hypervisor traffic and establish VLANs
- [x] Deploy pfSense and configure WAN/LAN/OPT interfaces
- [x] Stand up Wazuh SIEM with validated Sysmon-based detection
- [x] Solve remote access under CGNAT via a self-hosted WireGuard relay
- [ ] Stand up Security Onion (Valdor) for network security monitoring
- [ ] Stand up an Active Directory environment and run BloodHound for attack-path analysis
- [ ] Write and validate an original Suricata rule against a real, disclosed CVE
- [ ] Re-evaluate the broader SOCaaS/MSSP vision once core skills-development goals are met

---

*Note: this project's history includes an earlier build era using ChatGPT before migrating to Claude. The master changelog in `logs/` preserves that full history, credentials scrubbed, for continuity.*
