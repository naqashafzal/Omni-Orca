# Auto-Reply & Text Extraction Guide

## 🤖 Auto-Reply Capabilities

The Neural Automater can now **automatically read and respond to messages**!

---

## ✨ New Features

### 1. **Text Extraction**
```python
get_text(selector)          # Get text from single element
get_all_text()              # Get all visible text from page
extract_data(selector)      # Extract from multiple elements
```

### 2. **Clipboard Operations**
```python
copy_to_clipboard(text)     # Copy text to clipboard
paste_from_clipboard(selector)  # Paste into element
```

### 3. **Smart Waiting**
```python
wait_for_text(text)         # Wait for specific text to appear
```

---

## 📱 Auto-Reply Use Cases

### 1. **WhatsApp Web Auto-Reply**

**Auto-Pilot Command:**
```
"Monitor WhatsApp and reply to new messages"
```

**What it does:**
1. Reads incoming messages
2. Analyzes the content
3. Generates appropriate response
4. Types and sends the reply

**Example Flow:**
```json
[
  { "action": "wait_for_text", "text": "New message" },
  { "action": "get_text", "selector": ".message-in" },
  { "action": "type", "selector": ".input-field", "text": "Thanks for your message! I'll get back to you soon." },
  { "action": "press_key", "key": "Enter" }
]
```

---

### 2. **Email Auto-Reply**

**Command:**
```
"Read my Gmail inbox and reply to unread emails"
```

**Flow:**
1. Navigate to Gmail
2. Find unread emails
3. Read email content
4. Generate contextual reply
5. Send response

---

### 3. **Social Media Auto-Reply**

**Supported Platforms:**
- Facebook Messenger
- Instagram DMs
- Twitter/X DMs
- LinkedIn Messages
- Discord
- Telegram Web

**Example:**
```
"Reply to Instagram DMs with 'Thanks for reaching out!'"
```

---

### 4. **Customer Support Automation**

**Command:**
```
"Monitor support chat and respond to common questions"
```

**Smart Features:**
- Detects question type
- Provides relevant answers
- Escalates complex issues
- Maintains conversation context

---

## 🎯 Example Auto-Reply Scenarios

### Scenario 1: Simple Auto-Reply
```json
[
  { "action": "navigate", "url": "https://web.whatsapp.com" },
  { "action": "wait_for_text", "text": "WhatsApp" },
  { "action": "click", "selector": ".chat-item:first-child" },
  { "action": "get_text", "selector": ".message-in:last-child" },
  { "action": "type", "selector": "[contenteditable]", "text": "Got your message! Will respond shortly." },
  { "action": "press_key", "key": "Enter" }
]
```

### Scenario 2: Context-Aware Reply
The AI will:
1. Read the message
2. Understand context (question, greeting, request, etc.)
3. Generate appropriate response
4. Send reply

**Example:**
- **Incoming**: "What are your business hours?"
- **AI Reply**: "We're open Monday-Friday, 9 AM - 5 PM. How can I help you?"

### Scenario 3: Data Extraction + Reply
```json
[
  { "action": "extract_data", "selector": ".customer-name" },
  { "action": "get_text", "selector": ".customer-message" },
  { "action": "type", "selector": ".reply-box", "text": "Hi [Name], thanks for contacting us!" },
  { "action": "click", "selector": ".send-button" }
]
```

---

## 📋 Text Extraction Examples

### Extract Product Prices
```
"Extract all product prices from this page"
```

AI will use:
```json
{ "action": "extract_data", "selector": ".price", "attribute": "textContent" }
```

### Copy Page Content
```
"Copy all text from this article"
```

AI will:
1. Get all text
2. Copy to clipboard

### Extract Links
```
"Get all links from this page"
```

```json
{ "action": "extract_data", "selector": "a", "attribute": "href" }
```

---

## 🔄 Auto-Reply Loop (Continuous Monitoring)

### Setup Continuous Auto-Reply

**Command:**
```
"Continuously monitor and reply to new messages"
```

**What happens:**
1. Auto-pilot mode activates
2. AI monitors for new messages
3. Reads each new message
4. Generates contextual reply
5. Sends response
6. Repeats until stopped

**Stop:** Click the "⏹ STOP" button

---

## 💡 Smart Reply Features

### Context Understanding
The AI can understand:
- **Questions** → Provides answers
- **Greetings** → Responds with greetings
- **Requests** → Acknowledges and responds
- **Complaints** → Apologizes and offers help
- **Spam** → Ignores or reports

### Personalization
- Uses sender's name if available
- Maintains conversation tone
- Adapts to platform style

### Multi-Language Support
- Detects message language
- Replies in same language

---

## 🛠️ Advanced Features

### 1. **Conditional Replies**
```
"Reply only to messages containing 'urgent'"
```

### 2. **Template Responses**
```
"Reply with: 'Thanks! We'll process your order within 24 hours.'"
```

### 3. **Data Collection**
```
"Extract customer emails and save to clipboard"
```

### 4. **Scheduled Replies**
```
"Wait 5 seconds before replying"
```

---

## 📝 Example Commands

### WhatsApp
```
✅ "Reply to WhatsApp messages automatically"
✅ "Send 'BRB' to all new WhatsApp messages"
✅ "Monitor WhatsApp and reply to questions"
```

### Email
```
✅ "Reply to unread emails with 'Received, will respond soon'"
✅ "Extract all email addresses from inbox"
✅ "Copy the latest email content"
```

### Social Media
```
✅ "Reply to Instagram DMs"
✅ "Auto-reply to Facebook messages"
✅ "Respond to Twitter mentions"
```

### Customer Support
```
✅ "Monitor support chat and reply to FAQs"
✅ "Extract customer complaints and copy to clipboard"
✅ "Reply to support tickets with acknowledgment"
```

---

## ⚙️ Configuration Tips

### 1. **Set Reply Delay**
Add wait time between reading and replying:
```json
{ "action": "wait", "seconds": 2 }
```

### 2. **Custom Reply Templates**
Provide specific text to use:
```
"Reply with: 'Thank you for your message. Our team will respond within 24 hours.'"
```

### 3. **Filter Messages**
Only reply to specific types:
```
"Reply only to messages containing 'support'"
```

---

## 🚨 Important Notes

### Privacy & Ethics
- ⚠️ Only use on your own accounts
- ⚠️ Inform people if using auto-reply
- ⚠️ Don't spam or send unsolicited messages
- ⚠️ Review auto-replies periodically

### Platform Limitations
- Some platforms may detect automation
- Rate limits may apply
- Login required for most platforms

### Best Practices
- ✅ Test on small scale first
- ✅ Monitor auto-replies regularly
- ✅ Use professional, helpful language
- ✅ Have human review for important messages
- ✅ Set max iterations to prevent infinite loops

---

## 🎮 Quick Start

### 1. Simple Auto-Reply
```
1. Open WhatsApp Web
2. Enable auto-pilot
3. Command: "Reply to new messages with 'Thanks!'"
4. Watch it work!
```

### 2. Smart Auto-Reply
```
1. Enable auto-pilot
2. Command: "Monitor messages and reply appropriately"
3. AI will read, understand, and respond
```

### 3. Text Extraction
```
1. Navigate to any page
2. Command: "Extract all product names"
3. Data appears in logs
```

---

## 🔧 Troubleshooting

### Messages Not Detected
- Ensure correct selector
- Check if page is fully loaded
- Use `wait_for_text()` first

### Replies Not Sending
- Verify send button selector
- Try `press_key("Enter")` instead of clicking
- Check for confirmation dialogs

### Clipboard Not Working
- Browser may block clipboard access
- Grant permissions when prompted
- Use manual copy as fallback

---

Enjoy your automated messaging! 🚀
