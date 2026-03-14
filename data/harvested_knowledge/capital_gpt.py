# ======== 🧠 CAPITAL_GPT: MISSION STRATEGIST ========
# One mission. One mind. No mercy.

import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

# ┌────────────────────────────────────────────┐
# │ General’s Comment Markup & Strategic Notes │
# └────────────────────────────────────────────┘
#
# This file is the sacred mind of capital_gpt. If you’re reading this,
# it means the strategist is being tuned. Leave breadcrumbs, monologues,
# or Socratic reflections here — your future self will thank you.
#
# ▪ PROMPT: Add new mission parsing format? Extend scan_inbox() and msg_launch_mission()
# ▪ PROMPT: Inject blank agents live via reflex with msg_spawn_blank()
# ▪ PROMPT: Boot mission via reflex or .msg drop, like a warlord

import json
import time
import subprocess
import traceback
from matrixswarm.core.boot_agent import BootAgent

class Agent(BootAgent):
    def __init__(self):
        super().__init__()
        self.mission_root = os.path.join(self.path_resolution["comm_path_resolved"], "queue")
        self.inbox = os.path.join(self.path_resolution["comm_path_resolved"], "incoming")
        self.state_path = os.path.join(self.path_resolution["comm_path_resolved"], "state.json")
        self.matrix_payload = os.path.join(self.path_resolution["comm_path"], "matrix", "payload")
        os.makedirs(self.inbox, exist_ok=True)
        os.makedirs(self.mission_root, exist_ok=True)
        os.makedirs(self.matrix_payload, exist_ok=True)

        self.alert_fired = False
        self.trace_rounds = 0
        self.max_rounds = 5  # Failsafe to prevent infinite loops (Initialize here!)

    #INITIAL PROMPT
    def worker_pre(self):

        self.log("[CAPITAL] Pre-mission reflex initialized.")

        self.trace_rounds = 0
        self.alert_fired = False

        config = self.tree_node.get("config", {})
        mission_conf = config.get("mission", {})
        self.mission=mission_conf
        #msg["tracer_session_id"] = tracer_id
        #msg["packet_id"] = packet_num

        mission_id = mission_conf.get("mission_id", "spin-a")

        initial_prompt_text = mission_conf['1'].get('prompt', "")
        self.system_constraints = mission_conf.get("system_constraints", "")

        self.route_structured_prompt_to_oracle(
            intent_text=initial_prompt_text,
            mission_id=mission_id,
            role="oracle",
            history=[]
        )
        self.log("[CAPITAL] Initial prompt deployed to Oracle.")

    def generate_query_id(self):
        return f"q_{int(time.time())}_{os.getpid()}"


    '''
          "type": "prompt",
          "query_id": "q_1747592257_2533059",
          "content": "{\"prompt\": \"You are a cyber-intelligence strategist inside a secure AI swarm. Simulate a system posture analysis. Your in a Rocky 9 Linux environment. Identify risks. Classify them as suggestion, concern, or critical. Your response should be strategic, confident, and operationally useful.\", \"history\": [], \"mission_id\": \"blackhole-cometh\", \"target_universal_id\": \"sgt-in-arms\"}",
          "role": "oracle",
          "tracer_session_id": "GaXRBS1KU3zGoOmJoh91",
          "packet_id": 1747592260,
          "report_final_packet_to": "sgt-in-arms",
          "system_message": "You are Oracle, the AI strategist of MatrixSwarm. The strategist has no active thoughts or system context. You must ask for exact shell commands to gather Linux system information so you can advise next steps."
    '''
    def route_structured_prompt_to_oracle(self, intent_text, mission_id=None, role="oracle", history=None):

        time.sleep(5)

        qid = self.generate_query_id()
        mission_id = mission_id or self.get_current_mission_id()

        self.log("[REROUTE] Waiting 3 seconds before sending Oracle a new prompt...")


        prompt_payload = {
            "type": "prompt",
            "query_id": qid,
            "tracer_session_id": 'GaXRBS1KU3zGoOmJoh91',
            "packet_id": int(time.time()),
            "target_universal_id": self.command_line_args.get("universal_id"),
            "report_final_packet_to": self.command_line_args.get("universal_id"),
            "role": role,
            "response_mode": "terse",
            "content": {
                "prompt": intent_text,
                "mission_id": mission_id,
                "history": []
            }
        }

        self.save_to_trace_session(prompt_payload, msg_type="msg")

        uid = self.get_node_by_role("oracle")["universal_id"]
        inbox = os.path.join(self.path_resolution["comm_path"], uid, "incoming")
        os.makedirs(inbox, exist_ok=True)
        fname = f"prompt_{qid}.msg"
        with open(os.path.join(inbox, fname), "w", encoding="utf-8") as f:
            json.dump(prompt_payload, f, indent=2)

        dialogue_path = self.get_dialogue_path(mission_id)
        os.makedirs(dialogue_path, exist_ok=True)
        with open(os.path.join(dialogue_path, f"{qid}.prompt"), "w", encoding="utf-8") as f:
            json.dump(prompt_payload, f, indent=2)

        self.log(f"[INTEL] Routed structured prompt {qid} with mission_id {mission_id} to oracle.")


    def append_to_thread(self, query_id, role, type, content):
        """
               Appends a new message entry to a dialogue thread file in JSON Lines format.

               Parameters:
                   query_id (str): Identifier for the current query/thread.
                   role (str): The role of the message sender (e.g., 'user', 'system', 'agent').
                   type (str): The type of the message (e.g., 'text', 'action', 'error').
                   content (str or dict): The actual content of the message.

               Behavior:
                   - Constructs the file path for the thread using the current mission and query ID.
                   - Ensures the directory structure exists.
                   - Formats the message into a JSON object and appends it to the corresponding .jsonl thread file.
                   - Logs the operation for debugging or tracking purposes.
               """
        thread_path = os.path.join(self.get_dialogue_path(self.get_current_mission_id()), f"thread_{query_id}.jsonl")
        os.makedirs(os.path.dirname(thread_path), exist_ok=True)
        line = {
            "role": role,
            "type": type,
            "query_id": query_id,
            "content": content
        }
        with open(thread_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
        self.log(f"[THREAD] Appended {type} from {role} to thread: {query_id}")

    def msg_gpt_analysis(self, content, packet):

        response = content.get("response")

        oracle_response=response

        try:

            oracle_response = agent.extract_response_data(response)

        except Exception as e:
            self.log(f"[ORACLE][ERROR] Failed to parse response: {e}")
            self.log(f"[ORACLE][DEBUG] Raw content was:\n{response}")


        self.log(oracle_response.get('actions'))

        return


        qid = packet.get("query_id")

        self.append_to_thread(qid, role="oracle", type="gpt_response", content=response)

        mission_status = content.get("mission_status")
        if mission_status == 0:
            self.log("[CAPITAL] Oracle marked mission complete.")
            return
        if mission_status == -1:
            self.log("[CAPITAL][ERROR] Oracle encountered a failure. Mission paused. Operator intervention needed.")
            return

        tracer_session_id = content.get("tracer_session_id", "unknown")
        packet_id = content.get("packet_id", 1)

        try:
            # Parse the Oracle response
            if isinstance(response, str):
                try:
                    response_data = json.loads(response)
                except Exception as e:
                    self.log(f"[CAPITAL][ERROR] Failed to parse 'response' as JSON: {e}")
                    self.log(f"[CAPITAL][DEBUG] Raw response:\n{response}")
                    return
            else:
                response_data = response

            # Extract and flatten actions
            actions = response_data.get("actions", {})
            flat_actions = {}
            if isinstance(actions, dict):
                count = 1
                for value in actions.values():
                    if isinstance(value, dict) and "command" in value:
                        flat_actions[str(count)] = value["command"]
                    elif isinstance(value, str):
                        flat_actions[str(count)] = value
                    elif isinstance(value, list):
                        for cmd in value:
                            flat_actions[str(count)] = cmd
                            count += 1
                    else:
                        self.log(f"[CAPITAL][WARN] Unrecognized action format: {value}")
                    count += 1
            # Execute commands from actions
            command_output = {}
            for step, command in flat_actions.items():
                self.log(f"[EXECUTE] Running step {step}: {command}")
                output, error = self.run_check(command)
                command_output[step] = {
                    "command": command,
                    "output": output or "No output",
                    "error": error or "No error"
                }

            # Handle exit codes
            summary = response_data.get("summary", "")
            exit_code = response_data.get("exit_code", 0)

            if exit_code == 0:  # Mission complete
                if not self.alert_fired:
                    self.alert_operator(qid, message=f"🧹 Mission complete: {summary or 'No summary available.'}")
                return

            elif exit_code == 2:  # Oracle signals complete analysis
                self.log(f"[REFLEX] Oracle signaled complete analysis.")
                if not self.alert_fired:
                    self.alert_operator(qid,
                                        message=f"✅ Oracle received final analysis: {summary or 'No summary provided.'}")
                return

            elif exit_code == 3:  # Forced mission complete
                if not self.alert_fired:
                    self.alert_operator(qid,
                                        message=f"❌ Oracle forced mission completion: {summary or 'No summary provided.'}")
                return

            elif exit_code == -1:  # Retry once if Oracle failed
                if not content.get("already_retried"):
                    self.log("[REFLEX] Oracle returned exit_code -1. Retrying once...")
                    content["already_retried"] = True
                    self.route_structured_prompt_to_oracle(
                        intent_text=self.build_next_prompt(response, {}),
                        mission_id=content.get('mission_id'),
                        role="oracle"
                    )
                    return
                else:
                    if not self.alert_fired:
                        self.alert_operator(qid, message="Oracle parse failed again. Alerting operator.")
                    return

            elif exit_code == 1:  # Continue Reflex loop
                self.trace_rounds += 1
                self.log(f"[REFLEX] Trace round: {self.trace_rounds} of {self.max_rounds}")

                # Check if we've hit the maximum rounds
                if self.trace_rounds >= self.max_rounds:
                    self.log("[REFLEX] Max rounds reached. Checking for final summary.")

                    # Either provide the summary or notify no summary is available
                    if summary:
                        self.alert_operator(qid, message=f"🔚 Reflex loop complete. Final summary: {summary}")
                    else:
                        self.alert_operator(qid, message="🔚 Reflex loop complete. No summary available.")

                    self.alert_fired = True
                    return

                # Continue Reflex loop: generate next prompt and analyze
                self.route_structured_prompt_to_oracle(
                    intent_text=self.build_next_prompt(response, command_output),
                    mission_id=content.get("mission_id"),
                    role="oracle"
                )

        except Exception as e:
            error_details = traceback.format_exc()
            self.log(f"[CAPITAL][ERROR] Error processing Oracle response: {e} -> {error_details}")



    def alert_operator(self, qid, message=None):

        if self.alert_fired:
            return

        self.alert_fired = True

        if message:
            msg = f"{message}"
        else:
            msg = f"🚨 ORACLE REFLEX TERMINATION\n\nReflex loop failed (exit_code = -1)"

        comms = self.get_nodes_by_role('comm')
        if not comms:
            self.log("[REFLEX][ALERT] No comm nodes found. Alert not dispatched.")
        else:
            for comm in comms:
                self.log(f"[REFLEX] Alert routed to comm agent: {comm['universal_id']}")
                self.drop_reflex_alert(msg, comm['universal_id'], level="critical", cause="[PARSE ERROR]")

    def drop_reflex_alert(self, message, agent_dir, level="critical", cause=""):
        """
        Drop a reflex alert .msg file into /incoming/<agent_dir>/ for comm relays to pick up.
        Respects factory-injected Discord/Telegram agents already listening.
        """

        msg_body = message if message else "[REFLEX] No message provided."
        formatted_msg = f"📣 Swarm Message\n{msg_body}"
        payload = {
            "type": "send_packet_incoming",
            "content": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "universal_id": self.command_line_args.get("universal_id", "unknown"),
                "level": level,
                "msg": msg_body,
                "formatted_msg": formatted_msg,
                "cause": cause or msg_body,
                "origin": self.command_line_args.get("universal_id", "unknown")
            }
        }

        inbox_path = os.path.join(self.path_resolution["comm_path"], agent_dir, "incoming")
        os.makedirs(inbox_path, exist_ok=True)

        try:
            fname = f"reflex_alert_{int(time.time())}.msg"
            fullpath = os.path.join(inbox_path, fname)

            with open(fullpath, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            self.log(f"[REFLEX] Alert dropped to: {fullpath}")

        except Exception as e:
            self.log(f"[REFLEX][ERROR] Failed to write alert msg: {e}")

    @staticmethod
    def extract_response_data(response):
        """
        Extracts 'summary', 'commands', and 'exit_code' from the OpenAI response.
        Args:
            response (str): The raw OpenAI response text.
        Returns:
            dict: A dictionary containing 'summary', 'actions', and 'exit_code'.
        """
        # Default output in case of any issues with parsing
        parsed_response = {
            "summary": "[PARSE ERROR — No summary provided]",  # Default summary
            "actions": {},  # Default (empty) actions
            "exit_code": 3  # Default error code
        }

        try:
            # Check if it's properly JSON formatted, if yes, attempt parsing
            if isinstance(response, str) and response.strip().startswith("{"):
                response_data = json.loads(response)
                # Use parsed JSON (if valid)
                if "summary" in response_data:
                    parsed_response["summary"] = response_data["summary"]
                if "actions" in response_data:
                    parsed_response["actions"] = response_data["actions"]
                if "exit_code" in response_data:
                    parsed_response["exit_code"] = response_data["exit_code"]
            else:
                # Parse plain text response
                lines = response.splitlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("Classification:"):
                        # Extract summary
                        parsed_response["summary"] = line.split("Classification:")[1].strip()
                    elif line.startswith("Exit_Code:"):
                        # Extract exit code
                        try:
                            parsed_response["exit_code"] = int(line.split("Exit_Code:")[1].strip())
                        except ValueError:
                            pass  # Keep default exit_code in case of parsing errors
                    elif line and line[0].isdigit():  # Lines starting with numbers (commands)
                        # Extract command number and text
                        parts = line.split(".", 1)
                        if len(parts) == 2:
                            command_number = parts[0].strip()
                            command_text = parts[1].strip()
                            parsed_response["actions"][command_number] = command_text

        except Exception as e:
            # Log error if parsing failed (for debugging)
            print(f"[ERROR] Unable to parse response. Exception: {e}")

        return parsed_response

    def summarize_reflex_history(self, qid, limit=6):

        thread_path = os.path.join(self.get_dialogue_path(self.get_current_mission_id()), f"thread_{qid}.jsonl")

        if not os.path.exists(thread_path):
            return "[CAPITAL][ERROR] No thread log found."

        history = []
        with open(thread_path, 'r', encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    role = entry.get("role", "unknown")
                    content = entry.get("content", {})
                    if isinstance(content, str):
                        content_str = content
                    elif isinstance(content, dict):
                        summary = content.get("summary")
                        actions = content.get("actions")
                        if summary and actions:
                            content_str = f"🧠 {summary}\n📜 Commands: " + ", ".join(actions.values())
                        else:
                            content_str = json.dumps(content)
                    else:
                        content_str = str(content)

                    history.append(f"{role.upper()} ➤ {content_str}")
                except Exception as e:
                    history.append(f"[ERROR] Could not parse entry: {e}")

        # Only return the last few cycles for readability
        return "\n\n".join(history[-limit:])


    def build_next_prompt(self, response, command_output) -> str:
        """
        Given Oracle's last JSON response and your Linux command output,
        build the next prompt to send back to Oracle.

        Parameters:
            response (dict): The parsed JSON dictionary returned by Oracle.
            command_output (dict): A dictionary of command outputs,
                                   where key = "1", "2", etc. and value = (stdout, stderr)

        Returns:
            str: The next prompt to send to Oracle.
        """
        try:
            # Retrieve summary and actions from the response
            summary = response.get("summary", "")
            actions = response.get("actions", {})

            # Flatten the command output into a readable format
            shell_output_lines = []
            for key, output in command_output.items():
                # Validate and extract stdout and stderr
                if isinstance(output, tuple) and len(output) == 2:
                    stdout, stderr = output
                else:
                    self.log(f"[WARN] Invalid command output format for key {key}: {output}")
                    stdout, stderr = "No output", "No error"

                # Include the command details and results
                shell_output_lines.append(f"[Command {key}: {actions.get(key, '<unknown command>')}]")
                if stdout:
                    shell_output_lines.append(f"Output:\n{stdout}")
                if stderr:
                    shell_output_lines.append(f"Error:\n{stderr}")
                shell_output_lines.append("-" * 40)

            # Join all shell output lines into a single string
            shell_output_str = "\n".join(shell_output_lines)

            # Build the next prompt
            next_prompt = (
                f"Summary of previous analysis:\n{summary}\n\n"
                f"Shell Command Results:\n{shell_output_str}\n\n"
                f"Instructions: Based on the output above, what Linux command(s) should I run next?\n\n"
                f"⚠️ Return ONLY the following format:\n"
                f"Classification: [Suggestion | Concern | Critical]\n"
                f"1. command\n"
                f"2. command\n"
                f"Exit_Code: [1 | 2 | 3]\n\n"
                f"Do NOT use markdown. Do NOT return JSON. Do NOT explain anything."
            )

            # Log the constructed prompt for debugging
            self.log(f"#################{next_prompt}")

            return next_prompt

        except Exception as e:
            # Log the error and return a failure message as the prompt
            self.log(f"[ERROR] Exception in build_next_prompt: {e}")
            return f"[ERROR] Failed to build next prompt: {e}"

    def get_dialogue_history(self, qid):
        #  Implement this to fetch relevant history from thread files
        #  You'll need to read the JSONL files and format the history
        #  as a list of {"role": "...", "content": "..."} dictionaries.
        def get_dialogue_history(self, qid):
            history = []

            dialogue_path = self.get_dialogue_path(self.get_current_mission_id())
            thread_file = os.path.join(dialogue_path, f"thread_{qid}.jsonl")

            if os.path.exists(thread_file):
                with open(thread_file, 'r', encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())  # Load each line as JSON
                            role = entry.get("role")
                            content = entry.get("content")
                            if role and content:  # Only append if both exist
                                history.append({"role": role, "content": content})
                            else:
                                self.log(f"[CAPITAL][WARN] Incomplete entry in thread file: {line.strip()}")
                        except json.JSONDecodeError as e:
                            self.log(f"[CAPITAL][ERROR] JSON decode error in thread file: {e}, line: {line.strip()}")
                        except Exception as e:
                            self.log(
                                f"[CAPITAL][ERROR] Unexpected error reading thread file: {e}, line: {line.strip()}")
            else:
                self.log(f"[CAPITAL][WARN] No thread file found: {thread_file}")

            return history

    #Runs linux commands
    def run_check(self, command):
        try:
            start = time.time()
            try:
                output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=5)
                duration = round(time.time() - start, 3)
                self.log(f"[CMD] {command} completed in {duration}s")
                return output.decode("utf-8").strip(), None
            except subprocess.CalledProcessError as e:
                duration = round(time.time() - start, 3)
                self.log(f"[CMD] {command} failed in {duration}s")
                return "", e.output.decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            return "", e.output.decode("utf-8").strip()
        except Exception as e:
            return "", str(e)

    def fail_safe_stop(self, query_id, tracer_session_id, reason="no reason given"):
        self.log(f"[FAILSAFE] Mission aborted for {query_id}. Reason: {reason}")

    def validate_oracle_response(self, response):
        """
        Validates Oracle's response format.
        """
        if not isinstance(response, dict):
            return False

        required_keys = {"summary", "actions", "exit_code"}
        if not required_keys.issubset(response.keys()):
            return False

        if not isinstance(response["exit_code"], int) or response["exit_code"] not in {1, 2, 3}:
            return False

        return True

    def reflex_loop(self):
        """
        Core Reflex loop. Interacts with Oracle in iterative steps until max_rounds is reached
        or until reflex completion is signaled by Exit_Code: 2.

        Uses `end_prompt` in the final round.
        """
        self.current_round = 0

        while self.current_round < self.max_rounds:
            self.current_round += 1

            # Check if it's the final round
            if self.current_round == self.max_rounds:
                self.log(f"Final round {self.current_round}/{self.max_rounds} reached. Sending end_prompt.")
                prompt = self.mission["end_prompt"]
            else:
                # Use the current prompt for intermediate rounds
                prompt = self.current_prompt

            # Send the prompt to Oracle
            oracle_response = self.route_structured_prompt_to_oracle(prompt)

            # Validate the Oracle response
            if not self.validate_oracle_response(oracle_response):
                self.log(f"[ERROR] Invalid Oracle response in round {self.current_round}: {oracle_response}")
                return {
                    "classification": "Critical",
                    "summary": f"Invalid Oracle response in round {self.current_round}.",
                    "exit_code": 3,
                }

            # Log the processed response
            self.log(f"Round {self.current_round}/{self.max_rounds} Oracle Response: {oracle_response}")

            # Check exit_code to determine next steps
            exit_code = oracle_response.get("exit_code", 1)

            if exit_code == 2:
                self.log(f"Reflex loop complete. Oracle signaled Exit_Code: {exit_code}.")
                break
            elif exit_code == 3:
                self.log(f"Human intervention required. Oracle signaled Exit_Code: {exit_code}.")
                return oracle_response

            # If continuing, prepare the next prompt
            next_actions = oracle_response.get("actions", {})
            self.current_prompt = self.build_next_prompt(
                oracle_response,
                command_output=self.get_shell_outputs(next_actions)
            )

        # Reflex loop has exited; return completion signal
        return {
            "classification": "Suggestion",
            "summary": "Reflex loop completed. Review final response for details.",
            "exit_code": 2,
        }

    #todo dispatch to linux_scout or another os scout to handle the query
    #linux_scout; Bash - native, fast; windows_scout ; PowerShell; logic + WMI; container_scout; Docker - only; recon
    #gpu_scout NVIDIA driver / usage stats; k8s_scout; Cluster & pod; telemetry; db_scout SQL - aware schema scanner
    def TODOdispatch_to_scout(self, qid, commands, tracer_session_id="unknown", packet_id=1):

        scout_uid = self.get_node_by_role("scout")["universal_id"]

        msg = {
            "type": "check",
            "query_id": qid,
            "check": commands,
            "reflex_id": self.command_line_args.get("universal_id"),
            "tracer_session_id": tracer_session_id,
            "packet_id": int(time.time())
        }


        scout_inbox = os.path.join(self.path_resolution["comm_path"], scout_uid, "incoming")
        os.makedirs(scout_inbox, exist_ok=True)
        with open(os.path.join(scout_inbox, f"{qid}.msg"), "w", encoding="utf-8") as f:
            json.dump(msg, f, indent=2)
        self.log(f"[CAPITAL] Dispatched command to linux_scout")

    def reroute_back_to_oracle(self, query_id):
        thread_path = os.path.join(self.get_dialogue_path(self.get_current_mission_id()), f"thread_{query_id}.jsonl")
        if not os.path.exists(thread_path):
            self.log(f"[CAPITAL][ERROR] No thread found for {query_id}")
            return

        with open(thread_path, encoding="utf-8") as f:
            lines = f.readlines()

        history = []
        for line in lines:
            try:
                entry = json.loads(line)
                role = entry.get("role", "user")
                content = entry.get("content", {})
                if isinstance(content, dict):
                    msg = content.get("summary") or json.dumps(content)
                else:
                    msg = str(content)
                history.append(f"{role.upper()}: {msg}")
            except:
                continue

        prompt_text = "\n".join(history[-8:])  # last 8 turns
        self.route_structured_prompt_to_oracle(
            intent_text=prompt_text,
            mission_id=self.get_current_mission_id(),
            role="oracle",
            system_message_override="Continue the diagnostic conversation using prior messages. Suggest what command or investigation should be done next."
        )
    def get_current_mission_id(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, encoding="utf-8") as f:
                state = json.load(f)
            return state.get("active_mission", "unknown")
        return "unknown"

    def get_dialogue_path(self, mission_id):
        for folder in sorted(os.listdir(self.mission_root), reverse=True):
            if mission_id in folder:
                return os.path.join(self.mission_root, folder, "dialogue")
        return os.path.join(self.mission_root, f"unknown_mission_{mission_id}", "dialogue")



if __name__ == "__main__":
    agent = Agent()
    agent.boot()
