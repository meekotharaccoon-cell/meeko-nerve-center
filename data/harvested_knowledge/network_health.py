#Authored by Daniel F MacDonald and ChatGPT aka The Generals
import sys
import os
import psutil
import socket
from datetime import datetime

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    """
    MatrixSwarm NetworkHealthMonitor agent.
    Reports interface status, connections, load, packet errors, and top process hogs.
    """
    def __init__(self):
        super().__init__()
        self.name = "NetworkHealthMonitor"

        config = self.tree_node.get("config", {})

        self.iface_exclude = set(config.get("exclude_interfaces", []))
        self.tx_threshold_mbps = config.get("tx_threshold_mbps", 100)  # example: warn if outbound > 100 Mbps
        self.rx_threshold_mbps = config.get("rx_threshold_mbps", 100)
        self.conn_threshold = config.get("conn_threshold", 1000)
        self.top_n_procs = config.get("top_n_procs", 5)
        self.check_interval_sec = config.get("check_interval_sec", 30)
        self.report_to_role = config.get("report_to_role", "hive.forensics.data_feed")
        self.report_handler = config.get("report_handler", "cmd_ingest_status_report")

        # For traffic rate measurement
        self.prev_net_io = None
        self.prev_time = None

        self.log("NetworkHealthMonitor initialized.")

    def send_status_report(self, status, severity, details, metrics=None):
        """Sends status to the configured role."""
        content = {
            "handler": self.report_handler,
            "content": {
                "source_agent": self.name,
                "service_name": "system.network",
                "status": status,
                "details": details,
                "severity": severity,
                "metrics": metrics or {},
            }
        }
        report_nodes = self.get_nodes_by_role(self.report_to_role)
        if not report_nodes:
            return

        pk = self.get_delivery_packet("standard.command.packet")
        pk.set_data(content)
        for node in report_nodes:
            self.pass_packet(pk, node["universal_id"])
            self.log(f"Sent '{severity}' for 'system.network' to role '{self.report_to_role}'", level="INFO")


    def get_network_summary(self):
        """Collects interface/IP status and errors/drops."""
        metrics = {}
        if_stats = psutil.net_if_stats()
        if_addrs = psutil.net_if_addrs()
        if_io = psutil.net_io_counters(pernic=True)
        now = datetime.now().isoformat()

        # Rate measurement setup
        tx_rates = {}
        rx_rates = {}
        if self.prev_net_io and self.prev_time:
            dt = (datetime.now() - self.prev_time).total_seconds()
            for iface in if_io:
                if iface in self.prev_net_io:
                    tx_bps = (if_io[iface].bytes_sent - self.prev_net_io[iface].bytes_sent) / dt * 8
                    rx_bps = (if_io[iface].bytes_recv - self.prev_net_io[iface].bytes_recv) / dt * 8
                    tx_rates[iface] = round(tx_bps / 1e6, 2)  # Mbps
                    rx_rates[iface] = round(rx_bps / 1e6, 2)  # Mbps

        summary = []
        for iface, stats in if_stats.items():
            if iface in self.iface_exclude:
                continue
            addr_info = [a.address for a in if_addrs.get(iface, []) if a.family == socket.AF_INET]
            io = if_io.get(iface)
            line = {
                "iface": iface,
                "ip": addr_info,
                "up": stats.isup,
                "speed_mbps": stats.speed,
                "tx_errs": io.errout if io else 0,
                "rx_errs": io.errin if io else 0,
                "drops": (io.dropin + io.dropout) if io else 0,
                "tx_rate_mbps": tx_rates.get(iface, 0),
                "rx_rate_mbps": rx_rates.get(iface, 0),
            }
            summary.append(line)
        metrics["interfaces"] = summary
        self.prev_net_io = if_io
        self.prev_time = datetime.now()
        return metrics

    def get_conn_summary(self):
        """Summarizes active TCP/UDP connections."""
        conns = psutil.net_connections()
        count = len(conns)
        by_status = {}
        for c in conns:
            key = c.status if hasattr(c, 'status') else 'UNKNOWN'
            by_status[key] = by_status.get(key, 0) + 1
        return {"total_connections": count, "by_status": by_status}

    def get_top_process_hogs(self):
        """Returns top processes by network bytes, CPU, and memory."""
        proc_list = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'io_counters']):
            try:
                net_io = proc.io_counters() if proc.io_counters else None
                info = {
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu_percent": proc.info['cpu_percent'],
                    "rss_mb": proc.info['memory_info'].rss / (1024 ** 2) if proc.info['memory_info'] else 0,
                    "write_bytes": net_io.write_bytes if net_io else 0,
                    "read_bytes": net_io.read_bytes if net_io else 0,
                }
                proc_list.append(info)
            except Exception:
                continue
        # Sort by cpu_percent, then rss, then write_bytes
        proc_list.sort(key=lambda x: (x['cpu_percent'], x['rss_mb'], x['write_bytes']), reverse=True)
        return proc_list[:self.top_n_procs]

    def worker(self, config: dict = None, identity: IdentityObject = None):
        try:
            metrics = {}

            # 1. Interfaces and rates
            net_metrics = self.get_network_summary()
            metrics.update(net_metrics)
            iface_alerts = []
            for iface in net_metrics["interfaces"]:
                if iface["tx_rate_mbps"] > self.tx_threshold_mbps:
                    iface_alerts.append(f"{iface['iface']} outbound {iface['tx_rate_mbps']} Mbps > {self.tx_threshold_mbps} Mbps")
                if iface["rx_rate_mbps"] > self.rx_threshold_mbps:
                    iface_alerts.append(f"{iface['iface']} inbound {iface['rx_rate_mbps']} Mbps > {self.rx_threshold_mbps} Mbps")
                if iface["tx_errs"] > 0 or iface["rx_errs"] > 0 or iface["drops"] > 0:
                    iface_alerts.append(f"{iface['iface']} errors: TX={iface['tx_errs']} RX={iface['rx_errs']} drops={iface['drops']}")

            # 2. Connections
            conn_metrics = self.get_conn_summary()
            metrics.update(conn_metrics)
            conn_alert = conn_metrics["total_connections"] > self.conn_threshold

            # 3. Top process hogs
            metrics["top_procs"] = self.get_top_process_hogs()

            # Send alerts or regular report
            if iface_alerts or conn_alert:
                status = "network_issue"
                severity = "WARNING"
                details = "; ".join(iface_alerts)
                if conn_alert:
                    details += f"; High connection count: {conn_metrics['total_connections']} > {self.conn_threshold}"
                self.send_status_report(status, severity, details, metrics)
            else:
                # Routine, informational report (could throttle if you only want to send on change/issue)
                self.send_status_report("healthy", "INFO", "Network health within normal bounds.", metrics)

        except Exception as e:
            self.log(f"Error in NetworkHealthMonitor: {e}")

        interruptible_sleep(self, self.check_interval_sec)

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
