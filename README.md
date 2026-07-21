**Security Notice:**

> This documentation references internal-only, non-routable IP addresses and placeholder configurations. No credentials, license keys, or other directly-usable secrets are included in this repository. Where a real public IP or comparable identifier is operationally relevant, it has been redacted or generalized.

# 🔱 Empire_of_Man

> *Detection Engineering & Cybersecurity Skills Lab*

---

## 📜 Mission

Empire_of_Man is a homelab built to develop hands-on cybersecurity skills — detection engineering, network segmentation, purple-team exercises, and infrastructure administration — through direct practice rather than theory alone.

---

## 🛡️ Inspiration & Thematic Alignment

This project draws inspiration from the lore and aesthetic of Warhammer 40,000, aligning each system, VM, and security component with the roles and responsibilities of the Imperium of Man and its allies and enemies. Naming conventions — Rogal_Dorn, Lord_Commander_Guilliman, Alpharius, Eye_of_Terror — reflect a deliberate mapping between cybersecurity infrastructure and the eternal vigilance (and occasional treachery) of the 41st millennium.

"In the grim darkness of the far future, there is only war."

---

## 🧠 Philosophy

> This platform is built to develop real, demonstrable detection-engineering and infrastructure capability — one validated technique, one fixed misconfiguration, one documented root cause at a time.

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
| Role          | Defensive infrastructure: firewall, SIEM, network security monitoring |

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

## 🗺️ Topology

<img width="962" height="832" alt="topology_v20260720" src="https://github.com/user-attachments/assets/1c2a38b2-fa4b-45b9-bf6a-23c1b014956f" />


*Maintained in [draw.io](https://app.diagrams.net/); source file at [`diagrams/empire_of_man_topology.drawio`](diagrams/empire_of_man_topology.drawio).*

---

## 🛠️ Core Capabilities (Current)

- pfSense firewall/router (`Rogal_Dorn`) with VLAN-segmented internal networks
- WireGuard-based remote access, relayed through a small EC2 instance to work around CGNAT, with host-level logging (SSH auth, system events) on the relay itself
- Wazuh SIEM (`Lord_Commander_Guilliman`) with Sysmon-based Windows endpoint telemetry
- Security Onion (`Valdor`) for network security monitoring (Suricata + Zeek)
- Kali Linux attacker tooling on both hosts (`Horus` on VS, `Alpharius` on EoM)
- Detection validation against MITRE ATT&CK-mapped techniques using Atomic Red Team

## 🛠️ Capabilities (Planned)

- Active Directory domain controller + BloodHound for attack-path analysis
- Original Suricata detection rules validated against real, disclosed CVEs
- TheHive/Cortex for SOAR-style case management (longer-term)

---

## 📦 Current Scope

- Dell R640 running ESXi 8.0U3e, segmented via `vSwitch-palace` into two VLANs (`PG-Ultramarines`, `PG-Custodes`)
- pfSense firewall VM (`Rogal_Dorn`) providing routing, DHCP, segmentation, and WireGuard
- Wazuh SIEM (`Lord_Commander_Guilliman`) ingesting Sysmon telemetry from a Windows target
- Security Onion (`Valdor`) providing network security monitoring on `PG-Custodes`
- WireGuard remote access via a self-hosted EC2 relay (`Eye_of_Terror`), CGNAT-safe by design and logged into the SIEM
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
- [x] Stand up Security Onion (Valdor) for network security monitoring
- [ ] Stand up an Active Directory environment and run BloodHound for attack-path analysis
- [ ] Write and validate an original Suricata rule against a real, disclosed CVE
*Note: the master changelog in `logs/` preserves the full build history, credentials scrubbed, for continuity.*
