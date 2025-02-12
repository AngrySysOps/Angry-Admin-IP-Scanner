#!/usr/bin/env python3
import sys
import ipaddress
import socket
import subprocess
import platform
import concurrent.futures
import time

# Import dnspython modules
import dns.resolver
import dns.reversename

from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QPainter, QTextDocument
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QTableWidget,
    QTableWidgetItem, QMessageBox, QFileDialog, QAction, QCheckBox, QToolButton
)
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt5.Qt import QDesktopServices

# -------------------------------------------------------------------
# Custom QTableWidgetItem for numerical IP sorting.
# -------------------------------------------------------------------
class IPTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return int(ipaddress.IPv4Address(self.text())) < int(ipaddress.IPv4Address(other.text()))
        except Exception:
            return self.text() < other.text()

# -------------------------------------------------------------------
# Reverse DNS lookup using dnspython with local DNS settings.
# -------------------------------------------------------------------
def reverse_dns(ip):
    try:
        resolver = dns.resolver.Resolver()  
        # Uses the system's local DNS settings.
        rev_name = dns.reversename.from_address(ip)
        answers = resolver.resolve(rev_name, 'PTR', lifetime=5)
        result = "; ".join([str(rdata.target).rstrip('.') for rdata in answers])
        return result
    except Exception:
        return ""

# -------------------------------------------------------------------
# Parse user input into a list of IPv4Address objects.
#
# Accepted formats:
#   1. CIDR: e.g. "10.10.10.0/24"
#   2. Full range: e.g. "10.10.10.123-10.10.10.200"
#   3. Count-based range: e.g. "10.10.10.123-20" means 20 IPs starting at 10.10.10.123.
# -------------------------------------------------------------------
def parse_scan_input(scan_input: str):
    if "/" in scan_input:
        try:
            net = ipaddress.ip_network(scan_input, strict=False)
            return list(net.hosts())
        except Exception as e:
            raise ValueError("Please input a valid IP range. Example: 10.10.10.0/24 or 10.10.10.123-20")
    elif "-" in scan_input:
        parts = scan_input.replace(" ", "").split("-")
        if len(parts) != 2:
            raise ValueError("Please input a valid IP range. Example: 10.10.10.0/24 or 10.10.10.123-20")
        start_str = parts[0]
        end_part = parts[1]
        try:
            start_ip = ipaddress.IPv4Address(start_str)
        except Exception:
            raise ValueError("Invalid start IP. Example: 10.10.10.123-20")
        # If the end part contains a dot, treat it as a full IP.
        if "." in end_part:
            try:
                end_ip = ipaddress.IPv4Address(end_part)
            except Exception:
                raise ValueError("Invalid end IP. Example: 10.10.10.123-10.10.10.200")
        else:
            # Otherwise, treat the end part as the count of IPs.
            try:
                count = int(end_part)
            except Exception:
                raise ValueError("Invalid count in range. It should be numeric. Example: 10.10.10.123-20")
            start_int = int(start_ip)
            end_int = start_int + count - 1
            try:
                end_ip = ipaddress.IPv4Address(end_int)
            except Exception:
                raise ValueError("Computed end IP is invalid. Check your range.")
        if int(start_ip) > int(end_ip):
            raise ValueError("Start IP is greater than end IP in the range.")
        return [ipaddress.IPv4Address(ip) for ip in range(int(start_ip), int(end_ip) + 1)]
    else:
        raise ValueError("Please input a valid IP range. Example: CIDR: 10.10.10.0/24 or Range: 10.10.10.123-20")

# -------------------------------------------------------------------
# Worker class that performs the IP scan using various methods.
# -------------------------------------------------------------------
class ScanWorker(QObject):
    progress_signal = pyqtSignal(int)          # Emits progress percentage (0-100)
    result_signal = pyqtSignal(str, bool, str)   # Emits (ip, pingable, dns_name)
    finished_signal = pyqtSignal()               # Signals that scanning is complete
    error_signal = pyqtSignal(str)               # Emits error messages

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
        except Exception as e:
            self.error_signal.emit(str(e))
            return
        total = len(hosts)
        count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            future_to_ip = {executor.submit(self.scan_ip, str(ip)): str(ip) for ip in hosts}
            for future in concurrent.futures.as_completed(future_to_ip):
                try:
                    ip, pingable, dns_name = future.result()
                except Exception:
                    ip = future_to_ip[future]
                    pingable = False
                    dns_name = ""
                count += 1
                percent = int((count / total) * 100)
                self.progress_signal.emit(percent)
                self.result_signal.emit(ip, pingable, dns_name)
        self.finished_signal.emit()

    def scan_ip(self, ip):
        system = platform.system().lower()
        ping_ok = False
        if self.use_ping:
            attempts = 2
            for i in range(attempts):
                try:
                    if "windows" in system:
                        command = ["ping", "-n", "1", "-w", "2000", ip]
                    else:
                        command = ["ping", "-c", "1", "-W", "2", ip]
                    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if result.returncode == 0:
                        ping_ok = True
                        break
                except Exception:
                    ping_ok = False
                time.sleep(0.2)
        dns_name = ""
        if self.use_reverse_dns:
            dns_name = reverse_dns(ip)
        arp_ok = False
        if self.use_arp:
            try:
                if "windows" in system:
                    result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
                    if ip in result.stdout:
                        arp_ok = True
                else:
                    result = subprocess.run(["arping", "-c", "1", ip],
                                            stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL)
                    arp_ok = (result.returncode == 0)
            except Exception:
                arp_ok = False
        tcp_ok = False
        if self.use_tcp:
            try:
                s = socket.create_connection((ip, 80), timeout=2)
                s.close()
                tcp_ok = True
            except Exception:
                tcp_ok = False
        udp_ok = False
        if self.use_udp:
            try:
                udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udp_sock.settimeout(2)
                udp_sock.sendto(b"", (ip, 53))
                udp_sock.recvfrom(1024)
                udp_ok = True
                udp_sock.close()
            except Exception:
                udp_ok = False
        pingable = ping_ok or arp_ok or tcp_ok or udp_ok
        return (ip, pingable, dns_name)

# -------------------------------------------------------------------
# Main GUI Application
# -------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Angry Admin: IP Scanner")
        self.resize(800, 600)
        self.setWindowIcon(QIcon("icon.ico"))
        self.setup_ui()
        self.setup_menu()
        self.thread = None
        self.worker = None

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        # Input Area for IP Range / CIDR.
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
        # Scan Method Options.
        options_layout = QHBoxLayout()
        options_layout.setSpacing(155)
        self.checkbox_ping = self.create_option("Ping", "Sends an ICMP ping request to see if the host responds.", options_layout)
        self.checkbox_reverse_dns = self.create_option("Reverse DNS", "Uses dnspython to perform a reverse DNS lookup using local DNS settings.", options_layout)
        self.checkbox_arp = self.create_option("ARP", "Sends ARP requests to detect the host (local networks only).", options_layout)
        self.checkbox_tcp = self.create_option("TCP Connect", "Attempts a TCP connection on port 80.", options_layout)
        self.checkbox_udp = self.create_option("UDP", "Sends a UDP packet to port 53 and waits for a response.", options_layout)
        main_layout.addLayout(options_layout)
        # Progress Bar.
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        main_layout.addWidget(self.progress_bar)
        # Table to Display Results.
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["IP Address", "Status", "DNS Record"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(False)
        main_layout.addWidget(self.table)

    def create_option(self, name, info_text, parent_layout):
        hlayout = QHBoxLayout()
        hlayout.setSpacing(2)
        checkbox = QCheckBox(name)
        checkbox.setChecked(True if name in ["Ping", "Reverse DNS"] else False)
        hlayout.addWidget(checkbox)
        tool_btn = QToolButton()
        tool_btn.setText("?")
        tool_btn.setToolTip(info_text)
        tool_btn.clicked.connect(lambda _, t=name, m=info_text: self.show_info(t + " Info", m))
        hlayout.addWidget(tool_btn)
        parent_layout.addLayout(hlayout)
        return checkbox

    def show_info(self, title, message):
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
        # Add About action directly to the menubar.
        about_action = QAction("About Angry Admin IP Scanner", self)
        about_action.triggered.connect(self.show_about_dialog)
        menubar.addAction(about_action)

    def start_scan(self):
        if not (self.checkbox_ping.isChecked() or self.checkbox_reverse_dns.isChecked() or 
                self.checkbox_arp.isChecked() or self.checkbox_tcp.isChecked() or 
                self.checkbox_udp.isChecked()):
            QMessageBox.warning(self, "No Methods Selected", "Please select at least one scan method.")
            return
        self.start_button.setEnabled(False)
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.table.setSortingEnabled(False)
        scan_input = self.scan_input_edit.text().strip()
        use_ping = self.checkbox_ping.isChecked()
        use_reverse_dns = self.checkbox_reverse_dns.isChecked()
        use_arp = self.checkbox_arp.isChecked()
        use_tcp = self.checkbox_tcp.isChecked()
        use_udp = self.checkbox_udp.isChecked()
        self.thread = QThread()
        self.worker = ScanWorker(scan_input, use_ping, use_reverse_dns, use_arp, use_tcp, use_udp)
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
        if pingable:
            status = "Used"
        elif dns_name.strip() != "":
            status = "DNS reserved"
        else:
            status = "Free"
        row = self.table.rowCount()
        self.table.insertRow(row)
        ip_item = IPTableWidgetItem(ip)
        status_item = QTableWidgetItem(status)
        dns_item = QTableWidgetItem(dns_name)
        self.table.setItem(row, 0, ip_item)
        self.table.setItem(row, 1, status_item)
        self.table.setItem(row, 2, dns_item)

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

    def save_as_csv(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save as CSV", "", "CSV Files (*.csv)")
        if not filename:
            return
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("IP Address,Status,DNS Record\n")
                for row in range(self.table.rowCount()):
                    ip_item = self.table.item(row, 0)
                    status_item = self.table.item(row, 1)
                    dns_item = self.table.item(row, 2)
                    ip_text = ip_item.text() if ip_item is not None else ""
                    status_text = status_item.text() if status_item is not None else ""
                    dns_text = dns_item.text() if dns_item is not None else ""
                    f.write(f"{ip_text},{status_text},{dns_text}\n")
            QMessageBox.information(self, "Saved", f"Results saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def save_as_txt(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save as TXT", "", "Text Files (*.txt)")
        if not filename:
            return
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("IP Address\tStatus\tDNS Record\n")
                for row in range(self.table.rowCount()):
                    ip_item = self.table.item(row, 0)
                    status_item = self.table.item(row, 1)
                    dns_item = self.table.item(row, 2)
                    ip_text = ip_item.text() if ip_item is not None else ""
                    status_text = status_item.text() if status_item is not None else ""
                    dns_text = dns_item.text() if dns_item is not None else ""
                    f.write(f"{ip_text}\t{status_text}\t{dns_text}\n")
            QMessageBox.information(self, "Saved", f"Results saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def save_as_html(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save as HTML", "", "HTML Files (*.html)")
        if not filename:
            return
        try:
            html = "<html><head><meta charset='utf-8'><title>Angry Admin: IP Scanner Results</title></head><body>"
            html += "<table border='1' cellspacing='0' cellpadding='2'>"
            html += "<tr><th>IP Address</th><th>Status</th><th>DNS Record</th></tr>"
            for row in range(self.table.rowCount()):
                ip_item = self.table.item(row, 0)
                status_item = self.table.item(row, 1)
                dns_item = self.table.item(row, 2)
                ip_text = ip_item.text() if ip_item is not None else ""
                status_text = status_item.text() if status_item is not None else ""
                dns_text = dns_item.text() if dns_item is not None else ""
                html += f"<tr><td>{ip_text}</td><td>{status_text}</td><td>{dns_text}</td></tr>"
            html += "</table></body></html>"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            QMessageBox.information(self, "Saved", f"Results saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def print_results(self):
        # Prepare CSV-formatted text output.
        output = "IP Address,Status,DNS Record\n"
        for row in range(self.table.rowCount()):
            ip_item = self.table.item(row, 0)
            status_item = self.table.item(row, 1)
            dns_item = self.table.item(row, 2)
            ip_text = ip_item.text() if ip_item is not None else ""
            status_text = status_item.text() if status_item is not None else ""
            dns_text = dns_item.text() if dns_item is not None else ""
            output += f"{ip_text},{status_text},{dns_text}\n"
        doc = QTextDocument()
        doc.setPlainText(output)
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(lambda p: doc.print_(p))
        preview.exec_()

    def show_about_dialog(self):
        about_text = """
        <html>
        <head/><body>
        <h2>Angry Admin</h2>
        <p><b>Angry Admin: IP Scanner</b></p>
        <p>
            Visit our website: <a href='http://www.angrysysops.com'>www.angrysysops.com</a><br>
            Subscribe on YouTube: <a href='https://youtube.be/@AngryAdmin'>youtube.be/@AngryAdmin</a><br>
            Follow on X: <a href='https://x.com/AngrySysOps'>x.com/AngrySysOps</a>
        </p>
        </body></html>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("About")
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setIcon(QMessageBox.Information)
        msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
        msg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
