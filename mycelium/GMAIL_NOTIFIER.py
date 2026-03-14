import smtplib
import os
import json

def send_alert(subject, body):
    user = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_APP_PASSWORD')
    if not user or not password: return
    msg = f"Subject: {subject}\n\n{body}"
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(user, password)
        server.sendmail(user, user, msg)
        server.quit()
        print("📧 Notification sent.")
    except Exception as e:
        print(f"Mail Error: {e}")

if __name__ == "__main__":
    send_alert("Meeko Nerve Center", "System is stable and synchronized.")
