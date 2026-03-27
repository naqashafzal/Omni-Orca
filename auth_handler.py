import asyncio

PLATFORM_MAP = {
    "Facebook": {
        "url": "https://www.facebook.com/login",
        "user_selector": "#email",
        "pass_selector": "#pass",
        "btn_selector": "#loginbutton"
    },
    "Twitter (X)": {
        "url": "https://twitter.com/i/flow/login",
        "user_selector": "input[autocomplete='username']",
        "pass_selector": "input[name='password']",
        "btn_selector": "div[data-testid='LoginForm_Login_Button']" # Simplified, might need multi-step logic
    },
    "LinkedIn": {
        "url": "https://www.linkedin.com/login",
        "user_selector": "#username",
        "pass_selector": "#password",
        "btn_selector": "button[type='submit']"
    },
    "Instagram": {
        "url": "https://www.instagram.com/accounts/login/",
        "user_selector": "input[name='username']",
        "pass_selector": "input[name='password']",
        "btn_selector": "button[type='submit']"
    },
    "Reddit": {
        "url": "https://www.reddit.com/login/",
        "user_selector": "#loginUsername",
        "pass_selector": "#loginPassword",
        "btn_selector": "button[type='submit']"
    },
    "WhatsApp": {
        "url": "https://web.whatsapp.com/"
    }
}

async def perform_login(agent, platform, username, password):
    """
    Executes the login flow for the given platform.
    """
    if platform not in PLATFORM_MAP:
        raise ValueError(f"Unsupported platform: {platform}")
    
    config = PLATFORM_MAP[platform]
    
    print(f"Logging into {platform}...")
    await agent.navigate(config["url"])
    await asyncio.sleep(2) # Wait for load
    
    # Special handling for Twitter's multi-step login
    if platform == "Twitter (X)":
        await _login_twitter(agent, username, password)
        return
        
    if platform == "WhatsApp":
        print("Please scan the QR code to log into WhatsApp Web.")
        return

    # Standard single-page login
    try:
        await agent.type(config["user_selector"], username)
        await agent.type(config["pass_selector"], password)
        await asyncio.sleep(0.5)
        await agent.click(config["btn_selector"])
        print(f"Login submitted for {platform}")
    except Exception as e:
        print(f"Login failed: {e}")
        raise e

async def _login_twitter(agent, username, password):
    # Step 1: Username
    await agent.type("input[autocomplete='username']", username)
    await agent.press_key("Enter")
    await asyncio.sleep(2)
    
    # Step 2: Password (sometimes asks for email/phone verification first, skipping for simplicity)
    try:
        await agent.type("input[name='password']", password)
        await agent.press_key("Enter")
    except:
        # Fallback if it asks for "unusual activity" verification
        print("Twitter login flow interrupted (verification needed?)")
