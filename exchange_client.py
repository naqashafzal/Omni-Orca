"""
Exchange Client - Direct exchange API integration
Supports Binance API and paper trading simulation.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode


class Order:
    """Represents a trading order"""
    
    def __init__(self, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None):
        self.symbol = symbol
        self.side = side  # "BUY" or "SELL"
        self.order_type = order_type  # "MARKET", "LIMIT", "STOP_LOSS"
        self.quantity = quantity
        self.price = price
        self.status = "PENDING"
        self.filled_quantity = 0.0
        self.avg_fill_price = 0.0
        self.order_id = None
        self.timestamp = datetime.now()
    
    def __repr__(self):
        return f"Order({self.side} {self.quantity} {self.symbol} @ {self.price or 'MARKET'})"


class PaperTradingExchange:
    """Simulated exchange for paper trading"""
    
    def __init__(self, initial_balance: float = 10000):
        self.balances = {"USDT": initial_balance}
        self.orders: List[Order] = []
        self.order_counter = 1000
        self.current_prices: Dict[str, float] = {}
    
    def update_price(self, symbol: str, price: float):
        """Update current market price"""
        self.current_prices[symbol] = price
    
    def get_balance(self, asset: str = "USDT") -> float:
        """Get balance for an asset"""
        return self.balances.get(asset, 0.0)
    
    def get_all_balances(self) -> Dict[str, float]:
        """Get all balances"""
        return self.balances.copy()
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        return self.current_prices.get(symbol)
    
    def create_order(self, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str, Optional[Order]]:
        """Create a new order"""
        
        # Get current price
        current_price = self.current_prices.get(symbol)
        if not current_price:
            return False, f"No price data for {symbol}", None
        
        # Extract base and quote assets (e.g., BTCUSDT -> BTC, USDT)
        # Simplified: assume USDT quote
        base_asset = symbol.replace("USDT", "")
        quote_asset = "USDT"
        
        # Calculate order value
        fill_price = price if order_type == "LIMIT" and price else current_price
        order_value = quantity * fill_price
        
        # Check balance
        if side == "BUY":
            if self.balances.get(quote_asset, 0) < order_value:
                return False, f"Insufficient {quote_asset} balance", None
        else:  # SELL
            if self.balances.get(base_asset, 0) < quantity:
                return False, f"Insufficient {base_asset} balance", None
        
        # Create order
        order = Order(symbol, side, order_type, quantity, price)
        order.order_id = f"PAPER_{self.order_counter}"
        self.order_counter += 1
        
        # Execute immediately for market orders
        if order_type == "MARKET":
            order.status = "FILLED"
            order.filled_quantity = quantity
            order.avg_fill_price = current_price
            
            # Update balances
            if side == "BUY":
                self.balances[quote_asset] = self.balances.get(quote_asset, 0) - order_value
                self.balances[base_asset] = self.balances.get(base_asset, 0) + quantity
            else:  # SELL
                self.balances[base_asset] = self.balances.get(base_asset, 0) - quantity
                self.balances[quote_asset] = self.balances.get(quote_asset, 0) + order_value
        else:
            order.status = "OPEN"
        
        self.orders.append(order)
        return True, "Order created", order
    
    def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """Cancel an open order"""
        for order in self.orders:
            if order.order_id == order_id and order.status == "OPEN":
                order.status = "CANCELLED"
                return True, "Order cancelled"
        return False, "Order not found or already filled"
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        for order in self.orders:
            if order.order_id == order_id:
                return order
        return None
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders"""
        orders = [o for o in self.orders if o.status == "OPEN"]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders


class BinanceClient:
    """Binance API client for live trading"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://testnet.binance.vision/api" if testnet else "https://api.binance.com/api"
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": api_key})
    
    def _sign_request(self, params: Dict) -> str:
        """Sign request with API secret"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, signed: bool = False, **kwargs) -> Tuple[bool, any]:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        
        if signed:
            kwargs['timestamp'] = int(time.time() * 1000)
            kwargs['signature'] = self._sign_request(kwargs)
        
        try:
            if method == "GET":
                response = self.session.get(url, params=kwargs)
            elif method == "POST":
                response = self.session.post(url, params=kwargs)
            elif method == "DELETE":
                response = self.session.delete(url, params=kwargs)
            else:
                return False, "Invalid method"
            
            response.raise_for_status()
            return True, response.json()
        
        except requests.exceptions.RequestException as e:
            return False, str(e)
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        success, data = self._request("GET", "/v3/ping")
        if success:
            return True, "Connection successful"
        return False, str(data)
    
    def get_account_info(self) -> Tuple[bool, any]:
        """Get account information"""
        return self._request("GET", "/v3/account", signed=True)
    
    def get_balance(self, asset: str = "USDT") -> Optional[float]:
        """Get balance for specific asset"""
        success, data = self.get_account_info()
        if not success:
            return None
        
        for balance in data.get("balances", []):
            if balance["asset"] == asset:
                return float(balance["free"])
        return 0.0
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        success, data = self._request("GET", "/v3/ticker/price", symbol=symbol)
        if success:
            return float(data["price"])
        return None
    
    def get_all_prices(self) -> Dict[str, float]:
        """Get all symbol prices"""
        success, data = self._request("GET", "/v3/ticker/price")
        if success:
            return {item["symbol"]: float(item["price"]) for item in data}
        return {}
    
    def create_order(self, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str, Optional[Dict]]:
        """Create a new order"""
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity
        }
        
        if order_type == "LIMIT":
            if not price:
                return False, "Price required for LIMIT orders", None
            params["price"] = price
            params["timeInForce"] = "GTC"  # Good Till Cancel
        
        success, data = self._request("POST", "/v3/order", signed=True, **params)
        
        if success:
            return True, "Order created", data
        return False, str(data), None
    
    def cancel_order(self, symbol: str, order_id: int) -> Tuple[bool, str]:
        """Cancel an order"""
        success, data = self._request("DELETE", "/v3/order", signed=True, symbol=symbol, orderId=order_id)
        if success:
            return True, "Order cancelled"
        return False, str(data)
    
    def get_order(self, symbol: str, order_id: int) -> Optional[Dict]:
        """Get order status"""
        success, data = self._request("GET", "/v3/order", signed=True, symbol=symbol, orderId=order_id)
        if success:
            return data
        return None
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open orders"""
        params = {"symbol": symbol} if symbol else {}
        success, data = self._request("GET", "/v3/openOrders", signed=True, **params)
        if success:
            return data
        return []


class ExchangeClient:
    """Unified exchange client supporting both paper and live trading"""
    
    def __init__(self, mode: str = "paper", **kwargs):
        self.mode = mode
        
        if mode == "paper":
            initial_balance = kwargs.get("initial_balance", 10000)
            self.exchange = PaperTradingExchange(initial_balance)
        elif mode == "binance":
            api_key = kwargs.get("api_key")
            api_secret = kwargs.get("api_secret")
            testnet = kwargs.get("testnet", False)
            
            if not api_key or not api_secret:
                raise ValueError("API key and secret required for Binance mode")
            
            self.exchange = BinanceClient(api_key, api_secret, testnet)
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def get_balance(self, asset: str = "USDT") -> float:
        """Get balance"""
        return self.exchange.get_balance(asset)
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price"""
        return self.exchange.get_price(symbol)
    
    def update_price(self, symbol: str, price: float):
        """Update price (paper trading only)"""
        if self.mode == "paper":
            self.exchange.update_price(symbol, price)
    
    def create_market_order(self, symbol: str, side: str, quantity: float) -> Tuple[bool, str, Optional[any]]:
        """Create market order"""
        return self.exchange.create_order(symbol, side, "MARKET", quantity)
    
    def create_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Tuple[bool, str, Optional[any]]:
        """Create limit order"""
        return self.exchange.create_order(symbol, side, "LIMIT", quantity, price)
    
    def cancel_order(self, order_id: any) -> Tuple[bool, str]:
        """Cancel order"""
        if self.mode == "paper":
            return self.exchange.cancel_order(order_id)
        else:
            # Binance requires symbol, extract from order_id or pass separately
            return False, "Cancel not implemented for live mode yet"
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[any]:
        """Get open orders"""
        return self.exchange.get_open_orders(symbol)
    
    def is_paper_trading(self) -> bool:
        """Check if in paper trading mode"""
        return self.mode == "paper"
