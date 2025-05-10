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
