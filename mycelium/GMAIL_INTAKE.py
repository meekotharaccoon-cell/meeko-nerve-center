import imaplib
import email
import os

def check_inbox():
    user = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_APP_PASSWORD')
    if not user or not password:
        print("Gmail credentials missing.")
        return

    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(user, password)
        mail.select('inbox')

        # Search for unread emails with "Meeko" in the subject
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Meeko")')
        
        if status == 'OK':
            for num in messages[0].split():
                status, data = mail.fetch(num, '(RFC822)')
                for response_part in data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = msg['subject']
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                        else:
                            body = msg.get_payload(decode=True).decode()

                        # Inject into knowledge bank
                        with open('data/knowledge_bank.txt', 'a', encoding='utf-8') as f:
                            f.write(f"\n[Remote Intake] {subject}: {body.strip()}")
                        print(f"🧠 Remote Knowledge Injected: {subject}")

        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Intake Error: {e}")

if __name__ == "__main__":
    check_inbox()
