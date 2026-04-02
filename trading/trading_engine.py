"""
Trading Engine - Core Technical Analysis and Indicator Calculations
Provides technical indicators and market data management for trading strategies.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> List[float]:
        """Simple Moving Average"""
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            avg = sum(prices[i - period + 1:i + 1]) / period
            sma_values.append(avg)
        return sma_values
    
    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        """Exponential Moving Average"""
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema_values = []
        
        # Start with SMA for first value
        sma = sum(prices[:period]) / period
        ema_values.append(sma)
        
        # Calculate EMA for remaining values
        for price in prices[period:]:
            ema = (price - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return []
        
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        rsi_values = []
        
        # First RSI value
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))
        
        # Subsequent RSI values
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
        
        return rsi_values
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return {"macd": [], "signal": [], "histogram": []}
        
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)
        
        # Align the EMAs (slow starts later)
        offset = slow - fast
        ema_fast = ema_fast[offset:]
        
        # Calculate MACD line
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(ema_slow))]
        
        # Calculate signal line (EMA of MACD)
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        
        # Align MACD with signal
        macd_aligned = macd_line[len(macd_line) - len(signal_line):]
        
        # Calculate histogram
        histogram = [macd_aligned[i] - signal_line[i] for i in range(len(signal_line))]
        
        return {
            "macd": macd_aligned,
            "signal": signal_line,
            "histogram": histogram
        }
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
        """Bollinger Bands"""
        if len(prices) < period:
            return {"upper": [], "middle": [], "lower": []}
        
        middle = TechnicalIndicators.sma(prices, period)
        
        upper = []
        lower = []
        
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            std = np.std(window)
            idx = i - period + 1
            
            upper.append(middle[idx] + (std_dev * std))
            lower.append(middle[idx] - (std_dev * std))
        
        return {
            "upper": upper,
            "middle": middle,
            "lower": lower
        }
    
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
        """Average True Range (for volatility)"""
        if len(highs) < period + 1:
            return []
        
        true_ranges = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i - 1])
            low_close = abs(lows[i] - closes[i - 1])
            true_ranges.append(max(high_low, high_close, low_close))
        
        # First ATR is simple average
        atr_values = [sum(true_ranges[:period]) / period]
        
        # Subsequent ATRs use smoothing
        for i in range(period, len(true_ranges)):
            atr = (atr_values[-1] * (period - 1) + true_ranges[i]) / period
            atr_values.append(atr)
        
        return atr_values


class MarketData:
    """Manage market data and price history"""
    
    def __init__(self):
        self.price_history: Dict[str, List[Dict]] = {}
        self.current_prices: Dict[str, float] = {}
    
    def update_price(self, symbol: str, price: float, timestamp: Optional[datetime] = None):
        """Update current price for a symbol"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.current_prices[symbol] = price
        
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            "timestamp": timestamp,
            "price": price
        })
        
        # Keep only last 1000 data points
        if len(self.price_history[symbol]) > 1000:
            self.price_history[symbol] = self.price_history[symbol][-1000:]
    
    def get_prices(self, symbol: str, count: int = 100) -> List[float]:
        """Get recent price history"""
        if symbol not in self.price_history:
            return []
        
        history = self.price_history[symbol][-count:]
        return [item["price"] for item in history]
    
    def get_ohlc(self, symbol: str, count: int = 100) -> Dict[str, List[float]]:
        """Get OHLC data (simplified - uses price as all values)"""
        prices = self.get_prices(symbol, count)
        return {
            "open": prices,
            "high": prices,
            "low": prices,
            "close": prices
        }


class TradingSignal:
    """Represents a trading signal"""
    
    def __init__(self, symbol: str, action: str, confidence: float, reason: str, price: float):
        self.symbol = symbol
        self.action = action  # "BUY", "SELL", "HOLD"
        self.confidence = confidence  # 0.0 to 1.0
        self.reason = reason
        self.price = price
        self.timestamp = datetime.now()
    
    def __repr__(self):
        return f"Signal({self.action} {self.symbol} @ {self.price:.2f}, confidence={self.confidence:.2f})"


class TradingEngine:
    """Core trading engine that coordinates strategies and execution"""
    
    def __init__(self):
        self.market_data = MarketData()
        self.indicators = TechnicalIndicators()
        self.active_strategy = None
        self.is_running = False
    
    def set_strategy(self, strategy):
        """Set the active trading strategy"""
        self.active_strategy = strategy
        strategy.set_engine(self)
    
    def analyze(self, symbol: str) -> Optional[TradingSignal]:
        """Analyze a symbol and generate trading signal"""
        if not self.active_strategy:
            return None
        
        return self.active_strategy.generate_signal(symbol)
    
    def get_indicator(self, symbol: str, indicator_name: str, **kwargs) -> List[float]:
        """Get indicator values for a symbol"""
        prices = self.market_data.get_prices(symbol, kwargs.get('lookback', 200))
        
        if not prices:
            return []
        
        if indicator_name == "RSI":
            return self.indicators.rsi(prices, kwargs.get('period', 14))
        elif indicator_name == "SMA":
            return self.indicators.sma(prices, kwargs.get('period', 20))
        elif indicator_name == "EMA":
            return self.indicators.ema(prices, kwargs.get('period', 20))
        elif indicator_name == "MACD":
            return self.indicators.macd(prices, 
                                       kwargs.get('fast', 12),
                                       kwargs.get('slow', 26),
                                       kwargs.get('signal', 9))
        elif indicator_name == "BB":
            return self.indicators.bollinger_bands(prices,
                                                  kwargs.get('period', 20),
                                                  kwargs.get('std_dev', 2.0))
        else:
            return []
    
    def start(self):
        """Start the trading engine"""
        self.is_running = True
        print("Trading Engine started")
    
    def stop(self):
        """Stop the trading engine"""
        self.is_running = False
        print("Trading Engine stopped")
