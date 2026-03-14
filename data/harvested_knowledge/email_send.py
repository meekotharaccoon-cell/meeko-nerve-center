# email_relay.py
# Authored by Daniel F MacDonald and ChatGPT aka The Generals
# Refactored by Gemini

import sys
import os
import smtplib
from email.message import EmailMessage

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    """
    An agent that relays swarm alerts to a specified email address.

    This agent acts as a standard alert handler, listening for commands sent
    to the `cmd_send_alert_msg` handler. It is designed to work reliably
    with modern email providers like Gmail and Outlook by using a secure
    SSL/TLS connection from the outset.
    """
    def __init__(self):
        """
        Initializes the agent and loads its SMTP configuration.

        This method loads all necessary SMTP credentials and server details
        from the agent's directive configuration block.

        Attributes:
            smtp_host (str): The SMTP server hostname (e.g., "smtp.gmail.com").
            smtp_port (int): The SMTP server port (e.g., 465 for SSL).
            from_address (str): The email address to send from.
            password (str): The password or App Password for the sender's email.
            to_address (str): The email address to send the alert to.
        """
        super().__init__()

        config = self.tree_node.get("config", {})
        self.smtp_host = config.get("smtp_host")
        self.smtp_port = config.get("smtp_port")
        self.from_address = config.get("from_address")
        self.password = config.get("password")
        self.to_address = config.get("to_address")

    def worker(self, config: dict = None, identity: IdentityObject = None):
        """
        The main worker loop for this agent is intentionally left blank.

        As a relay agent, its functionality is entirely event-driven through
        the `cmd_send_alert_msg` handler. It does not need to perform any
        actions on a recurring basis.
        """
        pass

    def cmd_send_alert_msg(self, content: dict, packet, identity: IdentityObject = None):
        """
        The main command handler for receiving and processing swarm alerts.

        This method is triggered when another agent sends a packet to it. It
        extracts the relevant information from the alert, formats it for an
        email, and calls the internal `_send_email` method to dispatch it.

        Args:
            content (dict): The alert payload from the sending agent.
            packet (dict): The raw packet data.
            identity (IdentityObject): The verified identity of the command sender.
        """
        if not all([self.smtp_host, self.smtp_port, self.from_address, self.password, self.to_address]):
            self.log("SMTP configuration is incomplete. Cannot send email.", level="ERROR")
            return

        try:
            # The 'cause' of the alert makes a great email subject
            subject = content.get("cause", "MatrixSwarm Alert")

            # Prioritize the pre-formatted message, but fall back to the raw message
            body = content.get("formatted_msg") or content.get("msg") or "No message content provided."

            self._send_email(subject, body)

        except Exception as e:
            self.log("Failed to process alert for email sending.", error=e, block="cmd_send_alert_msg")

    def _send_email(self, subject: str, body: str):
        """
        Connects to the SMTP server and sends the email.

        This method uses `smtplib.SMTP_SSL` to establish a secure connection
        from the start, which is more reliable for services like Gmail and
        Outlook.

        Args:
            subject (str): The subject line for the email.
            body (str): The plain text body of the email.
        """
        msg = EmailMessage()
        msg["From"] = self.from_address
        msg["To"] = self.to_address
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            # Using SMTP_SSL establishes a secure connection from the beginning.
            # This is more robust and required by providers like Gmail on port 465.
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.from_address, self.password)
                server.send_message(msg)
                self.log(f"Successfully sent email alert to {self.to_address}")
        except smtplib.SMTPAuthenticationError:
            self.log("SMTP Authentication failed. Check username/password or consider using an App Password.", level="ERROR")
        except Exception as e:
            self.log("Failed to send email via SMTP.", error=e, block="_send_email")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
