Below is a clean and structured **pfSense Initial Configuration Checklist** 

---

## 📜 `pfsense_initial_setup.md`

### **Title:** pfSense Baseline Configuration Checklist

**System:** *Rogal\_Dorn*
**Date:** 2025-05-12
**Network Role:** Border and segmentation firewall for STC-SOCaaS\_v1 prototype

---

### ✅ **System Initialization**

* [x] Set admin password
* [x] Verified access via `https://10.0.10.1`
* [x] Acknowledged self-signed TLS warning and logged in

---

### ⚙️ **Interface Configuration**

* [x] Verified **WAN** assigned to external (`192.168.4.x`)
* [x] Verified **LAN** assigned to `pg-custodes` virtual switch
* [x] Confirmed LAN interface IP: `10.0.10.1/24`
* [ ] Renamed interfaces for clarity (`LAN → CustodesNet`, etc.)

---

### 🌐 **DHCP & IP Management**

* [x] Enabled DHCP server on LAN
* [x] Configured range: `10.0.10.100 – 10.0.10.200`
* [ ] Reserved static leases for key nodes (e.g., *Emperor\_of\_Mankind*, Wazuh, Security Onion)

---

### 🔥 **Firewall Rules**

* [x] Confirmed default allow rule on **LAN → any**
* [ ] Created custom rules for segmentation or logging
* [ ] Enabled logging on critical rule paths (optional)

---

### 🧠 **System Services**

* [ ] Verified NTP settings (under **System > General Setup**)
* [ ] Verified DNS Resolver (under **Services > DNS Resolver**)
* [ ] Enabled pfBlockerNG (optional, for threat intelligence/blocklists)
* [ ] Created backup of current config

---

### 🛡️ **Security Considerations**

* [ ] Disabled WAN-side admin access (unless remote access is needed and secured)
* [ ] Considered adding GeoIP blocking or rate-limiting
* [ ] Set GUI idle timeout (System > Advanced > Admin Access)

---

### 🧰 **Optional Enhancements**

* [ ] Create internal Certificate Authority (System > Cert Manager)
* [ ] Create VPN service (OpenVPN / WireGuard)
* [ ] Enable syslog or remote logging to *Emperor\_of\_Mankind*


