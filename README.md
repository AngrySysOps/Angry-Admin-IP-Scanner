## Angry Admin IP Scanner v1.0.0

The first public release of **Angry Admin IP Scanner** is here.

Built for admins who are tired of guessing, tired of messy spreadsheets, and tired of wasting time checking address space by hand.

This release gives you a fast, clean way to scan IP ranges and identify what looks used, reserved, or free using multiple detection methods in one desktop tool.

### What it does
- Scans target ranges using:
  - Ping
  - Reverse DNS
  - ARP
  - TCP Connect on port 80
  - UDP on port 53
- Supports:
  - CIDR notation
  - Full start-to-end ranges
  - Count-based ranges
- Displays:
  - Used
  - DNS reserved
  - Free
- Exports results to:
  - CSV
  - TXT
  - HTML
- Includes print support

### Supported input examples
- `10.10.10.0/24`
- `10.10.10.123-10.10.10.200`
- `10.10.10.123-20`

### Important notes
- On first launch, you must accept the disclaimer before using the application.
- If you tick **Don't show this again**, the disclaimer will be skipped on future launches.
- ARP checks are intended for local network use.
- Scan results can vary depending on DNS, firewall rules, endpoint behavior, and network design.

### Built with
- Python
- PyQt5
- QThread
- ThreadPoolExecutor
- dnspython

### Disclaimer
This software is provided **as is** without warranty of any kind.  
By using **Angry Admin IP Scanner**, you accept full responsibility for its use.  
The developer is not liable for any damages, losses, or legal issues arising from its use.

© 2025 Angry Admin  
[www.angrysysops.com](https://www.angrysysops.com)
