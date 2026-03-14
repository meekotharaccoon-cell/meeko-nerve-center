import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
import socket
socket.setdefaulttimeout(10)  # Set a 10-second global timeout for sockets
import email
from email.header import decode_header
from dotenv import load_dotenv
load_dotenv()
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()


        config = self.tree_node.get("config", {})

        self.interval = config.get("interval", int(os.getenv("EMAILCHECKAGENT_INTERVAL", 60)))
        self.mail_host = config.get("imap_host") or os.getenv("EMAILCHECKAGENT_IMAP_HOST")
        self.mail_user = config.get("email") or os.getenv("EMAILCHECKAGENT_EMAIL")
        self.mail_pass = config.get("password") or os.getenv("EMAILCHECKAGENT_PASSWORD")
        self.report_to = config.get("report_to") or os.getenv("EMAILCHECKAGENT_REPORT_TO", "mailman-1")

    def worker_pre(self):
        import socket
        import imaplib

        self.log("[EMAIL] Preparing IMAP connection...")
        socket.setdefaulttimeout(10)
        try:
            self.mail = imaplib.IMAP4_SSL(self.mail_host)
            self.mail.login(self.mail_user, self.mail_pass)
            self.mail.select("inbox")
            self.log("[EMAIL] Connected to inbox.")
        except Exception as e:
            self.log(f"[EMAIL][ERROR][LOGIN] {e}")
            self.mail = None

    def worker(self, config:dict = None, identity:IdentityObject = None):


        if not self.mail:
            return  # Connection failed during pre

        try:
            result, data = self.mail.search(None, 'UNSEEN')
            if result != 'OK' or not data or not data[0]:
                return

            ids = data[0].split()
            for num in ids:
                if not self.running:
                    break

                result, msg_data = self.mail.fetch(num, "(RFC822)")
                if result != 'OK':
                    continue

                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subject, encoding = decode_header(msg["Subject"])[0]
                subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject

                self.log(f"[EMAIL] New mail: {subject}")

        except Exception as e:
            self.log(f"[EMAIL][ERROR][WORKER] {e}")

    def worker_post(self):
        if hasattr(self, 'mail') and self.mail:
            try:
                self.mail.logout()
                self.log("[EMAIL] Logged out cleanly.")
            except Exception as e:
                self.log(f"[EMAIL][ERROR][LOGOUT] {e}")


    def extract_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return msg.get_payload(decode=True).decode()
        return "[no text]"

if __name__ == "__main__":
    agent = Agent()
    agent.boot()