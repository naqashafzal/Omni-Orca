import asyncio
import json
import os
import re
import time
import sqlite3
import random
from datetime import datetime, date


class SocialMediaManager:
    def __init__(self, browser_agent, content_generator, llm_client):
        self.browser = browser_agent
        self.content_gen = content_generator
        self.llm = llm_client
        self.scheduled_posts = []
        self._stop_bot = False   # Threading stop flag
        self._init_history_db()

    # ─────────────────────────────────────────────
    # Database helpers
    # ─────────────────────────────────────────────

    def _init_history_db(self):
        """Initialize SQLite database for tracking processed tweets and daily stats."""
        db_path = os.path.join(os.getcwd(), "social_bot_history.db")
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_tweets (
                tweet_id    TEXT PRIMARY KEY,
                platform    TEXT,
                reply_text  TEXT,
                timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                stat_date   TEXT PRIMARY KEY,
                reply_count INTEGER DEFAULT 0
            )
        ''')
        self.db.commit()

    def is_processed(self, tweet_id: str, platform: str = "twitter") -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT 1 FROM processed_tweets WHERE tweet_id = ? AND platform = ?",
            (tweet_id, platform)
        )
        return cursor.fetchone() is not None

    def mark_processed(self, tweet_id: str, platform: str, reply_text: str = ""):
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO processed_tweets (tweet_id, platform, reply_text) VALUES (?, ?, ?)",
            (tweet_id, platform, reply_text)
        )
        self.db.commit()

    def get_daily_reply_count(self) -> int:
        today = date.today().isoformat()
        cursor = self.db.cursor()
        cursor.execute("SELECT reply_count FROM daily_stats WHERE stat_date = ?", (today,))
        row = cursor.fetchone()
        return row[0] if row else 0

    def increment_daily_count(self):
        today = date.today().isoformat()
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO daily_stats (stat_date, reply_count) VALUES (?, 1) "
            "ON CONFLICT(stat_date) DO UPDATE SET reply_count = reply_count + 1",
            (today,)
        )
        self.db.commit()

    def stop_bot(self):
        """Signal the bot loop to stop."""
        self._stop_bot = True

    def reset_stop(self):
        """Reset the stop flag before a new run."""
        self._stop_bot = False

    # ─────────────────────────────────────────────
    # Human-like helpers
    # ─────────────────────────────────────────────

    async def _type_like_human(self, selector, text):
        """Type text character-by-character with random delays."""
        try:
            # Try clicking within a frame context too
            await self.browser.page.click(selector)
        except Exception:
            pass
        for char in text:
            await self.browser.page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.01, 0.05))
        # Occasional human pause mid-text
        if random.random() < 0.2:
            await asyncio.sleep(random.uniform(0.1, 0.3))

    async def _random_scroll(self):
        """Perform human-like random scrolling (fast)."""
        scrolls = random.randint(1, 2)
        for _ in range(scrolls):
            direction = random.choice([300, 400, -150])
            await self.browser.page.mouse.wheel(0, direction)
            await asyncio.sleep(random.uniform(0.2, 0.5))

    async def _extract_tweet_text(self) -> str:
        """Extract the actual tweet text from the current page."""
        try:
            elements = await self.browser.page.query_selector_all("[data-testid='tweetText']")
            texts = []
            for el in elements[:3]:  # First 3 text blocks should be the tweet
                t = await el.inner_text()
                if t.strip():
                    texts.append(t.strip())
            return " | ".join(texts) if texts else ""
        except Exception:
            return ""

    def _is_spam_or_hostile(self, text: str) -> bool:
        """Basic heuristic to skip clearly spam or hostile tweets."""
        if not text:
            return False
        patterns = [
            r'\bgiveaway\b', r'\bairdrop\b', r'\bfollowback\b',
            r'click here', r'bit\.ly', r't\.co\/[A-Za-z0-9]{6,}',
            r'buy now', r'discount', r'promo code',
            r'fuck you', r'\bscam\b'
        ]
        lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, lower):
                return True
        return False

    # ─────────────────────────────────────────────
    # Advanced Twitter Bot
    # ─────────────────────────────────────────────

    async def run_advanced_twitter_bot(
        self,
        keywords,
        max_replies=5,
        delay_range=(8, 20),   # ← was (30, 90) — 30-90s per reply = way too slow!
        mode="AI",
        prompt_context="",
        progress_callback=None,
        daily_limit=20
    ):
        """
        Advanced keyword-driven auto-commenter loop for Twitter/X.
        Features:
        - Reads actual tweet text via CSS selectors
        - AI-generated contextual replies via generate_text()
        - Spam/hostile tweet filtering
        - Daily reply limit enforcement
        - Human-like typing, scrolling, pauses
        - Stoppable via self._stop_bot flag
        """
        if not self.browser.page:
            await self.browser.start()

        self.reset_stop()
        replies_count = 0
        total_keywords = len(keywords)
        daily_done = self.get_daily_reply_count()

        def cb(msg):
            if progress_callback:
                progress_callback(msg)

        if daily_done >= daily_limit:
            return f"Daily limit of {daily_limit} replies already reached today. Try again tomorrow."

        for i, kw in enumerate(keywords):
            if self._stop_bot or replies_count >= max_replies:
                break
            if daily_done + replies_count >= daily_limit:
                cb(f"Daily limit ({daily_limit}) reached. Stopping.")
                break

            cb(f"🔍 Searching: '{kw}' ({i+1}/{total_keywords})")

            search_url = f"https://x.com/search?q={kw.strip().replace(' ', '%20')}&f=live"
            try:
                await self.browser.navigate(search_url)
                # Twitter uses React client-side rendering. Wait for tweets.
                cb("⏳ Waiting for X/Twitter to load...")
                await self.browser.page.wait_for_selector("article", timeout=12000)
                await asyncio.sleep(1)  # short settle time
            except Exception as e:
                cb(f"⚠️ Navigation/Load error: {e}")
                continue

            # Collect unique tweet URLs not yet processed
            elements = await self.browser.page.query_selector_all("a[href*='/status/']")
            candidate_urls = []
            seen_ids = set()
            # Sub-paths that are NOT tweet URLs
            _excluded_subpaths = ("/photo/", "/video/", "/analytics", "/quotes", "/retweets", "/bookmarked_by", "/likes")
            for el in elements:
                if self._stop_bot:
                    break
                try:
                    href = await el.get_attribute("href")
                    if not href or "/status/" not in href:
                        continue
                    # Skip known non-tweet sub-paths
                    if any(sub in href for sub in _excluded_subpaths):
                        continue
                    clean = ("https://x.com" + href.split('?')[0]
                             if href.startswith('/') else href.split('?')[0])
                    tid = clean.rstrip('/').split('/')[-1]
                    # Twitter status IDs are always numeric
                    if not tid.isdigit():
                        continue
                    if tid in seen_ids or self.is_processed(tid, "twitter"):
                        continue
                    seen_ids.add(tid)
                    candidate_urls.append((clean, tid))
                except Exception:
                    continue
                if len(candidate_urls) >= (max_replies - replies_count) * 3:
                    break

            cb(f"📋 Found {len(candidate_urls)} new tweets for '{kw}'")

            for url, tweet_id in candidate_urls:
                if self._stop_bot or replies_count >= max_replies:
                    break
                if daily_done + replies_count >= daily_limit:
                    break

                cb(f"📄 Reading tweet...")

                try:
                    await self.browser.navigate(url)
                    await asyncio.sleep(random.uniform(1.0, 1.5))
                    await self._random_scroll()
                except Exception as e:
                    cb(f"⚠️ Navigation error for tweet: {e}")
                    continue

                # Extract actual tweet text
                tweet_text = await self._extract_tweet_text()

                # Skip spam / hostile content
                if self._is_spam_or_hostile(tweet_text):
                    cb(f"⏭️ Skipping (spam/hostile)")
                    self.mark_processed(tweet_id, "twitter", "[SKIPPED-SPAM]")
                    continue

                # Generate AI comment
                comment = ""
                if mode == "AI":
                    context_hint = f"Your style/intent: {prompt_context}. " if prompt_context else ""
                    ai_prompt = (
                        f"You are commenting on a tweet. Write a short (1-2 sentence), "
                        f"natural, human-like reply. Do NOT start with 'I' or use hashtags. "
                        f"Do NOT quote the tweet.\n"
                        f"{context_hint}"
                        f"Tweet: \"{tweet_text[:500]}\"\n\n"
                        f"Reply:"
                    )
                    raw = self.llm.generate_text(ai_prompt)
                    # Clean up any leading/trailing quotes or labels
                    comment = raw.strip().strip('"').strip("Reply:").strip()
                    if not comment or comment.startswith("ERROR"):
                        comment = "Really interesting perspective! Thanks for sharing."

                    cb(f"💬 Generated: {comment[:60]}...")
                else:
                    comment = prompt_context if prompt_context else "Great point! Thanks for sharing."

                # Post the reply
                result = await self._post_reply_on_page(comment)

                if "✅" in result:
                    replies_count += 1
                    self.mark_processed(tweet_id, "twitter", comment)
                    self.increment_daily_count()
                    cb(f"✅ Reply {replies_count}/{max_replies} posted!")

                    wait = random.uniform(delay_range[0], delay_range[1])
                    cb(f"⏳ Waiting {int(wait)}s before next reply (anti-rate-limit)...")
                    # Break sleep into 1s chunks so stop_bot can interrupt
                    for _ in range(int(wait)):
                        if self._stop_bot:
                            break
                        await asyncio.sleep(1)
                else:
                    cb(f"❌ Failed: {result}")

        if self._stop_bot:
            return f"Bot stopped manually. Replies sent: {replies_count}"
        return f"✅ Bot finished. Replies sent: {replies_count} | Daily total: {daily_done + replies_count}"

    async def _post_reply_on_page(self, comment_text: str) -> str:
        """
        Post a reply on the currently loaded tweet page.
        - Clears box before typing (prevents double-text on retry)
        - Verifies submission by checking box disappears
        """
        reply_box = "[data-testid='tweetTextarea_0']"

        for attempt in range(3):
            try:
                # Open the reply box if not visible
                if not await self.browser.page.is_visible(reply_box):
                    try:
                        await self.browser.page.click("[data-testid='reply']", timeout=2000)
                        await asyncio.sleep(0.5)
                    except Exception:
                        pass

                if not await self.browser.page.is_visible(reply_box):
                    await self._random_scroll()
                    await asyncio.sleep(1.5)
                    continue

                # ── CLEAR the box before typing (Ctrl+A → Delete) ──
                await self.browser.page.click(reply_box)
                await asyncio.sleep(0.3)
                await self.browser.page.keyboard.press("Control+a")
                await asyncio.sleep(0.15)
                await self.browser.page.keyboard.press("Delete")
                await asyncio.sleep(0.3)

                # Type comment character-by-character
                await self._type_like_human(reply_box, comment_text)
                await asyncio.sleep(random.uniform(0.2, 0.4))

                # ── Submit ──
                # Try clicking the Post/Tweet button
                posted = False
                try:
                    await self.browser.page.click("[data-testid='tweetButton']", timeout=4000)
                    posted = True
                except Exception:
                    pass

                # Fallback: Ctrl+Enter also submits tweets
                if not posted:
                    await self.browser.page.keyboard.press("Control+Enter")
                    posted = True

                await asyncio.sleep(1.0)

                # ── Verify submission ──
                # If the reply box is GONE or EMPTY, it means the tweet was submitted
                still_visible = await self.browser.page.is_visible(reply_box)
                if not still_visible:
                    return "✅ Reply posted successfully."

                # Check if the box is now empty (dialog closed and re-opened blank)
                try:
                    box_text = await self.browser.page.inner_text(reply_box)
                    if not box_text.strip():
                        return "✅ Reply posted successfully."
                except Exception:
                    pass

                # If box still has our text — submission likely failed; clear and retry
                await self.browser.page.keyboard.press("Control+a")
                await self.browser.page.keyboard.press("Delete")

            except Exception as e:
                if attempt == 2:
                    return f"Error posting reply: {e}"
                await asyncio.sleep(2)

        return "Error: Could not confirm reply submission after 3 attempts."

    # ─────────────────────────────────────────────
    # Single-URL comment methods
    # ─────────────────────────────────────────────

    async def auto_comment_twitter(self, post_url: str, comment_text: str, human_like=True) -> str:
        """Post a single comment on a specific Twitter/X post URL."""
        if not self.browser.page:
            await self.browser.start()

        try:
            await self.browser.navigate(post_url, wait_until="domcontentloaded")
            await asyncio.sleep(4)
        except Exception as e:
            return f"Error navigating to post: {e}"

        title = await self.browser.get_title()
        if "log in" in title.lower() or "login" in title.lower():
            return "Error: Not logged in to Twitter."

        return await self._post_reply_on_page(comment_text)

    async def auto_comment_facebook(self, post_url: str, comment_text: str) -> str:
        """Post a single comment on a Facebook post URL."""
        if not self.browser.page:
            await self.browser.start()

        await self.browser.navigate(post_url, wait_until="domcontentloaded")
        await asyncio.sleep(4)

        title = await self.browser.get_title()
        if "log in" in title.lower() or "login" in title.lower():
            return "Error: Not logged in to Facebook. Use the Accounts tab to sign in first."

        try:
            comment_box_selectors = [
                "div[aria-label='Write a comment…'][contenteditable='true']",
                "div[aria-label='Write a comment'][contenteditable='true']",
                "div[role='textbox'][contenteditable='true']",
                "div[data-lexical-editor='true']"
            ]

            clicked = False
            for sel in comment_box_selectors:
                try:
                    await self.browser.click(sel)
                    await asyncio.sleep(1)
                    clicked = True
                    break
                except Exception:
                    continue

            if not clicked:
                await self.browser.scroll(0, 600)
                await asyncio.sleep(1)
                for sel in comment_box_selectors:
                    try:
                        await self.browser.click(sel)
                        clicked = True
                        break
                    except Exception:
                        continue

            if not clicked:
                return "Error: Could not find Facebook comment box."

            await self.browser.page.keyboard.type(comment_text, delay=30)
            await asyncio.sleep(0.5)
            await self.browser.press_key("Enter")
            await asyncio.sleep(2)
            return "✅ Comment posted on Facebook successfully."
        except Exception as e:
            return f"Error auto-commenting on Facebook: {e}"

    async def auto_message_whatsapp(self, target: str, message_text: str) -> str:
        """Send a single message on WhatsApp Web given a phone number or URL."""
        if not self.browser.page:
            await self.browser.start()

        if "chat.whatsapp.com" in target or "wa.me" in target:
            target_url = target if target.startswith("http") else f"https://{target}"
        else:
            clean_number = re.sub(r'\D', '', target)
            target_url = f"https://web.whatsapp.com/send/?phone={clean_number}"

        try:
            await self.browser.navigate(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)  # Let WhatsApp Web load

            # Fallbacks for the message input box selector
            selectors = [
                "div[title='Type a message']",
                "div[aria-label='Type a message']",
                "div[aria-placeholder='Type a message']",
                "div[contenteditable='true'][data-tab='10']",
                "div[contenteditable='true'][data-tab='1']"
            ]

            clicked = False
            for _ in range(15):  # Wait up to ~30s for the chat to fully load
                for sel in selectors:
                    if await self.browser.page.is_visible(sel):
                        await self.browser.page.click(sel)
                        clicked = True
                        break
                if clicked:
                    break
                await asyncio.sleep(2)

            if not clicked:
                return "Error: Could not find WhatsApp message box. Are you logged in via Accounts tab?"

            await self.browser.page.keyboard.type(message_text, delay=30)
            await asyncio.sleep(0.5)
            await self.browser.page.keyboard.press("Enter")
            await asyncio.sleep(2)
            return "✅ Message sent on WhatsApp successfully."
        except Exception as e:
            return f"Error messaging on WhatsApp: {e}"

    async def check_unread_whatsapp_messages(self, prompt_context: str, progress_callback=None, max_replies=5):
        """Scans WhatsApp Web for unread messages and uses the LLM to reply to them autonomously."""
        def cb(msg):
            if progress_callback: progress_callback(msg)
            
        if not self.browser.page:
            await self.browser.start()
            
        self.reset_stop()
        
        cb("🌐 Opening WhatsApp Web...")
        await self.browser.navigate("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        cb("⏳ Waiting for WhatsApp to sync chats (this could take 10-30s)...")
        try:
            # chat list container or search
            await self.browser.page.wait_for_selector("div[data-testid='chat-list-search']", timeout=30000)
        except Exception:
            cb("⚠️ Timeout waiting for chat list. Make sure you are logged in via Accounts tab!")
            return "Timeout checking messages."
            
        await asyncio.sleep(2)
        replies_sent = 0
        
        for _ in range(max_replies):
            if self._stop_bot:
                cb("⏹ Autoresponder stopped by user.")
                break
                
            cb("🔍 Scanning for unread badges...")
            # Common selectors for WhatsApp unread badges
            unread_selectors = [
                "span[aria-label*='unread message']",
                "div[aria-label*='unread message']",
                "span[aria-label*='Unread']",
                "span[aria-label*='unread']"
            ]
            
            unread_element = None
            for sel in unread_selectors:
                elements = await self.browser.page.query_selector_all(sel)
                if elements:
                    unread_element = elements[0]
                    break
                    
            if not unread_element:
                cb("✅ No more unread messages found.")
                break
                
            cb("📩 Found an unread chat. Opening it...")
            await unread_element.click()
            await asyncio.sleep(2)
            
            cb("👀 Reading recent messages...")
            msg_elements = await self.browser.page.query_selector_all("div[data-testid='msg-container']")
            
            chat_history = ""
            if msg_elements:
                recent_msgs = msg_elements[-5:] 
                for el in recent_msgs:
                    text = await el.inner_text()
                    chat_history += f"Message: {text}\n"
            else:
                chat_history = "Could not extract message text."
                
            cb("🧠 Generating AI reply...")
            ai_prompt = (
                "You are an AI assistant managing the user's WhatsApp.\n"
                f"User Instructions: {prompt_context}\n\n"
                f"Recent Messages in this chat:\n{chat_history}\n\n"
                "Write a short, natural, conversational reply. ONLY output the message text to send. No quotes."
            )
            reply_text = self.llm.generate_text(ai_prompt)
            
            if not reply_text or "Error" in reply_text:
                cb("⚠️ AI failed to generate a reply. Skipping.")
                continue
                
            cb(f"✍️ Typing reply: {reply_text[:20]}...")
            
            box_selectors = [
                 "div[title='Type a message']",
                 "div[aria-label='Type a message']",
                 "div[contenteditable='true'][data-tab='10']",
                 "div[contenteditable='true'][data-tab='1']"
            ]
            
            clicked = False
            for sel in box_selectors:
                if await self.browser.page.is_visible(sel):
                    await self.browser.page.click(sel)
                    clicked = True
                    break
                    
            if not clicked:
                cb("⚠️ Could not find the text input box. Skipping chat.")
                continue
                
            await self.browser.page.keyboard.type(reply_text, delay=20)
            await asyncio.sleep(0.5)
            await self.browser.page.keyboard.press("Enter")
            
            cb("✅ Sent!")
            replies_sent += 1
            await asyncio.sleep(3)
            
        return f"Autoresponder finished. Replied to {replies_sent} chats. (Or hit max limit)"

    async def check_unread_whatsapp_messages(self, prompt_context: str, progress_callback=None, max_replies=5):
        """Scans WhatsApp Web for unread messages and uses the LLM to reply to them autonomously."""
        def cb(msg):
            if progress_callback: progress_callback(msg)
            
        if not self.browser.page:
            await self.browser.start()
            
        self.reset_stop()
        
        cb("🌐 Opening WhatsApp Web...")
        await self.browser.navigate("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        cb("⏳ Waiting for WhatsApp to sync chats (this could take 10-30s)...")
        try:
            # WhatsApp frequently rotates its DOM. We wait for any of these standard chat-list indicators.
            await self.browser.page.wait_for_selector("div#pane-side, div[data-testid='chat-list-search'], div[aria-label*='Search']", timeout=30000)
        except Exception:
            cb("⚠️ Timeout waiting for chat list. Make sure you are logged in via Accounts tab!")
            return "Timeout checking messages."
            
        await asyncio.sleep(2)
        replies_sent = 0
        
        for _ in range(max_replies):
            if self._stop_bot:
                cb("⏹ Autoresponder stopped by user.")
                break
                
            cb("🔍 Scanning for unread badges...")
            # Advanced Playwright selectors: We look for the entire chat row that contains ANY element with an "unread" aria-label
            # This perfectly bypasses WhatsApp's random class/span changes
            unread_selectors = [
                "div[role='row']:has(*[aria-label*='unread message' i])",
                "div[role='row']:has(*[aria-label*='unread' i])",
                "div[role='listitem']:has(*[aria-label*='unread' i])",
                "#pane-side *[aria-label*='unread message' i]",
                "#pane-side *[aria-label*='unread' i]"
            ]
            
            unread_element = None
            for sel in unread_selectors:
                elements = await self.browser.page.query_selector_all(sel)
                if elements:
                    unread_element = elements[0]
                    break
                    
            if not unread_element:
                cb("✅ No more unread messages found.")
                break
                
            cb("📩 Found an unread chat. Opening it...")
            await unread_element.click()
            await asyncio.sleep(2)
            
            cb("👀 Reading recent messages...")
            # More resilient selector for WhatsApp messages:
            # We look specifically inside the main chat view (#main) for rows.
            # .copyable-text[data-pre-plain-text] holds the sender, time, and message payload universally.
            msg_elements = await self.browser.page.query_selector_all("#main div.copyable-text[data-pre-plain-text], #main div[role='row'] span.selectable-text")
            
            chat_history = ""
            if msg_elements:
                # Grab the last 5 visible text blocks
                recent_msgs = msg_elements[-5:] 
                for el in recent_msgs:
                    try:
                        text = await el.inner_text()
                        if text and len(text.strip()) > 0:
                            chat_history += f"[{text.strip()}]\n"
                    except Exception:
                        pass
            
            if not chat_history.strip():
                chat_history = "User sent an image/video, or message text could not be extracted."
                
            cb("🧠 Generating AI reply...")
            ai_prompt = (
                "You are an AI assistant managing the user's WhatsApp.\n"
                f"User Instructions: {prompt_context}\n\n"
                f"Recent Messages in this chat:\n{chat_history}\n\n"
                "Write a short, natural, conversational reply. ONLY output the message text to send. No quotes."
            )
            reply_text = self.llm.generate_text(ai_prompt)
            
            if not reply_text or "Error" in reply_text:
                cb("⚠️ AI failed to generate a reply. Skipping.")
                continue
                
            cb(f"✍️ Typing reply: {reply_text[:20]}...")
            
            box_selectors = [
                 "div[title='Type a message']",
                 "div[aria-label='Type a message']",
                 "div[contenteditable='true'][data-tab='10']",
                 "div[contenteditable='true'][data-tab='1']"
            ]
            
            clicked = False
            for sel in box_selectors:
                if await self.browser.page.is_visible(sel):
                    await self.browser.page.click(sel)
                    clicked = True
                    break
                    
            if not clicked:
                cb("⚠️ Could not find the text input box. Skipping chat.")
                continue
                
            await self.browser.page.keyboard.type(reply_text, delay=20)
            await asyncio.sleep(0.5)
            await self.browser.page.keyboard.press("Enter")
            
            cb("✅ Sent!")
            replies_sent += 1
            await asyncio.sleep(3)
            
        return f"Autoresponder finished. Replied to {replies_sent} chats."

    # ─────────────────────────────────────────────
    # Content / Trends methods
    # ─────────────────────────────────────────────

    async def research_trends(self, topic):
        """Research a topic using multiple sources."""
        if not self.browser.page:
            await self.browser.start()

        aggregated_text = ""

        await self.browser.navigate(f"https://www.google.com/search?q={topic.replace(' ', '+')}&tbm=nws")
        await asyncio.sleep(2)
        aggregated_text += f"\n--- GOOGLE NEWS ---\n{await self.browser.get_all_text()}"

        await self.browser.navigate(f"https://www.google.com/search?q=site:reddit.com+{topic.replace(' ', '+')}+after:2024")
        await asyncio.sleep(2)
        aggregated_text += f"\n--- REDDIT DISCUSSIONS ---\n{await self.browser.get_all_text()}"

        analysis_prompt = (
            f"You are a viral content strategist. Analyze this raw search data about '{topic}'.\n\n"
            f"Data:\n{aggregated_text[:8000]}\n\n"
            f"Return a JSON object with: velocity, angles (list), controversy, summary. JSON ONLY."
        )

        try:
            raw = self.llm.generate_text(analysis_prompt)
            # Try to parse JSON from the response
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {"summary": raw[:200], "angles": ["General Update"], "velocity": "Unknown"}
        except Exception as e:
            return {"summary": f"Error: {e}", "angles": ["Error"], "velocity": "Error"}

    async def generate_content_plan(self, topic, trends_context, vibe="Professional"):
        """Generate a post plan using the LLM."""
        prompt = (
            f"Write a compelling social media post about: {topic}\n"
            f"Context: {trends_context}\n"
            f"Tone/Vibe: {vibe}\n"
            f"Keep it concise (under 280 chars for Twitter-compatibility). No hashtags unless essential."
        )
        post_text = self.llm.generate_text(prompt)
        return {
            "topic": topic,
            "text": post_text,
            "image": None,
            "timestamp": datetime.now().isoformat()
        }

    async def post_to_twitter(self, content_data):
        """Navigate to Twitter and fill the compose box."""
        text = content_data.get("text", "")
        if not self.browser.page:
            await self.browser.start()

        await self.browser.navigate("https://x.com/compose/tweet", wait_until="domcontentloaded")
        await asyncio.sleep(4)

        title = await self.browser.get_title()
        if "login" in title.lower():
            return "Error: Please log in to Twitter in the Accounts tab first."

        try:
            await self._type_like_human("[data-testid='tweetTextarea_0']", text)
            return "✅ Draft filled. Review and click Post in the browser."
        except Exception as e:
            return f"Error posting to Twitter: {e}"

    async def post_to_linkedin(self, content_data):
        """Navigate to LinkedIn and fill the post box."""
        text = content_data.get("text", "")
        if not self.browser.page:
            await self.browser.start()

        await self.browser.navigate("https://www.linkedin.com/feed/")
        await asyncio.sleep(3)

        if "Login" in await self.browser.get_title():
            return "Error: Please log in to LinkedIn first."

        try:
            await self.browser.click("button.share-box-feed-entry__trigger")
            await asyncio.sleep(1)
            await self.browser.type(".ql-editor", text)
            return "✅ Draft filled. Review and click Post in the browser."
        except Exception as e:
            return f"Error posting to LinkedIn: {e}"
