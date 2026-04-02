"""
Trading Strategies - Pre-built algorithmic trading strategies
Implements various technical analysis-based trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional
from trading.trading_engine import TradingSignal
from datetime import datetime


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.engine = None
        self.config = {}
    
    def set_engine(self, engine):
        """Set the trading engine reference"""
        self.engine = engine
    
    def configure(self, **kwargs):
        """Configure strategy parameters"""
        self.config.update(kwargs)
    
    @abstractmethod
    def generate_signal(self, symbol: str) -> Optional[TradingSignal]:
        """Generate trading signal for a symbol"""
        pass


class RSIStrategy(BaseStrategy):
    """RSI-based mean reversion strategy"""
    
    def __init__(self):
        super().__init__("RSI Strategy")
        self.config = {
            "period": 14,
            "oversold": 30,
            "overbought": 70,
            "lookback": 100
        }
    
    def generate_signal(self, symbol: str) -> Optional[TradingSignal]:
        """Generate signal based on RSI levels"""
        if not self.engine:
            return None
        
        # Get RSI values
        rsi_values = self.engine.get_indicator(
            symbol, 
            "RSI", 
            period=self.config["period"],
            lookback=self.config["lookback"]
        )
        
        if not rsi_values or len(rsi_values) < 2:
            return None
        
        current_rsi = rsi_values[-1]
        prev_rsi = rsi_values[-2]
        current_price = self.engine.market_data.current_prices.get(symbol, 0)
        
        # Oversold - Buy signal
        if current_rsi < self.config["oversold"] and prev_rsi >= self.config["oversold"]:
            confidence = (self.config["oversold"] - current_rsi) / self.config["oversold"]
            return TradingSignal(
                symbol=symbol,
                action="BUY",
                confidence=min(confidence, 1.0),
                reason=f"RSI oversold: {current_rsi:.2f} < {self.config['oversold']}",
                price=current_price
            )
        
        # Overbought - Sell signal
        elif current_rsi > self.config["overbought"] and prev_rsi <= self.config["overbought"]:
            confidence = (current_rsi - self.config["overbought"]) / (100 - self.config["overbought"])
            return TradingSignal(
                symbol=symbol,
                action="SELL",
                confidence=min(confidence, 1.0),
                reason=f"RSI overbought: {current_rsi:.2f} > {self.config['overbought']}",
                price=current_price
            )
        
        # Hold
        return TradingSignal(
            symbol=symbol,
            action="HOLD",
            confidence=0.5,
            reason=f"RSI neutral: {current_rsi:.2f}",
            price=current_price
        )


class MACDStrategy(BaseStrategy):
    """MACD crossover trend-following strategy"""
    
    def __init__(self):
        super().__init__("MACD Strategy")
        self.config = {
            "fast": 12,
            "slow": 26,
            "signal": 9,
            "lookback": 100
        }
    
    def generate_signal(self, symbol: str) -> Optional[TradingSignal]:
        """Generate signal based on MACD crossovers"""
        if not self.engine:
            return None
        
        macd_data = self.engine.get_indicator(
            symbol,
            "MACD",
            fast=self.config["fast"],
            slow=self.config["slow"],
            signal=self.config["signal"],
            lookback=self.config["lookback"]
        )
        
        if not macd_data or len(macd_data.get("histogram", [])) < 2:
            return None
        
        histogram = macd_data["histogram"]
        current_hist = histogram[-1]
        prev_hist = histogram[-2]
        current_price = self.engine.market_data.current_prices.get(symbol, 0)
        
        # Bullish crossover (histogram crosses above zero)
        if current_hist > 0 and prev_hist <= 0:
            confidence = min(abs(current_hist) / 10, 1.0)  # Normalize
            return TradingSignal(
                symbol=symbol,
                action="BUY",
                confidence=confidence,
                reason=f"MACD bullish crossover (histogram: {current_hist:.4f})",
                price=current_price
            )
        
        # Bearish crossover (histogram crosses below zero)
        elif current_hist < 0 and prev_hist >= 0:
            confidence = min(abs(current_hist) / 10, 1.0)
            return TradingSignal(
                symbol=symbol,
                action="SELL",
                confidence=confidence,
                reason=f"MACD bearish crossover (histogram: {current_hist:.4f})",
                price=current_price
            )
        
        return TradingSignal(
            symbol=symbol,
            action="HOLD",
            confidence=0.5,
            reason=f"MACD no crossover (histogram: {current_hist:.4f})",
            price=current_price
        )


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands mean reversion strategy"""
    
    def __init__(self):
        super().__init__("Bollinger Bands Strategy")
        self.config = {
            "period": 20,
            "std_dev": 2.0,
            "lookback": 100
        }
    
    def generate_signal(self, symbol: str) -> Optional[TradingSignal]:
        """Generate signal based on Bollinger Bands"""
        if not self.engine:
            return None
        
        bb_data = self.engine.get_indicator(
            symbol,
            "BB",
            period=self.config["period"],
            std_dev=self.config["std_dev"],
            lookback=self.config["lookback"]
        )
        
        if not bb_data or not bb_data.get("upper"):
            return None
        
        current_price = self.engine.market_data.current_prices.get(symbol, 0)
        upper = bb_data["upper"][-1]
        lower = bb_data["lower"][-1]
        middle = bb_data["middle"][-1]
        
        # Price touches lower band - Buy
        if current_price <= lower:
            distance = (middle - current_price) / (middle - lower)
            confidence = min(distance, 1.0)
            return TradingSignal(
                symbol=symbol,
                action="BUY",
                confidence=confidence,
                reason=f"Price at lower BB: {current_price:.2f} <= {lower:.2f}",
                price=current_price
            )
        
        # Price touches upper band - Sell
        elif current_price >= upper:
            distance = (current_price - middle) / (upper - middle)
            confidence = min(distance, 1.0)
            return TradingSignal(
                symbol=symbol,
                action="SELL",
                confidence=confidence,
                reason=f"Price at upper BB: {current_price:.2f} >= {upper:.2f}",
                price=current_price
            )
        
        return TradingSignal(
            symbol=symbol,
            action="HOLD",
            confidence=0.5,
            reason=f"Price within bands: {lower:.2f} < {current_price:.2f} < {upper:.2f}",
            price=current_price
        )


class TrendFollowingStrategy(BaseStrategy):
    """EMA crossover trend-following strategy"""
    
    def __init__(self):
        super().__init__("Trend Following Strategy")
        self.config = {
            "fast_period": 9,
            "slow_period": 21,
            "lookback": 100
        }
    
    def generate_signal(self, symbol: str) -> Optional[TradingSignal]:
        """Generate signal based on EMA crossovers"""
        if not self.engine:
            return None
        
        fast_ema = self.engine.get_indicator(
            symbol,
            "EMA",
            period=self.config["fast_period"],
            lookback=self.config["lookback"]
        )
        
        slow_ema = self.engine.get_indicator(
            symbol,
            "EMA",
            period=self.config["slow_period"],
            lookback=self.config["lookback"]
        )
        
        if not fast_ema or not slow_ema or len(fast_ema) < 2:
            return None
        
        # Align arrays (slow EMA starts later)
        offset = len(slow_ema) - len(fast_ema)
        if offset > 0:
            fast_ema = fast_ema[offset:]
        
        current_fast = fast_ema[-1]
        current_slow = slow_ema[-1]
        prev_fast = fast_ema[-2]
        prev_slow = slow_ema[-2]
        
        current_price = self.engine.market_data.current_prices.get(symbol, 0)
        
        # Golden cross (fast crosses above slow)
        if current_fast > current_slow and prev_fast <= prev_slow:
            distance = abs(current_fast - current_slow) / current_slow
            confidence = min(distance * 10, 1.0)
            return TradingSignal(
                symbol=symbol,
                action="BUY",
                confidence=confidence,
                reason=f"Golden cross: Fast EMA {current_fast:.2f} > Slow EMA {current_slow:.2f}",
                price=current_price
            )
        
        # Death cross (fast crosses below slow)
        elif current_fast < current_slow and prev_fast >= prev_slow:
            distance = abs(current_fast - current_slow) / current_slow
            confidence = min(distance * 10, 1.0)
            return TradingSignal(
                symbol=symbol,
                action="SELL",
                confidence=confidence,
                reason=f"Death cross: Fast EMA {current_fast:.2f} < Slow EMA {current_slow:.2f}",
                price=current_price
            )
        
        return TradingSignal(
            symbol=symbol,
            action="HOLD",
            confidence=0.5,
            reason=f"No crossover: Fast {current_fast:.2f}, Slow {current_slow:.2f}",
            price=current_price
        )


class MultiIndicatorStrategy(BaseStrategy):
    """Combined strategy using multiple indicators for confirmation"""
    
    def __init__(self):
        super().__init__("Multi-Indicator Strategy")
        self.config = {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "ema_fast": 9,
            "ema_slow": 21,
            "lookback": 100,
            "min_confirmations": 2  # Require at least 2 indicators to agree
        }
    
    def generate_signal(self, symbol: str) -> Optional[TradingSignal]:
        """Generate signal requiring multiple indicator confirmation"""
        if not self.engine:
            return None
        
        current_price = self.engine.market_data.current_prices.get(symbol, 0)
        buy_signals = 0
        sell_signals = 0
        reasons = []
        
        # Check RSI
        rsi_values = self.engine.get_indicator(symbol, "RSI", period=self.config["rsi_period"], lookback=self.config["lookback"])
        if rsi_values:
            current_rsi = rsi_values[-1]
            if current_rsi < self.config["rsi_oversold"]:
                buy_signals += 1
                reasons.append(f"RSI oversold ({current_rsi:.1f})")
            elif current_rsi > self.config["rsi_overbought"]:
                sell_signals += 1
                reasons.append(f"RSI overbought ({current_rsi:.1f})")
        
        # Check MACD
        macd_data = self.engine.get_indicator(symbol, "MACD", fast=self.config["macd_fast"], 
                                              slow=self.config["macd_slow"], signal=self.config["macd_signal"],
                                              lookback=self.config["lookback"])
        if macd_data and macd_data.get("histogram"):
            histogram = macd_data["histogram"]
            if len(histogram) >= 2:
                if histogram[-1] > 0 and histogram[-2] <= 0:
                    buy_signals += 1
                    reasons.append("MACD bullish crossover")
                elif histogram[-1] < 0 and histogram[-2] >= 0:
                    sell_signals += 1
                    reasons.append("MACD bearish crossover")
        
        # Check EMA trend
        fast_ema = self.engine.get_indicator(symbol, "EMA", period=self.config["ema_fast"], lookback=self.config["lookback"])
        slow_ema = self.engine.get_indicator(symbol, "EMA", period=self.config["ema_slow"], lookback=self.config["lookback"])
        
        if fast_ema and slow_ema:
            if fast_ema[-1] > slow_ema[-1]:
                buy_signals += 1
                reasons.append("Uptrend (EMA)")
            elif fast_ema[-1] < slow_ema[-1]:
                sell_signals += 1
                reasons.append("Downtrend (EMA)")
        
        # Generate signal based on confirmations
        min_conf = self.config["min_confirmations"]
        
        if buy_signals >= min_conf:
            confidence = min(buy_signals / 3, 1.0)  # Max 3 indicators
            return TradingSignal(
                symbol=symbol,
                action="BUY",
                confidence=confidence,
                reason=f"{buy_signals} buy signals: " + ", ".join(reasons),
                price=current_price
            )
        
        elif sell_signals >= min_conf:
            confidence = min(sell_signals / 3, 1.0)
            return TradingSignal(
                symbol=symbol,
                action="SELL",
                confidence=confidence,
                reason=f"{sell_signals} sell signals: " + ", ".join(reasons),
                price=current_price
            )
        
        return TradingSignal(
            symbol=symbol,
            action="HOLD",
            confidence=0.5,
            reason=f"Insufficient confirmation (buy:{buy_signals}, sell:{sell_signals})",
            price=current_price
        )


# Strategy registry for easy access
STRATEGIES = {
    "RSI": RSIStrategy,
    "MACD": MACDStrategy,
    "Bollinger Bands": BollingerBandsStrategy,
    "Trend Following": TrendFollowingStrategy,
    "Multi-Indicator": MultiIndicatorStrategy
}
