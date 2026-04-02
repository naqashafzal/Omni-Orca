"""
call_agent.py
Twilio-powered AI phone calls and SMS.
Get a free Twilio trial at https://twilio.com — gives $15 credit.
"""

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


class CallAgent:
    def __init__(self):
        self.account_sid = None
        self.auth_token = None
        self.from_number = None  # Your Twilio phone number e.g. "+12025551234"
        self.client = None
        self.configured = False

    def configure(self, account_sid: str, auth_token: str, from_number: str) -> str:
        """
        Sets up Twilio credentials.
        Get these from: https://console.twilio.com
        """
        if not TWILIO_AVAILABLE:
            return "Error: twilio not installed. Run: pip install twilio"

        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

        try:
            self.client = TwilioClient(account_sid, auth_token)
            # Verify by fetching account info
            account = self.client.api.accounts(account_sid).fetch()
            self.configured = True
            return f"✅ Twilio connected. Account: {account.friendly_name}"
        except Exception as e:
            self.configured = False
            return f"❌ Twilio connection failed: {e}"

    def make_call(self, to_number: str, message: str) -> str:
        """
        Makes an AI-powered outbound phone call.
        The AI converts `message` to speech using Twilio's built-in TTS.
        `to_number` format: +923001234567
        """
        if not self.configured:
            return "Error: Call Agent not configured. Call configure() first."

        try:
            # Twilio TwiML: simple text-to-speech
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="en-US">{message}</Say>
    <Pause length="1"/>
    <Say voice="Polly.Joanna">This message was sent from Neural Automater.</Say>
</Response>"""

            call = self.client.calls.create(
                twiml=twiml,
                to=to_number,
                from_=self.from_number
            )

            return f"✅ Call initiated to {to_number}. Call SID: {call.sid}"
        except Exception as e:
            return f"❌ Call failed: {e}"

    def send_sms(self, to_number: str, message: str) -> str:
        """
        Sends an SMS text message.
        `to_number` format: +923001234567
        """
        if not self.configured:
            return "Error: Call Agent not configured."

        try:
            sms = self.client.messages.create(
                body=message,
                to=to_number,
                from_=self.from_number
            )
            return f"✅ SMS sent to {to_number}. Message SID: {sms.sid}"
        except Exception as e:
            return f"❌ SMS failed: {e}"

    def get_call_logs(self, limit: int = 5) -> str:
        """Returns the last N calls from the Twilio account log."""
        if not self.configured:
            return "Error: Not configured."

        try:
            calls = self.client.calls.list(limit=limit)
            if not calls:
                return "No call logs found."

            output = f"📞 Last {limit} calls:\n"
            for c in calls:
                output += f"  • To: {c.to} | Status: {c.status} | Duration: {c.duration}s | {c.start_time}\n"
            return output
        except Exception as e:
            return f"Error fetching call logs: {e}"


if __name__ == "__main__":
    agent = CallAgent()
    print("Call Agent loaded.")
    print("Configure with Twilio credentials to make calls.")
    # agent.configure("ACxxxx", "your_auth_token", "+1XXXXXXXXXX")
    # print(agent.send_sms("+923001234567", "Hello from Neural Automater!"))
