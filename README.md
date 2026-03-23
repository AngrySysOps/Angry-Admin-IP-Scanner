## Download

The latest public build of **Angry Admin IP Scanner** is available on GitHub Releases.

### Current platform targets
- Windows executable
- Linux Debian package: `angry-admin-ipscanner_1.0_amd64.deb`
- Linux RPM package: `angry-admin-ipscanner-1.0-1.x86_64.rpm`
- macOS application bundle and ZIP archive

### Install from release packages
- `angry-admin-ipscanner-1.0-1.x86_64.rpm`  
  RPM package for Linux. Install using: `sudo rpm -i angry-admin-ipscanner-1.0-1.x86_64.rpm`.

- `angry-admin-ipscanner_1.0_amd64.deb`  
  DEB package for Debian/Ubuntu systems. Install using: `sudo dpkg -i angry-admin-ipscanner_1.0_amd64.deb`.

- `AngryAdminIPScanner-macos.zip`  
  macOS application archive. Install by opening the ZIP, then drag `Angry Admin IP Scanner.app` into `Applications`.

### How to create the Linux packages
Build the Linux packages on a Linux machine.

#### 1. Install the required system packages
On Debian or Ubuntu:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip dpkg-dev rpm patchelf binutils
```

On Fedora, RHEL, Rocky, or AlmaLinux:

```bash
sudo dnf install -y python3 python3-pip rpm-build dpkg-devtools patchelf binutils
```

#### 2. Clone the repository and enter the project folder
```bash
git clone https://github.com/AngrySysOps/Angry-Admin-IP-Scanner.git
cd Angry-Admin-IP-Scanner
```

#### 3. Run the Linux build script
```bash
./scripts/build_linux_packages.sh
```

#### 4. Collect the generated files
The script writes the final artifacts to `dist/linux/`:
- `dist/linux/angry-admin-ipscanner_1.0_amd64.deb`
- `dist/linux/angry-admin-ipscanner-1.0-1.x86_64.rpm`

#### 5. Optional install tests
To install the Debian package:

```bash
sudo dpkg -i dist/linux/angry-admin-ipscanner_1.0_amd64.deb
sudo apt-get install -f
```

To install the RPM package:

```bash
sudo rpm -ivh dist/linux/angry-admin-ipscanner-1.0-1.x86_64.rpm
```

### How to create the macOS app
Build the macOS version on a Mac.

#### 1. Install command line tools
```bash
xcode-select --install
```

#### 2. Clone the repository and enter the project folder
```bash
git clone https://github.com/AngrySysOps/Angry-Admin-IP-Scanner.git
cd Angry-Admin-IP-Scanner
```

#### 3. Run the macOS build script
```bash
./scripts/build_macos_app.sh
```

#### 4. Collect the generated files
The script writes the final artifacts to `dist/macos/`:
- `dist/macos/Angry Admin IP Scanner.app`
- `dist/macos/AngryAdminIPScanner-macos.zip`

### Release automation
- Pushing a Git tag builds the Linux and macOS artifacts and uploads them to the matching GitHub Release, creating the release automatically if it does not exist yet.
- Publishing a GitHub Release also rebuilds the artifacts and re-attaches the generated `.deb`, `.rpm`, `.app`, and macOS ZIP outputs to that release.
- Manual workflow runs require a `release_tag` input so the workflow knows which GitHub Release should receive the generated files.
- The macOS workflow installs Pillow so the existing `.ico` file can be converted during bundling, and the Linux workflow installs the Qt/XCB/GStreamer/PulseAudio libraries needed by PyInstaller on GitHub-hosted runners.

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
- Build the Linux packages on Linux and the app bundle on macOS; the scripts are designed for native packaging on each platform.

### Legal Disclaimer
This software is provided **as is**, without warranty of any kind, express or implied.  
By using **Angry Admin IP Scanner**, you accept full responsibility for its use.  
The author is not liable for any damages, losses, or legal issues arising from the use of this software.

### Project Info
**Angry Admin IP Scanner** is built with **Python** and **PyQt5**, using a multi-threaded design to keep the interface responsive during scans.

Website: [www.angrysysops.com](https://www.angrysysops.com)
