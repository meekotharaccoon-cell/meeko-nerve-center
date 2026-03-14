import imaplib
import email
import os

def check_gmail_for_updates():
    # USES YOUR WORKING GMAIL CHANNEL
    user = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not user or not password:
        print("Gmail credentials missing. Skipping intake.")
        return

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")
        
        # Search for updates sent from YOU to YOURSELF
        status, messages = mail.search(None, '(SUBJECT "MEEKO_UPDATE")')
        
        for num in messages[0].split():
            status, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    new_code = part.get_payload(decode=True).decode()
                    # Save as a new engine to be picked up by the next cycle
                    filename = f"mycelium/AUTO_ENGINE_{num.decode()}.py"
                    with open(filename, "w") as f:
                        f.write(new_code)
                    print(f"Successfully birthed {filename} via Gmail Intake.")
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Gmail Intake Error: {e}")

if __name__ == '__main__':
    check_gmail_for_updates()
