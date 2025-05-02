# Cybersecurity Homelab and Threat Range

This project documents the architecture, design, and phased execution of a home-based cyber range, hosted on a Dell PowerEdge R640 and virtualized using VMware. It combines a traditional blue team lab, an offensive test range, and passive home network monitoring while preserving strict segmentation from personal and family systems.

## 🎯 Project Goals

- Build a modular, virtualized cybersecurity lab for blue/red team training
- Monitor and analyze home network traffic safely
- Segregate the family LAN, gaming PC, and cyber lab securely
- Enable remote lab access using a hardened AWS jump server
- Implement full MITRE ATT&CK detection mapping across host and network
- Document all deployments, configurations, and security boundaries using Git

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

| VLAN ID | Purpose             |
|---------|---------------------|
| 10      | Lab Clients         |
| 20      | Lab Servers         |
| 30      | DMZ (Honeypots)     |
| 40      | C2/Red Team Net     |
| 50      | Gaming PC VLAN      |
| 100     | Home LAN (isolated) |

### Key VMs

- pfSense
- Windows 10 / 11 endpoints
- Active Directory & DNS
- Kali Linux (Red Team)
- **Security Onion** (NSM/IDS/Zeek/Suricata/SOC stack)
- **Wazuh Stack** (host-based XDR with ELK and MITRE alignment)
- Range Admin Workstation (internal jump VM)

## 🌐 Segmentation Strategy

- **Home network**: Isolated, monitored only via SPAN port or passive TAP
- **Gaming rig**: On separate VLAN (50), no lab access; no lab tooling or scanning allowed
- **Lab range**: Internal VLANs routed and firewalled by pfSense
- **Remote access**: AWS EC2 jump box (Ubuntu or Windows Server), hardened and optionally VPN-connected to lab

## 🔐 Detection & Monitoring Stack

| Tool             | Role                                                 |
|------------------|------------------------------------------------------|
| **pfSense**      | Firewall, router, VLAN segmentation                  |
| **Security Onion** | NSM, IDS, Zeek, Suricata, Kibana, Sguil             |
| **Wazuh**        | Host-based detection, MITRE ATT&CK mapping, FIM, vulnerability detection, built on ELK |
| **SPAN/TAP**     | Feeds Security Onion from home LAN for passive monitoring |

## 📁 Git Repo Structure (Planned)

cyber-range-docs/
├── diagrams/
│ ├── lab-topology.drawio
│ └── vlan-layout.drawio
├── configs/
│ ├── pfSense/
│ ├── SecurityOnion/
│ └── Wazuh/
├── playbooks/
│ └── test-cases.md
├── logs/
│ └── deployment-changelog.md
└── README.md


## 📅 Execution Phases

| Phase | Description                                 |
|-------|---------------------------------------------|
| 0     | Rack and power on server                    |
| 1     | Install VMware ESXi                         |
| 2     | Deploy pfSense with basic WAN/LAN setup     |
| 3     | Build vSwitches and VLAN port groups        |
| 4     | Deploy client/server/DMZ VMs                |
| 5     | Deploy Security Onion                       |
| 6     | Deploy Wazuh stack with ELK + MITRE mapping |
| 7     | Build Range Admin VM                        |
| 8     | Harden and test AWS jump server             |
| 9     | Connect cloud jump box to lab               |
| 10    | Monitor home network via SPAN               |
| 11    | Begin threat emulation + detection testing  |

## 🧠 Next Steps

- Finalize draw.io topology
- Deploy core infrastructure (pfSense + VLANs)
- Build Git-based documentation pipeline
- Deploy Security Onion and Wazuh with lab logging inputs
- Start tracking configurations and attack test cases using MITRE tags
