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
  - PG-custodes (Admin / Custodes)
- Enabled Promiscuous Mode and MAC Forging on appropriate port groups
- Management and lab networking fully separated

Next up: Deploy pfSense and build core internal lab routing.


Dell PowerEdge R640 
iDRAC9
Service Tag: GKSH1S2
Static IP: 192.168.4.120
Static Gateway: 192.168.4.1
RAID controller (PERC H730P)

Updated the following R640 firmware via iDRAC:
 SAS-RAID_Firmware_700GG_WN64_25.5.9.0001_A17_01
 iDRAC-with-Lifecycle-Controller-Firmware_RVDDR_WN64_7.00.00.181_A00
 BIOS_J6D53_WN64_2.23.0


ESXi 8.0 Update 2 (Dell Custom ISO)?
ESXi 192.168.4.40 [https://192.168.4.40]
Primary DNS set to 8.8.8.8 and Alt 1.1.1.1
Hostname: Lionsgate [https://Lionsgate/]
 

Lionsgate is using vmnic0

Segmenting to keep vSwitch0 for management.
Going to create a new virtual switch for all other traffic.
vSwitch-palace
Creating port groups under vSwitch-palace:

Pg-vlan10 (vlan10) (Lab Clients)	 
Pg-vlan20 (vlan20) (Lab Servers)
Pg-vlan30 (vlan 30) (DMZ)
Pg-vlan40 (vlan 40) (Red Team)
Pg-custodes (vlan100) Admin / CustodianNet)
Enabled promiscuous, MAC address changes, and forged transmits on 10-40 (not 100 (custodes)

