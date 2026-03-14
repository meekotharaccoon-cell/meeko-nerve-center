import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
import psutil
import time
import json
import traceback
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        sample_interval=60
        report_window = 24 * 60

        self.sample_interval = sample_interval  # in seconds
        self.report_window = report_window  # in minutes (default: 24 hours)
        self.samples = []
        self.process_stats = Counter()
        self.cpu_count = psutil.cpu_count(logical=True)
        self.last_bin_report = {}
        self.current_day = self.today()

    def today(self):
        return datetime.now().strftime("%Y-%m-%d")


    def sample(self):
        load = psutil.getloadavg()[0]  # 1-minute load avg
        timestamp = time.time()
        self.samples.append((timestamp, load))

        # trim window
        cutoff = timestamp - (self.report_window * 60)
        self.samples = [s for s in self.samples if s[0] >= cutoff]

        # process stats
        for proc in psutil.process_iter(['name', 'cpu_percent']):
            try:
                self.process_stats[proc.info['name']] += proc.info['cpu_percent']
            except Exception:
                continue

        self.log(f"Sampled load={load:.2f} | Active processes: {len(self.process_stats)}")

    def analyze(self):
        bins = defaultdict(int)
        hours = defaultdict(float)
        total_load = 0.0

        for ts, load in self.samples:
            percent_load = load / self.cpu_count
            total_load += percent_load

            # Range bins
            if percent_load < 0.1:
                bins['<0.1'] += 1
            elif percent_load < 0.5:
                bins['0.1-0.5'] += 1
            elif percent_load < 1.0:
                bins['0.5-1.0'] += 1
            elif percent_load < 2.0:
                bins['1.0-2.0'] += 1
            else:
                bins['>2.0'] += 1

            # Time-of-day contribution
            hour = datetime.fromtimestamp(ts).hour
            hours[hour] += percent_load

        total_samples = len(self.samples)
        report = {
            "date": self.today(),
            "load_distribution": {
                k: (v / total_samples) * 100 for k, v in bins.items()
            },
            "hourly_load_contribution": {
                f"{h:02d}:00": (v / total_load) * 100 for h, v in sorted(hours.items())
            },
            "top_processes": [
                {"name": name, "cpu_total": round(cpu, 2)} for name, cpu in self.process_stats.most_common(3)
            ]
        }

        # Log it in style with deltas
        self.log("--- Load Range Report ---")
        for rng, pct in report["load_distribution"].items():
            delta = pct - self.last_bin_report.get(rng, 0.0)
            sign = "+" if delta >= 0 else "-"
            self.log(f"Load {rng}: {pct:.2f}% ({sign}{abs(delta):.2f}%)")
        self.last_bin_report = report["load_distribution"]

        for hour, pct in report["hourly_load_contribution"].items():
            self.log(f"{hour} load share: {pct:.2f}%")
        for proc in report["top_processes"]:
            self.log(f"Top process: {proc['name']} (CPU Total: {proc['cpu_total']:.2f}%)")
        self.log("--------------------------")

        return report

    def write_daily_summary(self, report):
        try:
            summary_dir = os.path.join(self.path_resolution["comm_path_resolved"], "summary")
            os.makedirs(summary_dir, exist_ok=True)

            date = self.today()
            summary_path = os.path.join(summary_dir, f"loadrange_summary_{date}.json")
            latest_path = os.path.join(summary_dir, "loadrange_summary_latest.json")

            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            with open(latest_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            self.log(f"[SUMMARY] ✅ loadrange summary written to: {summary_path}")

        except Exception as e:
            self.log(f"[SUMMARY][ERROR] Failed to write loadrange summary: {e}")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        try:
                if self.today() != self.current_day:
                    # new day, flush report
                    report = self.analyze()
                    self.write_daily_summary(report)
                    self.samples = []
                    self.process_stats = Counter()
                    self.current_day = self.today()

                self.sample()

        except Exception as e:
            err = str(e)
            stack = traceback.format_exc()
            self.log(f"[LOAD_RANGE][WORKER][ERROR] {err}")
            self.log(stack)  # Optional: write full trace to logs

        interruptible_sleep(self, self.sample_interval)

if __name__ == "__main__":
    agent = Agent()
    agent.boot()