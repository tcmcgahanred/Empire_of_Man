| Component                   | IP Address     | Username         | Notes                                         |
|----------------------------|----------------|------------------|-----------------------------------------------|
| iDRAC (Dell R640)          | 192.168.4.120  | root             | Out-of-band management                        |
| ESXi Host (Lionsgate)      | 192.168.4.40   | root / custodian | Hypervisor Web UI                             |
| pfSense WAN (Rogal_Dorn)   | 192.168.4.187  | admin            | DHCP from Eero via VM Network                 |
| pfSense LAN (Rogal_Dorn)   | 10.0.10.1      | admin            | WebGUI (accessible from PG-VLAN10 only)       |
| pfSense OPT1 (CustodesNet) | 10.0.100.1     | admin            | Reserved for admin access (PG-Custodes)       |
