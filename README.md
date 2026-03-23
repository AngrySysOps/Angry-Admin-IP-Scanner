## Download

The latest public build of **Angry Admin IP Scanner** is available on GitHub Releases.

### Latest Release
- [Download the latest release](https://github.com/AngrySysOps/Angry-Admin-IP-Scanner/releases/latest)

### Current Release
- [Angry Admin IP Scanner v1.0.0](https://github.com/AngrySysOps/Angry-Admin-IP-Scanner/releases/tag/v1.0.0)

### What’s included
The release package includes the Windows executable for **Angry Admin IP Scanner**.

### Supported scan methods
- Ping
- Reverse DNS
- ARP
- TCP Connect (port 80)
- UDP (port 53)

### Supported input formats
- CIDR notation  
  Example: `10.10.10.0/24`

- Full range  
  Example: `10.10.10.123-10.10.10.200`

- Count-based range  
  Example: `10.10.10.123-20`

### Export options
Scan results can be exported to:
- CSV
- TXT
- HTML

### Notes
- On first launch, the application displays a disclaimer that must be accepted before use.
- If **Don't show this again** is selected, the disclaimer will not appear on future launches.
- ARP-based checks are only useful on local networks.
- Some scan methods may be affected by firewall rules, host configuration, or network policy.

### Legal Disclaimer
This software is provided **as is**, without warranty of any kind, express or implied.  
By using **Angry Admin IP Scanner**, you accept full responsibility for its use.  
The author is not liable for any damages, losses, or legal issues arising from the use of this software.

### Project Info
**Angry Admin IP Scanner** is built with **Python** and **PyQt5**, using a multi-threaded design to keep the interface responsive during scans.

Website: [www.angrysysops.com](https://www.angrysysops.com)
