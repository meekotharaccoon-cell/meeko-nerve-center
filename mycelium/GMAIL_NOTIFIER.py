# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

﻿import smtplib
import os
import json
from datetime import datetime

def send_alert(subject, body):
    user = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_APP_PASSWORD')
    if not user or not password:
        print("Gmail credentials missing. Cannot notify.")
        return

    msg = f"Subject: {subject}\n\n{body}"
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(user, password)
        server.sendmail(user, user, msg)
        server.quit()
        print("📧 Notification sent to your inbox.")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    # Check for recent sales in proof_ledger.json
    ledger_path = 'data/proof_ledger.json'
    if os.path.exists(ledger_path):
        with open(ledger_path, 'r') as f:
            data = json.load(f)
            if data.get('pcrf_donation_due_usd', 0) > 0:
                send_alert("MEEKO SALE DETECTED", f"Revenue detected! PCRF Donation Due: ")
