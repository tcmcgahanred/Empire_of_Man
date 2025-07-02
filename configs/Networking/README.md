## 🔐 Segmentation Strategy

| Port Group Name    | VLAN ID | Purpose                                      | Assigned Systems                                                            |
| ------------------ | ------- | -------------------------------------------- | --------------------------------------------------------------------------- |
| `pg-wan`           | 60      | External ingress/egress interface (WAN)      | `Rogal_Dorn` (WAN interface)                                                |
| `pg-custodes`      | 100     | Command, control, and routing infrastructure | `Rogal_Dorn` (LAN), `Emperor_of_Mankind` (admin node)                       |
| `pg-administratum` | 10      | Security appliance & log processing network  | `Sanguinius` (Wazuh Manager), future: `Security Onion`, `TheHive`, `Cortex` |
