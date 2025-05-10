# Cybersecurity Homelab and Threat Range

This project documents the architecture, design, and phased execution of a home-based cyber range, hosted on a Dell PowerEdge R640 and virtualized using VMware. It combines a traditional blue team lab, an offensive test range, and passive home network monitoring while preserving strict segmentation from personal and family systems.

---

## 🌟 Project Goals

- Build a modular, virtualized cybersecurity lab for blue/red team training
- Monitor and analyze home network traffic safely
- Segregate the family LAN, gaming PC, and cyber lab securely
- Enable remote lab access using a hardened AWS jump server
- Integrate TheHive and Cortex as the SOAR platform
- Document all deployments, configurations, and security boundaries using Git

---

## 🧱 Physical & Virtual Infrastructure

### Server
- **Dell PowerEdge R640**
  - Dual Xeon CPUs
  - 64–128GB RAM
  - Quad-port i350 NIC
  - VMware ESXi hypervisor

### Networking
- pfSense VM (core firewall/router)
- Virtual switches and VLANs inside VMware
- Optional: Managed physical switch for VLAN trunking later

### Key VLANs
| VLAN ID | Purpose            |
|---------|--------------------|
| 10      | Lab Clients        |
| 20      | Lab Servers        |
| 30      | DMZ (Honeypots)    |
| 40      | C2/Red Team Net    |
| 50      | Gaming PC VLAN     |
| 100     | Home LAN (isolated)|

### Key VMs
- pfSense
- Windows 10 / 11 endpoints
- Active Directory & DNS
- Kali Linux (Red Team)
- Security Onion (IDS/NIDS)
- Wazuh (SIEM)
- TheHive (Case Management)
- Cortex (SOAR Automation)
- Range Admin Workstation (internal jump VM)

---

## 🌐 Segmentation Strategy

- **Home network**: Isolated, monitored only via SPAN port or passive TAP
- **Gaming rig**: On separate VLAN (50), no lab access; no lab tooling or scanning allowed
- **Lab range**: Internal VLANs routed and firewalled by pfSense
- **Remote access**: AWS EC2 jump box (Ubuntu or Windows Server), hardened and optionally VPN-connected to lab

---

## 🔐 Security Practices

- pfSense as centralized access control (stateful firewall rules per VLAN)
- pfBlockerNG for known-bad IP/DNS blocking
- Suricata (via Security Onion) for active threat detection
- No shared infrastructure or tooling between personal and lab systems
- Admin access from dedicated VM or cloud jump box only

---

## 📁 Git Repo Structure (Planned)

```
cyber-range-docs/
├── README.md                            # Overview of the entire lab environment
├── deployment-changelog.md             # Time-stamped build log (you’re updating this now)
├── esxi-hardening.md                   # Optional: notes on securing the hypervisor
│
├── diagrams/                           # Network topology and design files
│   ├── lab-topology.drawio
│   └── vlan-layout.drawio
│
├── configs/                            # Configuration backups or notes for appliances
│   ├── pfSense/
│   │   └── interfaces-config.xml       # (once exported)
│   ├── Suricata/
│   ├── Wazuh/
│   ├── SecurityOnion/
│   └── ESXi/
│       └── host-config-backup.txt
│
├── playbooks/                          # Test cases, attack simulations, blue team responses
│   ├── test-cases.md
│   └── pfSense-firewall-baseline.md
│
├── logs/                               # Logging behaviors, network captures, findings
│   └── notes-on-detections.md
│
└── ISOs/                               # (Optional) Folder name reference only — actual ISOs not stored in Git
    └── README.md                       # Track which ISO versions were uploaded and where

```

---

## 🗓️ Execution Phases

| Phase | Description                                |
|--------|--------------------------------------------|
| 0      | Rack and power on server                   |
| 1      | Install VMware ESXi                        |
| 2      | Deploy pfSense with basic WAN/LAN setup    |
| 3      | Build vSwitches and VLAN port groups       |
| 4      | Deploy client/server/DMZ VMs               |
| 5      | Deploy IDS and SIEM stack                  |
| 6      | Build Range Admin VM                       |
| 7      | Harden and test AWS jump server            |
| 8      | Connect cloud jump box to lab              |
| 9      | Monitor home network via SPAN              |
| 10     | Begin threat emulation + detection testing |
| 11     | Deploy TheHive and Cortex for SOAR         |

---

## 🧠 Next Steps
- Finalize draw.io topology
- Deploy core infrastructure (pfSense + VLANs)
- Build Git-based documentation pipeline
- Integrate TheHive + Cortex with lab alerting stack
- Begin tracking configurations and attack test cases
