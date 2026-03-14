import imaplib, email, os

def harvest_news():
    user, pw = os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD')
    if not user or not pw: return
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(user, pw)
        mail.select('inbox')
        # Search for common tech newsletters or keywords
        status, messages = mail.search(None, '(OR SUBJECT "Newsletter" SUBJECT "Tech")')
        if status == 'OK':
            for num in messages[0].split()[-5:]: # Get the 5 most recent
                res, data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])
                content = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            content = part.get_payload(decode=True).decode()
                else: content = msg.get_payload(decode=True).decode()
                
                with open('data/knowledge_bank.txt', 'a', encoding='utf-8') as f:
                    f.write(f"\n🌱 [Seed Harvested] {msg['subject']}: {content[:500]}")
        mail.logout()
        print("🌻 News Harvester: Seeds collected from the digital wind.")
    except Exception as e: print(f"Harvester Error: {e}")

if __name__ == "__main__": harvest_news()
