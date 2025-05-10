## [2025-05-08] Phase 1 Complete – ESXi Deployment + Lab Network Segmentation

- Mounted Dell PowerEdge R640 into Vevor open-frame rack
- Configured iDRAC via USB and set static IP
- Updated BIOS, iDRAC, RAID controller (H730P), and Lifecycle Controller firmware
- Created RAID 10 virtual disk across 4 drives
- Installed VMware ESXi 8.0.2 using Dell-customized ISO
- Assigned static IP to vmnic0 for management via Eero LAN
- Created second admin account: `custodian`
- Logged into ESXi web GUI successfully via `https://<host-ip>`
- Created isolated vSwitch `vSwitch-palace` for lab segmentation
- Added VLAN-tagged port groups:
  - PG-VLAN10 (Clients)
  - PG-VLAN20 (Servers)
  - PG-VLAN30 (DMZ)
  - PG-VLAN40 (Red Team / C2)
  - PG-VLAN100 (Admin / Custodes)
- Enabled Promiscuous Mode and MAC Forging on appropriate port groups
- Management and lab networking fully separated

Next up: Deploy pfSense and build core internal lab routing.
