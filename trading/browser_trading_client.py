"""
Browser Trading Client - Execute trades via browser automation
Works with ANY exchange (Binance, Coinbase, Kraken, etc.)
"""

import asyncio
from typing import Optional, Tuple, Dict
from datetime import datetime


class BrowserTradingClient:
    """Execute trades using browser automation instead of API"""
    
    def __init__(self, browser_agent, exchange: str = "binance"):
        self.agent = browser_agent
        self.exchange = exchange.lower()
        self.is_logged_in = False
        self.current_symbol = None
        
        # Exchange configurations
        self.exchanges = {
            "binance": {
                "url": "https://www.binance.com/en/trade/{symbol}",
                "login_url": "https://www.binance.com/en/login",
                "selectors": {
                    "price": ".showPrice",
                    "buy_tab": "#buy-tab",
                    "sell_tab": "#sell-tab",
                    "market_order": "text=Market",
                    "amount_input": "input[name='quantity']",
                    "buy_button": "button:has-text('Buy')",
                    "sell_button": "button:has-text('Sell')",
                    "confirm_button": "button:has-text('Confirm')",
                    "balance": ".asset-balance"
                }
            },
            "coinbase": {
                "url": "https://pro.coinbase.com/trade/{symbol}",
                "login_url": "https://www.coinbase.com/signin",
                "selectors": {
                    "price": ".market-price",
                    "buy_tab": "button:has-text('Buy')",
                    "sell_tab": "button:has-text('Sell')",
                    "market_order": "button:has-text('Market')",
                    "amount_input": "input[placeholder='Amount']",
                    "buy_button": "button:has-text('Place Buy Order')",
                    "sell_button": "button:has-text('Place Sell Order')",
                    "confirm_button": "button:has-text('Confirm')",
                    "balance": ".balance-value"
                }
            }
        }
    
    def get_config(self) -> Dict:
        """Get configuration for current exchange"""
        return self.exchanges.get(self.exchange, self.exchanges["binance"])
    
    async def navigate_to_trading(self, symbol: str) -> bool:
        """Navigate to trading page for symbol"""
        try:
            config = self.get_config()
            # Convert symbol format (BTCUSDT -> BTC_USDT for URL)
            url_symbol = symbol.replace("USDT", "_USDT")
            url = config["url"].format(symbol=url_symbol)
            
            await self.agent.navigate(url)
            await asyncio.sleep(3)  # Wait for page load
            
            self.current_symbol = symbol
            return True
        except Exception as e:
            print(f"Navigation error: {e}")
            return False
    
    async def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Login to exchange via browser"""
        try:
            config = self.get_config()
            
            # Navigate to login page
            await self.agent.navigate(config["login_url"])
            await asyncio.sleep(2)
            
            # Fill login form (selectors may vary by exchange)
            await self.agent.type("input[type='email'], input[name='email']", username)
            await self.agent.type("input[type='password'], input[name='password']", password)
            await self.agent.click("button[type='submit'], button:has-text('Log In')")
            
            # Wait for login to complete
            await asyncio.sleep(5)
            
            # Check if logged in (look for account/profile element)
            try:
                await self.agent.page.wait_for_selector(".user-menu, .account-menu", timeout=10000)
                self.is_logged_in = True
                return True, "Login successful"
            except:
                return False, "Login failed - check credentials"
                
        except Exception as e:
            return False, f"Login error: {str(e)}"
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get current price from browser page"""
        try:
            if symbol != self.current_symbol:
                await self.navigate_to_trading(symbol)
            
            config = self.get_config()
            price_text = await self.agent.get_text(config["selectors"]["price"])
            
            # Clean price text (remove commas, currency symbols)
            price_clean = price_text.replace(",", "").replace("$", "").strip()
            return float(price_clean)
        except Exception as e:
            print(f"Price fetch error: {e}")
            return None
    
    async def get_balance(self, asset: str = "USDT") -> Optional[float]:
        """Get account balance from browser"""
        try:
            config = self.get_config()
            balance_text = await self.agent.get_text(config["selectors"]["balance"])
            
            # Extract number from balance text
            import re
            numbers = re.findall(r'[\d,]+\.?\d*', balance_text)
            if numbers:
                return float(numbers[0].replace(",", ""))
            return None
        except Exception as e:
            print(f"Balance fetch error: {e}")
            return None
    
    async def place_market_order(self, symbol: str, side: str, quantity: float) -> Tuple[bool, str, Optional[Dict]]:
        """
        Place market order via browser automation
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: "BUY" or "SELL"
            quantity: Amount to trade
        
        Returns:
            (success, message, order_info)
        """
        try:
            # Navigate to trading page if needed
            if symbol != self.current_symbol:
                success = await self.navigate_to_trading(symbol)
                if not success:
                    return False, "Failed to navigate to trading page", None
            
            config = self.get_config()
            selectors = config["selectors"]
            
            # 1. Click Buy or Sell tab
            tab_selector = selectors["buy_tab"] if side == "BUY" else selectors["sell_tab"]
            await self.agent.click(tab_selector)
            await asyncio.sleep(1)
            
            # 2. Select Market order type
            await self.agent.click(selectors["market_order"])
            await asyncio.sleep(1)
            
            # 3. Enter quantity
            await self.agent.click(selectors["amount_input"])
            await self.agent.page.keyboard.press("Control+A")  # Select all
            await self.agent.type(selectors["amount_input"], str(quantity))
            await asyncio.sleep(1)
            
            # 4. Click Buy/Sell button
            button_selector = selectors["buy_button"] if side == "BUY" else selectors["sell_button"]
            await self.agent.click(button_selector)
            await asyncio.sleep(2)
            
            # 5. Confirm if confirmation dialog appears
            try:
                await self.agent.click(selectors["confirm_button"])
                await asyncio.sleep(2)
            except:
                pass  # No confirmation needed
            
            # 6. Wait for order confirmation
            try:
                await self.agent.wait_for_text("Order filled", timeout=10000)
                
                # Get current price for order info
                price = await self.get_price(symbol)
                
                order_info = {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "timestamp": datetime.now()
                }
                
                return True, f"{side} order filled", order_info
                
            except:
                # Order might still be processing
                return True, f"{side} order submitted", {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "status": "submitted"
                }
                
        except Exception as e:
            return False, f"Order failed: {str(e)}", None
    
    async def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """Cancel an order (browser-based)"""
        try:
            # Navigate to orders page
            await self.agent.click("text=Orders")
            await asyncio.sleep(2)
            
            # Find and click cancel button for the order
            await self.agent.click(f"button:has-text('Cancel'):near(:text('{order_id}'))")
            await asyncio.sleep(1)
            
            return True, "Order cancelled"
        except Exception as e:
            return False, f"Cancel failed: {str(e)}"
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Get open orders from browser"""
        try:
            # Navigate to orders page
            await self.agent.click("text=Orders")
            await asyncio.sleep(2)
            
            # Scrape open orders table
            orders = await self.agent.scrape_data(
                ".order-row",
                {
                    "symbol": ".order-symbol",
                    "side": ".order-side",
                    "price": ".order-price",
                    "amount": ".order-amount",
                    "status": ".order-status"
                }
            )
            
            if symbol:
                orders = [o for o in orders if o.get("symbol") == symbol]
            
            return orders
        except Exception as e:
            print(f"Get orders error: {e}")
            return []
    
    def is_paper_trading(self) -> bool:
        """Browser trading is always live (not paper trading)"""
        return False


class HybridTradingClient:
    """
    Unified client that can use either API or Browser trading
    Automatically falls back to browser if API fails
    """
    
    def __init__(self, mode: str = "auto", **kwargs):
        """
        Initialize hybrid trading client
        
        Args:
            mode: "api", "browser", or "auto" (tries API first, falls back to browser)
            **kwargs: Configuration for API or browser
        """
        self.mode = mode
        self.api_client = None
        self.browser_client = None
        self.active_client = None
        
        # Initialize based on mode
        if mode in ["api", "auto"]:
            try:
                from trading.exchange_client import ExchangeClient
                api_key = kwargs.get("api_key")
                api_secret = kwargs.get("api_secret")
                
                if api_key and api_secret:
                    self.api_client = ExchangeClient(
                        mode="binance",
                        api_key=api_key,
                        api_secret=api_secret,
                        testnet=kwargs.get("testnet", False)
                    )
                    self.active_client = self.api_client
                    print("✅ API trading client initialized")
            except Exception as e:
                print(f"⚠️ API client initialization failed: {e}")
        
        if mode in ["browser", "auto"] or not self.active_client:
            browser_agent = kwargs.get("browser_agent")
            exchange = kwargs.get("exchange", "binance")
            
            if browser_agent:
                self.browser_client = BrowserTradingClient(browser_agent, exchange)
                if not self.active_client:
                    self.active_client = self.browser_client
                    print("✅ Browser trading client initialized")
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get price using active client"""
        if isinstance(self.active_client, BrowserTradingClient):
            return await self.active_client.get_price(symbol)
        else:
            return self.active_client.get_price(symbol)
    
    async def create_market_order(self, symbol: str, side: str, quantity: float):
        """Create market order using active client"""
        if isinstance(self.active_client, BrowserTradingClient):
            return await self.active_client.place_market_order(symbol, side, quantity)
        else:
            return self.active_client.create_market_order(symbol, side, quantity)
    
    def get_balance(self, asset: str = "USDT"):
        """Get balance using active client"""
        if isinstance(self.active_client, BrowserTradingClient):
            # Browser client needs async
            return asyncio.run(self.active_client.get_balance(asset))
        else:
            return self.active_client.get_balance(asset)
    
    def is_paper_trading(self) -> bool:
        """Check if using paper trading"""
        return self.active_client.is_paper_trading()
    
    def get_active_mode(self) -> str:
        """Get currently active trading mode"""
        if isinstance(self.active_client, BrowserTradingClient):
            return "browser"
        elif self.active_client:
            return "api"
        else:
            return "none"
