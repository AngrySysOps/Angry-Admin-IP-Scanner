#!/usr/bin/env python3
import importlib.util
import os
import sys
import ipaddress
import shutil
import socket
import subprocess
import platform
import concurrent.futures
import time

APP_NAME = "Angry Admin: IP Scanner"
APP_BUNDLE_NAME = "Angry Admin IP Scanner"
APP_DESCRIPTION = "Desktop IP scanner for subnet, range, and DNS discovery workflows."
PACKAGE_NAME = "angry-admin-ipscanner"
PACKAGE_VERSION = "1.0"
PACKAGE_RELEASE = "1"
ORG_NAME = "AngrySysOps"
WEBSITE_URL = "https://angrysysops.com"
GUIDE_URL = "https://angrysysops.com/ip-scanner/"
X_HANDLE = "@TheTechWorldPod"
X_URL = "https://x.com/TheTechWorldPod"
YOUTUBE_NAME = "AngryAdmin"
YOUTUBE_URL = "https://youtube.com/@AngryAdmin"
DISCLAIMER_TEXT = (
    "Disclaimer:\n\n"
    "This program is provided 'as is' without any warranty, either express or implied. "
    "By using this program, you agree that you are doing so at your own risk, and the developer "
    "assumes no responsibility for any damages, losses, or legal issues that may result from its use."
)
PYQT5_MISSING_MESSAGE = "Missing dependency: PyQt5\nInstall it with: pip install PyQt5"
DNSPYTHON_WARNING = (
    "Reverse DNS requires the optional dnspython package.\n\n"
    "Install it with: pip install dnspython"
)


def has_module(module_name):
    return importlib.util.find_spec(module_name) is not None


HAS_DNSPYTHON = has_module("dns")
HAS_PYQT5 = has_module("PyQt5")

if HAS_DNSPYTHON:
    import dns.resolver
    import dns.reversename


def resource_path(*parts):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, *parts)


def application_icon_path():
    for candidate in ("icon.icns", "icon.png", "icon.ico"):
        icon_path = resource_path(candidate)
        if os.path.exists(icon_path):
            return icon_path
    return ""


def run_background_command(command, capture_output=False, text=False):
    system = platform.system().lower()
    kwargs = {}
    if system == "windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    if capture_output:
        kwargs["capture_output"] = True
        kwargs["text"] = text
    else:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    return subprocess.run(command, **kwargs)


def reverse_dns(ip):
    if not HAS_DNSPYTHON:
        return ""
    try:
        resolver = dns.resolver.Resolver()
        rev_name = dns.reversename.from_address(ip)
        answers = resolver.resolve(rev_name, "PTR", lifetime=5)
        return "; ".join(str(rdata.target).rstrip(".") for rdata in answers)
    except Exception:
        return ""


def parse_scan_input(scan_input: str):
    if "/" in scan_input:
        try:
            net = ipaddress.ip_network(scan_input, strict=False)
            return list(net.hosts())
        except Exception as exc:
            raise ValueError(
                "Please input a valid IP range. Example: 10.10.10.0/24 or 10.10.10.123-20"
            ) from exc
    if "-" in scan_input:
        parts = scan_input.replace(" ", "").split("-")
        if len(parts) != 2:
            raise ValueError("Please input a valid IP range. Example: 10.10.10.0/24 or 10.10.10.123-20")
        start_str, end_part = parts
        try:
            start_ip = ipaddress.IPv4Address(start_str)
        except Exception as exc:
            raise ValueError("Invalid start IP. Example: 10.10.10.123-20") from exc

        if "." in end_part:
            try:
                end_ip = ipaddress.IPv4Address(end_part)
            except Exception as exc:
                raise ValueError("Invalid end IP. Example: 10.10.10.123-10.10.10.200") from exc
        else:
            try:
                count = int(end_part)
            except Exception as exc:
                raise ValueError(
                    "Invalid count in range. It should be numeric. Example: 10.10.10.123-20"
                ) from exc
            if count <= 0:
                raise ValueError("Range count must be greater than zero.")
            try:
                end_ip = ipaddress.IPv4Address(int(start_ip) + count - 1)
            except Exception as exc:
                raise ValueError("Computed end IP is invalid. Check your range.") from exc

        if int(start_ip) > int(end_ip):
            raise ValueError("Start IP is greater than end IP in the range.")
        return [ipaddress.IPv4Address(ip) for ip in range(int(start_ip), int(end_ip) + 1)]

    raise ValueError(
        "Please input a valid IP range. Example: CIDR: 10.10.10.0/24 or Range: 10.10.10.123-20"
    )


def ping_command(ip):
    system = platform.system().lower()
    if system == "windows":
        return ["ping", "-n", "1", "-w", "2000", ip]
    if system == "darwin":
        return ["ping", "-c", "1", "-W", "2000", ip]
    return ["ping", "-c", "1", "-W", "2", ip]


def arp_command(ip):
    system = platform.system().lower()
    if system == "windows":
        return ["arp", "-a"]
    if system == "darwin":
        return ["arp", "-an", ip]
    if shutil.which("arping"):
        return ["arping", "-c", "1", ip]
    if shutil.which("ip"):
        return ["ip", "neigh", "show", ip]
    if shutil.which("arp"):
        return ["arp", "-n", ip]
    return []


if HAS_PYQT5:
    from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt, QSettings, QUrl
    from PyQt5.QtGui import QIcon, QTextDocument
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QProgressBar, QTableWidget,
        QTableWidgetItem, QMessageBox, QFileDialog, QAction, QCheckBox, QToolButton
    )
    from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
    from PyQt5.Qt import QDesktopServices


    class IPTableWidgetItem(QTableWidgetItem):
        def __lt__(self, other):
            try:
                return int(ipaddress.IPv4Address(self.text())) < int(ipaddress.IPv4Address(other.text()))
            except Exception:
                return self.text() < other.text()


    class ScanWorker(QObject):
        progress_signal = pyqtSignal(int)
        result_signal = pyqtSignal(str, bool, str)
        finished_signal = pyqtSignal()
        error_signal = pyqtSignal(str)

        def __init__(self, scan_input, use_ping, use_reverse_dns, use_arp, use_tcp, use_udp):
            super().__init__()
            self.scan_input = scan_input
            self.use_ping = use_ping
            self.use_reverse_dns = use_reverse_dns
            self.use_arp = use_arp
            self.use_tcp = use_tcp
            self.use_udp = use_udp

        def run(self):
            try:
                hosts = parse_scan_input(self.scan_input)
            except Exception as exc:
                self.error_signal.emit(str(exc))
                return

            total = len(hosts)
            completed = 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(100, max(1, total))) as executor:
                future_to_ip = {executor.submit(self.scan_ip, str(ip)): str(ip) for ip in hosts}
                for future in concurrent.futures.as_completed(future_to_ip):
                    try:
                        ip, pingable, dns_name = future.result()
                    except Exception:
                        ip = future_to_ip[future]
                        pingable = False
                        dns_name = ""
                    completed += 1
                    self.progress_signal.emit(int((completed / total) * 100))
                    self.result_signal.emit(ip, pingable, dns_name)
            self.finished_signal.emit()

        def scan_ip(self, ip):
            ping_ok = False
            if self.use_ping:
                command = ping_command(ip)
                for _ in range(2):
                    try:
                        if run_background_command(command).returncode == 0:
                            ping_ok = True
                            break
                    except Exception:
                        ping_ok = False
                    time.sleep(0.2)

            dns_name = reverse_dns(ip) if self.use_reverse_dns else ""

            arp_ok = False
            if self.use_arp:
                try:
                    command = arp_command(ip)
                    if command:
                        result = run_background_command(command, capture_output=True, text=True)
                        arp_output = result.stdout or ""
                        if platform.system().lower() == "windows":
                            arp_ok = ip in arp_output
                        else:
                            arp_ok = result.returncode == 0 and ip in arp_output
                except Exception:
                    arp_ok = False

            tcp_ok = False
            if self.use_tcp:
                try:
                    with socket.create_connection((ip, 80), timeout=2):
                        tcp_ok = True
                except Exception:
                    tcp_ok = False

            udp_ok = False
            if self.use_udp:
                udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    udp_sock.settimeout(2)
                    udp_sock.sendto(b"", (ip, 53))
                    udp_sock.recvfrom(1024)
                    udp_ok = True
                except Exception:
                    udp_ok = False
                finally:
                    udp_sock.close()

            return ip, (ping_ok or arp_ok or tcp_ok or udp_ok), dns_name


    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.settings = QSettings(ORG_NAME, APP_NAME)
            self.setWindowTitle(APP_NAME)
            self.resize(900, 620)
            icon_path = application_icon_path()
            if icon_path:
                self.setWindowIcon(QIcon(icon_path))
            self.thread = None
            self.worker = None
            self.setup_ui()
            self.setup_menu()
            if not HAS_DNSPYTHON:
                self.statusBar().showMessage(DNSPYTHON_WARNING, 15000)

        def setup_ui(self):
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)

            input_layout = QHBoxLayout()
            label = QLabel("Enter Subnet (CIDR) or IP Range:")
            self.scan_input_edit = QLineEdit()
            self.scan_input_edit.setPlaceholderText("CIDR: 10.10.10.0/24 or Range: 10.10.10.123-20")
            self.scan_input_edit.returnPressed.connect(self.start_scan)
            self.start_button = QPushButton("Start Scan")
            self.start_button.clicked.connect(self.start_scan)
            input_layout.addWidget(label)
            input_layout.addWidget(self.scan_input_edit)
            input_layout.addWidget(self.start_button)
            main_layout.addLayout(input_layout)

            options_layout = QHBoxLayout()
            options_layout.setSpacing(50)
            self.checkbox_ping = self.create_option(
                "Ping",
                "Sends an ICMP ping request to see if the host responds.",
                options_layout,
            )
            self.checkbox_reverse_dns = self.create_option(
                "Reverse DNS",
                "Uses dnspython to perform a reverse DNS lookup using local DNS settings.",
                options_layout,
            )
            if not HAS_DNSPYTHON:
                self.checkbox_reverse_dns.setChecked(False)
                self.checkbox_reverse_dns.setEnabled(False)
                self.checkbox_reverse_dns.setToolTip(DNSPYTHON_WARNING)
            self.checkbox_arp = self.create_option(
                "ARP",
                "Uses the local ARP toolchain to detect neighbors on the local network.",
                options_layout,
            )
            self.checkbox_tcp = self.create_option(
                "TCP Connect",
                "Attempts a TCP connection on port 80.",
                options_layout,
            )
            self.checkbox_udp = self.create_option(
                "UDP",
                "Sends a UDP packet to port 53 and waits for a response.",
                options_layout,
            )
            main_layout.addLayout(options_layout)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            main_layout.addWidget(self.progress_bar)

            self.table = QTableWidget(0, 3)
            self.table.setHorizontalHeaderLabels(["IP Address", "Status", "DNS Record"])
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setSortingEnabled(False)
            main_layout.addWidget(self.table)

        def create_option(self, name, info_text, parent_layout):
            hlayout = QHBoxLayout()
            hlayout.setSpacing(2)
            checkbox = QCheckBox(name)
            checkbox.setChecked(name in ["Ping", "Reverse DNS"])
            hlayout.addWidget(checkbox)
            tool_btn = QToolButton()
            tool_btn.setText("?")
            tool_btn.setToolTip(info_text)
            tool_btn.clicked.connect(lambda _, t=name, m=info_text: self.show_info(f"{t} Info", m))
            hlayout.addWidget(tool_btn)
            parent_layout.addLayout(hlayout)
            return checkbox

        def show_info(self, title, message):
            if title == "Reverse DNS Info" and not HAS_DNSPYTHON:
                message = f"{message}\n\n{DNSPYTHON_WARNING}"
            QMessageBox.information(self, title, message)

        def setup_menu(self):
            menubar = self.menuBar()

            file_menu = menubar.addMenu("File")
            save_csv_action = QAction("Save as CSV", self)
            save_csv_action.triggered.connect(self.save_as_csv)
            file_menu.addAction(save_csv_action)

            save_txt_action = QAction("Save as TXT", self)
            save_txt_action.triggered.connect(self.save_as_txt)
            file_menu.addAction(save_txt_action)

            save_html_action = QAction("Save as HTML", self)
            save_html_action.triggered.connect(self.save_as_html)
            file_menu.addAction(save_html_action)

            print_action = QAction("Print", self)
            print_action.triggered.connect(self.print_results)
            file_menu.addAction(print_action)

            about_menu = menubar.addMenu("About")
            user_guide_action = QAction("User Guide", self)
            user_guide_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(GUIDE_URL)))
            about_menu.addAction(user_guide_action)

            website_action = QAction("Website", self)
            website_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(WEBSITE_URL)))
            about_menu.addAction(website_action)

            about_action = QAction("About Angry Admin IP Scanner", self)
            about_action.triggered.connect(self.show_about_dialog)
            about_menu.addAction(about_action)

            disclaimer_action = QAction("Disclaimer", self)
            disclaimer_action.triggered.connect(self.show_disclaimer_dialog)
            menubar.addAction(disclaimer_action)

        def start_scan(self):
            if not any([
                self.checkbox_ping.isChecked(),
                self.checkbox_reverse_dns.isChecked(),
                self.checkbox_arp.isChecked(),
                self.checkbox_tcp.isChecked(),
                self.checkbox_udp.isChecked(),
            ]):
                QMessageBox.warning(self, "No Methods Selected", "Please select at least one scan method.")
                return

            self.start_button.setEnabled(False)
            self.table.setRowCount(0)
            self.progress_bar.setValue(0)
            self.table.setSortingEnabled(False)

            self.thread = QThread()
            self.worker = ScanWorker(
                self.scan_input_edit.text().strip(),
                self.checkbox_ping.isChecked(),
                self.checkbox_reverse_dns.isChecked(),
                self.checkbox_arp.isChecked(),
                self.checkbox_tcp.isChecked(),
                self.checkbox_udp.isChecked(),
            )
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.progress_signal.connect(self.update_progress)
            self.worker.result_signal.connect(self.add_result)
            self.worker.error_signal.connect(self.handle_error)
            self.worker.finished_signal.connect(self.scan_finished)
            self.worker.finished_signal.connect(self.thread.quit)
            self.worker.finished_signal.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()

        def update_progress(self, value):
            self.progress_bar.setValue(value)

        def add_result(self, ip, pingable, dns_name):
            status = "Used" if pingable else ("DNS reserved" if dns_name.strip() else "Free")
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, IPTableWidgetItem(ip))
            self.table.setItem(row, 1, QTableWidgetItem(status))
            self.table.setItem(row, 2, QTableWidgetItem(dns_name))

        def handle_error(self, message):
            QMessageBox.critical(self, "Input Error", message)
            self.start_button.setEnabled(True)
            if self.thread and self.thread.isRunning():
                self.thread.quit()

        def scan_finished(self):
            self.table.sortItems(0, Qt.AscendingOrder)
            self.table.setSortingEnabled(True)
            if not self.start_button.isEnabled():
                QMessageBox.information(self, "Scan Complete", "The scan has completed.")
                self.start_button.setEnabled(True)

        def _iter_rows(self):
            for row in range(self.table.rowCount()):
                ip_item = self.table.item(row, 0)
                status_item = self.table.item(row, 1)
                dns_item = self.table.item(row, 2)
                yield (
                    ip_item.text() if ip_item else "",
                    status_item.text() if status_item else "",
                    dns_item.text() if dns_item else "",
                )

        def save_as_csv(self):
            filename, _ = QFileDialog.getSaveFileName(self, "Save as CSV", "", "CSV Files (*.csv)")
            if not filename:
                return
            try:
                with open(filename, "w", encoding="utf-8") as handle:
                    handle.write("IP Address,Status,DNS Record\n")
                    for ip_text, status_text, dns_text in self._iter_rows():
                        handle.write(f"{ip_text},{status_text},{dns_text}\n")
                QMessageBox.information(self, "Saved", f"Results saved to {filename}")
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to save file: {exc}")

        def save_as_txt(self):
            filename, _ = QFileDialog.getSaveFileName(self, "Save as TXT", "", "Text Files (*.txt)")
            if not filename:
                return
            try:
                with open(filename, "w", encoding="utf-8") as handle:
                    handle.write("IP Address\tStatus\tDNS Record\n")
                    for ip_text, status_text, dns_text in self._iter_rows():
                        handle.write(f"{ip_text}\t{status_text}\t{dns_text}\n")
                QMessageBox.information(self, "Saved", f"Results saved to {filename}")
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to save file: {exc}")

        def save_as_html(self):
            filename, _ = QFileDialog.getSaveFileName(self, "Save as HTML", "", "HTML Files (*.html)")
            if not filename:
                return
            try:
                html = [
                    "<html><head><meta charset='utf-8'><title>Angry Admin: IP Scanner Results</title></head><body>",
                    "<table border='1' cellspacing='0' cellpadding='2'>",
                    "<tr><th>IP Address</th><th>Status</th><th>DNS Record</th></tr>",
                ]
                for ip_text, status_text, dns_text in self._iter_rows():
                    html.append(f"<tr><td>{ip_text}</td><td>{status_text}</td><td>{dns_text}</td></tr>")
                html.append("</table></body></html>")
                with open(filename, "w", encoding="utf-8") as handle:
                    handle.write("".join(html))
                QMessageBox.information(self, "Saved", f"Results saved to {filename}")
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to save file: {exc}")

        def print_results(self):
            output = ["IP Address,Status,DNS Record\n"]
            for ip_text, status_text, dns_text in self._iter_rows():
                output.append(f"{ip_text},{status_text},{dns_text}\n")
            doc = QTextDocument()
            doc.setPlainText("".join(output))
            printer = QPrinter(QPrinter.HighResolution)
            preview = QPrintPreviewDialog(printer, self)
            preview.paintRequested.connect(lambda p: doc.print_(p))
            preview.exec_()

        def show_about_dialog(self):
            about_text = f"""
            <html>
            <head/><body>
            <h2>{APP_NAME}</h2>
            <p><b>Powered by AngrySysOps</b></p>
            <p>{APP_DESCRIPTION}</p>
            <p>
                Website: <a href='{WEBSITE_URL}'>{WEBSITE_URL}</a><br>
                X: <a href='{X_URL}'>{X_HANDLE}</a><br>
                YouTube: <a href='{YOUTUBE_URL}'>{YOUTUBE_NAME}</a>
            </p>
            </body></html>
            """
            msg = QMessageBox(self)
            msg.setWindowTitle(f"About {APP_NAME}")
            msg.setTextFormat(Qt.RichText)
            msg.setText(about_text)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setIcon(QMessageBox.Information)
            msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
            msg.exec_()

        def show_disclaimer_dialog(self):
            QMessageBox.information(self, "Disclaimer", DISCLAIMER_TEXT)


    def ensure_disclaimer_accepted():
        settings = QSettings(ORG_NAME, APP_NAME)
        if settings.value("disclaimerAccepted", False, type=bool):
            return True

        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle("Disclaimer")
        dialog.setText(f"{DISCLAIMER_TEXT}\n\nDo you accept these terms?")
        checkbox = QCheckBox("Don't show this again")
        dialog.setCheckBox(checkbox)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.Yes)
        accepted = dialog.exec_() == QMessageBox.Yes
        if accepted and checkbox.isChecked():
            settings.setValue("disclaimerAccepted", True)
        return accepted


    def main():
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(PACKAGE_VERSION)
        app.setOrganizationName(ORG_NAME)
        icon_path = application_icon_path()
        if icon_path:
            app.setWindowIcon(QIcon(icon_path))
        if not ensure_disclaimer_accepted():
            return 0
        window = MainWindow()
        window.show()
        return app.exec_()
else:
    def main():
        print(PYQT5_MISSING_MESSAGE, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
