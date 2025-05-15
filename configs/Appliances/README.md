| Component            | Category  | Config Path                   | Description                                          |
| -------------------- | --------- | ----------------------------- | ---------------------------------------------------- |
| `Emperor_of_Mankind` | VM        | `configs/VMs/`                | Ubuntu 22.04 admin/analyst workstation               |
| `Rogal_Dorn`         | Appliance | `configs/Appliances/pfsense/` | pfSense firewall for routing, DHCP, segmentation     |
| `pg-custodes`        | Network   | `configs/Networking/`         | Internal LAN port group connected to trusted enclave |
| `vSwitch-palace`     | Network   | `configs/Networking/`         | ESXi virtual switch used for segmentation            |


| Component           | Category  | Intended Config Path                | Description                                  |
| ------------------- | --------- | ----------------------------------- | -------------------------------------------- |
| `Wazuh`             | Appliance | `configs/Appliances/wazuh/`         | SIEM for log aggregation and alerting        |
| `Security Onion`    | Appliance | `configs/Appliances/securityonion/` | Passive NIDS and packet inspection           |
| `TheHive`           | Appliance | `configs/Appliances/thehive/`       | Incident case management and Cortex SOAR     |
| `Cortex`            | Appliance | `configs/Appliances/thehive/`       | Observable enrichment and automation backend |
| VLAN 10/20 Segments | Network   | `configs/Networking/`               | Segmentation for sensors, DMZ, and red team  |


