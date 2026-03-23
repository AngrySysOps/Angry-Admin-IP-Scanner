## Download

The latest public build of **Angry Admin IP Scanner** is available on GitHub Releases.

### Current platform targets
- Windows executable
- Linux Debian package: `angry-admin-ipscanner_1.0_amd64.deb`
- Linux RPM package: `angry-admin-ipscanner-1.0-1.x86_64.rpm`
- macOS application bundle and ZIP archive

### Build the Linux packages
Run the Linux packaging script on a Linux host that has `dpkg-deb` and `rpmbuild` installed:

```bash
./scripts/build_linux_packages.sh
```

Artifacts are written to `dist/linux/`.

### Build the macOS app
Run the macOS packaging script on macOS:

```bash
./scripts/build_macos_app.sh
```

Artifacts are written to `dist/macos/`.

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
- ARP checks now use the native tooling available on Windows, Linux, and macOS.
- Some scan methods may be affected by firewall rules, host configuration, or network policy.

### Legal Disclaimer
This software is provided **as is**, without warranty of any kind, express or implied.  
By using **Angry Admin IP Scanner**, you accept full responsibility for its use.  
The author is not liable for any damages, losses, or legal issues arising from the use of this software.

### Project Info
**Angry Admin IP Scanner** is built with **Python** and **PyQt5**, using a multi-threaded design to keep the interface responsive during scans.

Website: [www.angrysysops.com](https://www.angrysysops.com)
