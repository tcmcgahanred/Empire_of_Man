## 🔐 Segmentation Strategy

| VLAN ID | Port Group     | Purpose                        |
|---------|----------------|--------------------------------|
| 10      | PG-VLAN10      | SOC core services              |
| 60      | PG-WAN         | WAN uplink to Eero             |
| 100     | PG-Custodes    | Admin-only command VLAN        |

Traffic segmentation and isolation enforced by `Rogal_Dorn` (pfSense). VLANs are not bridged unless explicitly routed.