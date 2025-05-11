# 🛡️ SOC-as-a-Service Platform (Prototype)

This project documents the design, architecture, and deployment of a blue team–focused SOC platform, developed as the foundation for a future **SOC-as-a-Service (SOCaaS)** company. The goal is to build a scalable, modular, and secure virtual environment capable of providing **24/7 cybersecurity monitoring, consultation, and incident response** services to small organizations, such as 501(c)(3) nonprofits and other under-resourced entities.

---

## 🎯 Vision

To establish a lean, professional-grade SOC platform that can:
- Support a small cybersecurity business (< 50 employees)
- Serve multiple clients across a region via remote telemetry ingestion
- Deliver SIEM, IDS, SOAR, and IR workflows affordably and reliably
- Provide 24/7 detection, monitoring, and analyst response

---

## 🧱 Core Architecture

### Host System
- **Dell PowerEdge R640**
  - Dual Xeon CPUs
  - 64–128GB RAM
  - Quad-port i350 NIC
  - VMware ESXi 8.0
  - Mounted in Vevor open-frame rack

### Network Topology
- `vSwitch0`: Management / Eero LAN
- `vSwitch-palace`: Segmented internal SOC traffic (no uplinks)
- `pfSense` (Rogal_Dorn) as central firewall and router

### VLAN Port Groups
| VLAN ID | Port Group     | Purpose                      |
|---------|----------------|------------------------------|
| 10      | PG-VLAN10      | Core SOC services            |
| 100     | PG-Custodes    | Admin-only access (C2 node)  |

---

## 🧰 Platform VMs

| VM Name           | Role                             | Notes                                     |
|-------------------|----------------------------------|--------------------------------------------|
| `Rogal_Dorn`      | pfSense (router/firewall)        | Segmentation and external connectivity    |
| `SecurityOnion`   | IDS/NIDS                         | Suricata/Zeek, full packet analysis       |
| `Wazuh`           | SIEM + HIDS                      | Remote log collection, alerting, asset inventory |
| `TheHive`         | IR case management               | Analyst workflows, alert triage           |
| `Cortex`          | SOAR automation                  | Automated enrichment, active response     |
| `Throne_Operator` | Admin VM                         | Secure analyst/admin GUI workstation      |

---

## 🔐 Security Model

- **No red team activity generated locally**
- Strict segmentation between internal services and external ingress
- External telemetry expected via secure VPN, Syslog/TLS, or agent pipelines
- All administrative activity flows through `PG-Custodes` only
- pfSense enforces VLAN boundaries and external visibility

---

## 🧠 Business Prototype Goals

- Serve multiple small clients (nonprofits, small clinics, K-12, etc.)
- Deploy lightweight telemetry kits to customer networks (agents, sensors, Pi-based collectors)
- Deliver:
  - 24/7 alerting and SOC visibility
  - Customized dashboards and metrics
  - On-call incident response and escalation workflows
  - Threat intelligence and vulnerability context

---

## 📁 Git Repo Structure



## 📁 Git Repo Layout

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

## 📅 Deployment Phases

| Phase | Description                                       |
|--------|---------------------------------------------------|
| 1      | Rack, power, and configure base server            |
| 2      | Deploy ESXi and create vSwitch segmentation       |
| 3      | Install pfSense and establish VLAN topology       |
| 4      | Deploy Wazuh and enable external agent ingestion  |
| 5      | Stand up Security Onion and configure flow analysis |
| 6      | Deploy TheHive and Cortex; integrate with Wazuh   |
| 7      | Deploy and harden Throne_Operator admin VM        |
| 8      | Begin onboarding of external telemetry sources    |
| 9      | Build response playbooks and customer reporting flow |

---

## 🌍 Future Integration Targets

- Wazuh agents on external networks (via VPN or TLS)
- Passive traffic collectors (e.g., Zeek sensors on Raspberry Pi)
- SOAR playbooks mapped to NIST and CIS Controls
- Threat intel ingestion via Cortex analyzers
- Lightweight alerting dashboards for client access

---

## 🚀 Strategic Outcome

This lab is the operational blueprint for launching a real-world, affordable SOC-as-a-Service business — one built to protect small organizations who need it most, without enterprise overhead.
