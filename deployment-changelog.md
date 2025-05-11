## [2025-05-08] Phase 1 Complete – ESXi Deployment + Lab Network Segmentation

- Mounted Dell PowerEdge R640 into Vevor open-frame rack  
- iDRAC9 configured via USB with static IP 192.168.4.120/24, gateway 192.168.4.1  
- Service Tag: GKSH1S2  
- Updated firmware via iDRAC:
  - SAS-RAID: SAS-RAID_Firmware_700GG_WN64_25.5.9.0001_A17_01  
  - iDRAC: iDRAC-with-Lifecycle-Controller-Firmware_RVDDR_WN64_7.00.00.181_A00  
  - BIOS: BIOS_J6D53_WN64_2.23.0  
- Created RAID 10 virtual disk across 4 drives using PERC H730P
- Installed VMware ESXi 8.0 Update 2 (Dell-custom ISO)  
- ESXi host static IP: 192.168.4.40  
- Hostname: Lionsgate ([https://Lionsgate/](https://Lionsgate/))  
- DNS: Primary 8.8.8.8, Alternate 1.1.1.1  
- Created secondary ESXi admin account: `custodian`  
- Management network isolated using vSwitch0 → `vmnic0` → Eero

### vSwitch-palace (Segmented Lab Virtual Switch)
- Created `vSwitch-palace` with no uplinks
- Created VLAN-tagged port groups:
  - PG-VLAN10 (vlan10) – Lab Clients
  - PG-VLAN20 (vlan20) – Lab Servers
  - PG-VLAN30 (vlan30) – DMZ
  - PG-VLAN40 (vlan40) – Red Team
  - PG-Custodes (vlan100) – Admin / CustodianNet
- Enabled promiscuous mode, MAC address changes, and forged transmits on VLANs 10–40
- PG-Custodes remained locked down (no promiscuous mode enabled)

### pfSense Prep
- Downloaded pfSense CE AMD64 ISO from Netgate ([https://www.pfsense.org/download/](https://www.pfsense.org/download/))
- Used 7-Zip to extract .gz-compressed installer ISO
- Deployed new VM `Rogal_Dorn` for pfSense
- Initially added 5 NICs for PG-VLAN10, 20, 30, 40, and PG-Custodes
- Attempted interface assignment with vmx0 (00:0c:29:40:2b:f8) but ran into installer limitations

---

## [2025-05-09] Rollback to Simplified Lab Core

- Removed unused NICs from `Rogal_Dorn` VM to simplify setup
- Retained 3 NICs:
  - NIC 1 → PG-Custodes (vlan100) → MAC: 00:0c:29:40:2b:f8
  - NIC 2 → PG-VLAN10 (vlan10) → MAC: 00:0c:29:40:2b:02
  - NIC 3 → VM Network (default on vSwitch0) → MAC: 00:0c:29:40:2b:0c
- Rebuilt pfSense using two-NIC layout for core functionality:
  - WAN → VM Network (via vSwitch0)
  - LAN → PG-VLAN10 (Lab Clients)
- Used VM Network MAC 00:0c:29:40:2b:0c for WAN
- Used PG-VLAN10 MAC 00:0c:29:40:2b:02 for LAN
- Completed pfSense CE installation successfully and reached initial configuration wizard
- Skipped cloud-based Netgate services and proceeded with local-only configuration
- Verified LAN connectivity to 192.168.1.1 from VLAN10

### Active Network Configuration

**vSwitch0 (Management & WAN)**
- Connected to `vmnic0` (Eero LAN)
- Port groups:
  - VM Network (active WAN interface for pfSense)
  - PG-WAN (VLAN 60, created for future use)

**vSwitch-palace (Segmented Lab)**
- PG-VLAN10 (vmx3 → 00:0c:29:40:2b:02)
- PG-Custodes (vmx1 → 00:0c:29:40:2b:f8)



Set 10.0.10.1

WAN vmx2 v4/DHCP4: 192.168.4.187/22
LAN vmx1 10.0.10.1/24
OPT 1 vmx0

admin/pfsense

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