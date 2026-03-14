# Authored by Daniel F MacDonald and Gemini
import sys
import os

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import importlib
import time
import json
import hashlib
import uuid
from collections import OrderedDict

from matrixswarm.core.boot_agent import BootAgent


class Agent(BootAgent):
    def __init__(self):
        super().__init__()
        self.name = "ForensicDetective"
        self.event_buffer = OrderedDict()
        self.buffer_size = 100
        self.correlation_window_sec = 120
        self.service_name = ""
        self.source_agent = ""

        config = self.tree_node.get("config", {})
        self.alert_cooldown = config.get("alert_cooldown_sec", 300)
        self.alert_role = config.get("alert_to_role", "hive.alert.send_alert_msg")

        # --- Oracle Integration Config ---
        # This feature is off by default. To enable, add an "oracle_analysis"
        # block to your directive's config.
        oracle_config = config.get("oracle_analysis", {})
        self.enable_oracle_analysis = bool(oracle_config.get("enable_oracle", 0))
        self.oracle_role = oracle_config.get("role", "hive.oracle")

        self.last_alerts = {}
        self.summary_path = os.path.join(self.path_resolution["comm_path_resolved"], "summary")
        os.makedirs(self.summary_path, exist_ok=True)

    def _hash_event(self, event_data):
        """Creates a consistent hash based on the event's content."""
        event_string = json.dumps({
            k: event_data[k] for k in sorted(event_data) if k != 'timestamp'
        }, sort_keys=True).encode('utf-8')
        return hashlib.sha256(event_string).hexdigest()

    def should_alert(self, key):
        """Checks if an alert should be sent based on the cooldown period."""
        now = time.time()
        last_alert_time = self.last_alerts.get(key, 0)
        if (now - last_alert_time) > self.alert_cooldown:
            self.last_alerts[key] = now
            return True
        self.log(f"Alert for '{key}' is on cooldown. Suppressing.", level="INFO")
        return False

    def send_simple_alert(self, message, incident_id, critical_event, title_prefix="🔬 Forensic Report"):
        """Constructs and sends a unified alert packet with both text and embed data."""
        if not self.alert_role: return
        alert_nodes = self.get_nodes_by_role(self.alert_role)
        if not alert_nodes: return

        trigger_service = critical_event.get('service_name', 'unknown')
        trigger_status = critical_event.get('status', 'unknown')

        simple_formatted_msg = (
            f"{title_prefix}: {trigger_service.capitalize()} is {trigger_status.upper()}\n"
            f"ID: {incident_id}\n---\n{message}"
        )

        embed_data = {
            "title": f"{title_prefix}: {trigger_service.capitalize()} Failure",
            "description": f"**Trigger:** `{trigger_service}` reported as `{trigger_status}`.\n---\n**Analysis:**\n{message}",
            "color": "red" if title_prefix.startswith("🔬") else "blue",
            "footer": f"Incident ID: {incident_id}"
        }

        pk = self.get_delivery_packet("notify.alert.general")
        pk.set_data({
            "msg": message,
            "formatted_msg": simple_formatted_msg,
            "embed_data": embed_data,
            "cause": "Forensic Analysis Report",
            "origin": self.command_line_args.get("universal_id")
        })

        cmd_pk = self.get_delivery_packet("standard.command.packet")
        cmd_pk.set_data({"handler": "cmd_send_alert_msg"})
        cmd_pk.set_packet(pk, "content")

        for node in alert_nodes:
            self.pass_packet(cmd_pk, node["universal_id"])

    def cmd_ingest_status_report(self, content, packet, identity=None):
        """Handler for receiving data. Triggers forensics on CRITICAL events."""
        try:
            status_data = content
            self.source_agent = status_data.get('source_agent', 'unknown_agent')
            self.service_name = status_data.get('service_name', 'unknown_service')
            severity = status_data.get('severity', 'INFO').upper()
            self.log(f"[INGEST] ✅ Received '{severity}' report from '{self.source_agent}' for service '{self.service_name}'.")

            event_hash = self._hash_event(status_data)
            now = time.time()

            if event_hash not in self.event_buffer:
                self.event_buffer[event_hash] = {'count': 0, 'first_seen': now, 'event_data': status_data}
            self.event_buffer[event_hash]['count'] += 1
            self.event_buffer[event_hash]['last_seen'] = now
            self.event_buffer.move_to_end(event_hash)

            if len(self.event_buffer) > self.buffer_size:
                self.event_buffer.popitem(last=False)

            service_name = status_data.get('service_name', 'unknown_service')

            if severity == "CRITICAL" and self.should_alert(service_name):
                incident_id = str(uuid.uuid4())
                self.log(f"CRITICAL event for '{service_name}' triggered a new incident: {incident_id}")

                correlated_events = [
                    event['event_data'] for event in self.event_buffer.values()
                    if (now - event['last_seen']) < self.correlation_window_sec
                ]

                forensic_findings_list = self.run_forensics(status_data['service_name'], correlated_events)
                full_forensic_report = "\n".join(forensic_findings_list)
                concise_alert_summary = forensic_findings_list[0] if forensic_findings_list else "Forensic analysis could not be completed."

                # --- STAGE 1: Send Immediate Alert ---
                self.send_simple_alert(concise_alert_summary, incident_id, status_data)

                # --- STAGE 2: Request Oracle Analysis ---
                if self.enable_oracle_analysis:
                    self._request_oracle_analysis(incident_id, status_data, correlated_events)

                self.save_event_summary(incident_id, status_data, correlated_events, full_forensic_report)

        except Exception as e:
            self.log(error=e, level="ERROR", block="main_try")

    def _request_oracle_analysis(self, incident_id, critical_event, correlated_events):
        """Asks the Oracle for a deeper analysis of the incident."""
        oracle_nodes = self.get_nodes_by_role(self.oracle_role)
        if not oracle_nodes:
            self.log(f"Oracle analysis enabled, but no agent with role '{self.oracle_role}' found.", level="WARNING")
            return

        # --- REMEDY ---
        # Robustly handle the 'details' field, which can be a dict or a string.
        details = critical_event.get('details')
        if isinstance(details, dict):
            critical_log = details.get('log_line', str(details))
        elif isinstance(details, str):
            critical_log = details
        else:
            critical_log = "No specific log line or details provided for the critical event."

        context_logs_list = []
        for evt in correlated_events:
            if evt.get('severity') != 'CRITICAL':
                evt_details = evt.get('details')
                log_line = 'N/A'
                if isinstance(evt_details, dict):
                    log_line = evt_details.get('log_line', str(evt_details))
                elif isinstance(evt_details, str):
                    log_line = evt_details

                context_logs_list.append(f"- {evt.get('severity')}: {log_line}")

        context_logs_str = "\n".join(context_logs_list)
        # --- END REMEDY ---

        prompt = (
            "You are an expert IT security analyst and systems administrator. "
            "An automated monitor has detected a critical event on a server. "
            "Your task is to analyze the critical event in the context of the preceding log entries, "
            "diagnose the probable root cause, and provide clear, actionable remediation steps.\n\n"
            "**Critical Event:**\n"
            f"`{critical_log}`\n\n"
            "**Preceding Events (for context):**\n"
            f"{context_logs_str}\n\n"
            "**Your Analysis:**\n"
            "1.  **Root Cause Analysis:** (Based on the events, what is the most likely cause of the critical event?)\n"
            "2.  **Recommended Actions:** (Provide a short, numbered list of shell commands or steps an administrator should take to verify the issue and remediate it.)"
        )

        pk = self.get_delivery_packet("standard.command.packet")
        pk.set_data({
            "handler": "cmd_msg_prompt",
            "content": {
                "prompt": prompt,
                "query_id": incident_id,  # Use incident_id to track the response
                "target_universal_id": self.command_line_args.get("universal_id"),
                "return_handler": "cmd_oracle_forensics_response"  # The handler for the Oracle's answer
            }
        })

        # Send the request to the first available Oracle
        self.pass_packet(pk, oracle_nodes[0]['universal_id'])
        self.log(f"Requested Oracle analysis for incident {incident_id}.")

    def cmd_oracle_forensics_response(self, content, packet, identity=None):
        """Handles the enriched analysis received from the Oracle."""
        try:
            incident_id = content.get("query_id")
            ai_analysis = content.get("response")

            if not incident_id or not ai_analysis:
                self.log("Received an invalid forensics response from Oracle.", level="ERROR")
                return

            self.log(f"Received Oracle analysis for incident {incident_id}.")

            # We need a 'critical_event' to properly format the alert.
            # This is a limitation; we'll create a placeholder.
            placeholder_event = {
                "service_name": "AI Analysis",
                "status": "Completed"
            }

            # Send the AI's response as a new, enriched alert
            self.send_simple_alert(ai_analysis, incident_id, placeholder_event, title_prefix="🤖 AI-Enhanced Analysis")

        except Exception as e:
            self.log(error=e, level="ERROR", block="cmd_oracle_forensics_response")

    def save_event_summary(self, incident_id, critical_event, correlated_events, forensic_report):
        """Saves all event data to a single JSON file for offline analysis."""
        summary_data = {
            "incident_id": incident_id,
            "incident_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "critical_event": critical_event,
            "correlated_events": correlated_events,
            "full_forensic_report": forensic_report
        }
        filename = f"{time.strftime('%Y%m%d-%H%M%S')}-{critical_event['service_name']}-failure.json"
        filepath = os.path.join(self.summary_path, filename)
        try:
            with open(filepath, 'w', encoding="utf-8") as f:
                json.dump(summary_data, f, indent=4)
            self.log(f"Full incident summary saved to: {filepath}")
        except Exception as e:
            self.log(f"Failed to save event summary: {e}", level="ERROR")

    def run_forensics(self, service_name, recent_events):
        """Dynamically loads and runs the appropriate investigator."""
        findings = []
        try:
            mod_path = f"forensic_detective.factory.watchdog.{service_name}.investigator"
            factory_module = importlib.import_module(mod_path)
            Investigator = getattr(factory_module, "Investigator")
            specialized_investigator = Investigator(self, service_name, recent_events)
            return specialized_investigator.add_specific_findings(findings)
        except ImportError:
            self.log(f"No specialized factory for '{service_name}'.", level="INFO")
            return ["No specialized forensic investigator found."]
        except Exception as e:
            self.log(f"Specialized factory failed: {e}", level="ERROR")
            return [f"[!] The specialized '{service_name}' investigator failed to run."]


if __name__ == "__main__":
    agent = Agent()
    agent.boot()