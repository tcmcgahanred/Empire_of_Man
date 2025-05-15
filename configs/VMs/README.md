| VM Name            | Role              | OS           | IP Address                | Interfaces             | Port Group                          |
|:-------------------|:------------------|:-------------|:--------------------------|:-----------------------|:------------------------------------|
| Rogal_Dorn         | Firewall          | pfSense      | 192.168.4.187 / 10.0.10.1 | vmx0 (WAN), vmx1 (LAN) | WAN = VM Network, LAN = pg-custodes |
| Emperor_of_Mankind | Admin Workstation | Ubuntu 22.04 | 10.0.10.10                | ens34                  | pg-custodes                         |






| Tool                                  | Purpose                                       | Installation Method   | Status                   |
|:--------------------------------------|:----------------------------------------------|:----------------------|:-------------------------|
| fail2ban                              | Brute-force protection for SSH                | apt                   | Active                   |
| ufw                                   | Firewall management                           | apt                   | Enabled with SSH allowed |
| open-vm-tools / open-vm-tools-desktop | VMware integration (clipboard, display, etc.) | apt                   | Installed                |
| zsh                                   | Enhanced shell experience                     | apt                   | Installed                |
| git                                   | Version control                               | apt                   | Installed and configured |
| curl / wget                           | Command-line HTTP/FTP downloads               | apt                   | Installed                |
| htop                                  | Interactive process monitoring                | apt                   | Installed                |