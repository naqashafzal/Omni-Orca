"""
email_agent.py
Gmail IMAP/SMTP email reader and composer.
No OAuth needed — uses Gmail App Password (Settings → Security → App Passwords).
"""

import smtplib
import imaplib
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import os


class EmailAgent:
    def __init__(self):
        self.email_address = None
        self.app_password = None
        self.imap = None
        self.connected = False

    def configure(self, email_address: str, app_password: str) -> str:
        """
        Sets Gmail credentials. Use an App Password, NOT your real Gmail password.
        Generate one at: myaccount.google.com -> Security -> App Passwords
        """
        self.email_address = email_address
        self.app_password = app_password
        return self._connect_imap()

    def _connect_imap(self) -> str:
        try:
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            self.imap.login(self.email_address, self.app_password)
            self.connected = True
            return f"✅ Connected to Gmail: {self.email_address}"
        except Exception as e:
            self.connected = False
            return f"❌ Email IMAP connection failed: {e}\n\nMake sure you've created an App Password at myaccount.google.com"

    def get_unread(self, n: int = 5) -> str:
        """
        Fetches the last N unread emails from the Gmail inbox.
        Returns a formatted summary with sender, subject, and body preview.
        """
        if not self.connected:
            return "Error: Not connected to email. Call configure() first."

        try:
            # Reconnect if disconnected
            try:
                self.imap.noop()
            except Exception:
                self._connect_imap()

            self.imap.select("INBOX")
            # Search for unread messages
            _, message_ids = self.imap.search(None, "UNSEEN")
            ids = message_ids[0].split()

            if not ids:
                return "📭 No unread emails in inbox."

            # Get latest N
            latest_ids = ids[-n:]
            output = f"📬 {len(ids)} unread emails total. Showing last {len(latest_ids)}:\n\n"

            for msg_id in reversed(latest_ids):
                _, data = self.imap.fetch(msg_id, "(RFC822)")
                raw_email = data[0][1]
                msg = email_lib.message_from_bytes(raw_email)

                # Decode subject
                subject_raw = msg.get("Subject", "No Subject")
                subject_parts = decode_header(subject_raw)
                subject = "".join(
                    part.decode(enc or "utf-8") if isinstance(part, bytes) else part
                    for part, enc in subject_parts
                )

                sender = msg.get("From", "Unknown Sender")
                date = msg.get("Date", "Unknown Date")

                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                output += f"FROM: {sender}\n"
                output += f"DATE: {date}\n"
                output += f"SUBJECT: {subject}\n"
                output += f"PREVIEW: {body.strip()[:300]}...\n"
                output += "---\n"

            return output.strip()

        except Exception as e:
            return f"Error reading emails: {e}"

    def send_email(self, to: str, subject: str, body: str) -> str:
        """
        Sends an email via Gmail SMTP.
        """
        if not self.email_address or not self.app_password:
            return "Error: Email not configured. Call configure() first."

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.email_address, self.app_password)
                server.send_message(msg)

            return f"✅ Email sent to {to} with subject: '{subject}'"

        except Exception as e:
            return f"❌ Failed to send email: {e}"

    def search_emails(self, keyword: str, max_results: int = 5) -> str:
        """Search inbox for emails containing a keyword in subject or body."""
        if not self.connected:
            return "Error: Not connected to email."
        try:
            self.imap.select("INBOX")
            _, message_ids = self.imap.search(None, f'SUBJECT "{keyword}"')
            ids = message_ids[0].split()
            if not ids:
                return f"No emails found with subject containing '{keyword}'"

            latest = ids[-max_results:]
            results = []
            for msg_id in reversed(latest):
                _, data = self.imap.fetch(msg_id, "(RFC822)")
                msg = email_lib.message_from_bytes(data[0][1])
                subject_raw = decode_header(msg.get("Subject", ""))[0]
                subject = subject_raw[0].decode(subject_raw[1] or "utf-8") if isinstance(subject_raw[0], bytes) else subject_raw[0]
                results.append(f"FROM: {msg.get('From')} | SUBJECT: {subject}")

            return "\n".join(results)
        except Exception as e:
            return f"Search error: {e}"


if __name__ == "__main__":
    agent = EmailAgent()
    # Replace with your Gmail address and App Password to test
    # result = agent.configure("your@gmail.com", "xxxx xxxx xxxx xxxx")
    # print(result)
    # print(agent.get_unread(3))
    print("Email Agent loaded. Configure with your Gmail App Password to use.")
