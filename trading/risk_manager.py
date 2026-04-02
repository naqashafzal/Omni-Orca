"""
Risk Manager - Portfolio and risk management for trading
Handles position sizing, stop-loss, take-profit, and portfolio limits.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import json


@dataclass
class Position:
    """Represents an open trading position"""
    symbol: str
    side: str  # "LONG" or "SHORT"
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def value(self) -> float:
        """Position value at entry"""
        return self.entry_price * self.quantity
    
    def pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L"""
        if self.side == "LONG":
            return (current_price - self.entry_price) * self.quantity
        else:  # SHORT
            return (self.entry_price - current_price) * self.quantity
    
    def pnl_percent(self, current_price: float) -> float:
        """Calculate P&L as percentage"""
        return (self.pnl(current_price) / self.value) * 100


@dataclass
class Trade:
    """Represents a completed trade"""
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_percent: float
    reason: str


class Portfolio:
    """Track portfolio state and performance"""
    
    def __init__(self, initial_balance: float):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
    
    def add_position(self, position: Position):
        """Add a new position"""
        self.positions[position.symbol] = position
        self.balance -= position.value
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "Manual close") -> Optional[Trade]:
        """Close a position and record trade"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        pnl = position.pnl(exit_price)
        pnl_pct = position.pnl_percent(exit_price)
        
        trade = Trade(
            symbol=symbol,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            entry_time=position.entry_time,
            exit_time=datetime.now(),
            pnl=pnl,
            pnl_percent=pnl_pct,
            reason=reason
        )
        
        # Update balance
        self.balance += exit_price * position.quantity
        self.total_pnl += pnl
        self.daily_pnl += pnl
        
        # Record trade and remove position
        self.trade_history.append(trade)
        del self.positions[symbol]
        
        return trade
    
    def get_equity(self, current_prices: Dict[str, float]) -> float:
        """Calculate total equity (balance + position values)"""
        equity = self.balance
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            equity += current_price * position.quantity
        return equity
    
    def get_unrealized_pnl(self, current_prices: Dict[str, float]) -> float:
        """Calculate total unrealized P&L"""
        total = 0.0
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            total += position.pnl(current_price)
        return total
    
    def get_statistics(self) -> Dict:
        """Get portfolio statistics"""
        if not self.trade_history:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "total_pnl": self.total_pnl,
                "return_pct": (self.balance - self.initial_balance) / self.initial_balance * 100
            }
        
        wins = [t for t in self.trade_history if t.pnl > 0]
        losses = [t for t in self.trade_history if t.pnl < 0]
        
        total_wins = sum(t.pnl for t in wins)
        total_losses = abs(sum(t.pnl for t in losses))
        
        return {
            "total_trades": len(self.trade_history),
            "win_rate": len(wins) / len(self.trade_history) * 100,
            "avg_win": total_wins / len(wins) if wins else 0,
            "avg_loss": total_losses / len(losses) if losses else 0,
            "profit_factor": total_wins / total_losses if total_losses > 0 else 0,
            "total_pnl": self.total_pnl,
            "return_pct": (self.balance - self.initial_balance) / self.initial_balance * 100
        }


class RiskManager:
    """Manage trading risk and position sizing"""
    
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
        self.config = {
            "max_position_size_pct": 10.0,  # Max 10% of portfolio per position
            "max_total_exposure_pct": 50.0,  # Max 50% total exposure
            "max_daily_loss_pct": 5.0,  # Max 5% loss per day
            "max_drawdown_pct": 20.0,  # Max 20% drawdown from peak
            "default_stop_loss_pct": 2.0,  # Default 2% stop loss
            "default_take_profit_pct": 6.0,  # Default 6% take profit (3:1 R:R)
            "position_sizing_method": "fixed_percent",  # "fixed_percent", "fixed_amount", "kelly"
            "risk_per_trade_pct": 1.0  # Risk 1% of portfolio per trade
        }
        self.peak_equity = portfolio.initial_balance
    
    def configure(self, **kwargs):
        """Update risk management configuration"""
        self.config.update(kwargs)
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss_pct: Optional[float] = None) -> float:
        """Calculate position size based on risk management rules"""
        if stop_loss_pct is None:
            stop_loss_pct = self.config["default_stop_loss_pct"]
        
        method = self.config["position_sizing_method"]
        
        if method == "fixed_percent":
            # Fixed percentage of portfolio
            max_value = self.portfolio.balance * (self.config["max_position_size_pct"] / 100)
            return max_value / entry_price
        
        elif method == "fixed_amount":
            # Fixed dollar amount
            fixed_amount = self.config.get("fixed_position_amount", 1000)
            return fixed_amount / entry_price
        
        elif method == "kelly":
            # Kelly Criterion (simplified)
            stats = self.portfolio.get_statistics()
            win_rate = stats["win_rate"] / 100
            avg_win = stats["avg_win"]
            avg_loss = stats["avg_loss"]
            
            if avg_loss == 0 or win_rate == 0:
                # Fallback to fixed percent
                max_value = self.portfolio.balance * (self.config["max_position_size_pct"] / 100)
                return max_value / entry_price
            
            # Kelly % = W - [(1 - W) / R] where W = win rate, R = avg_win/avg_loss
            r = avg_win / avg_loss
            kelly_pct = win_rate - ((1 - win_rate) / r)
            kelly_pct = max(0, min(kelly_pct, 0.25))  # Cap at 25%
            
            max_value = self.portfolio.balance * kelly_pct
            return max_value / entry_price
        
        else:
            # Risk-based sizing
            risk_amount = self.portfolio.balance * (self.config["risk_per_trade_pct"] / 100)
            stop_loss_amount_per_unit = entry_price * (stop_loss_pct / 100)
            return risk_amount / stop_loss_amount_per_unit
    
    def calculate_stop_loss(self, entry_price: float, side: str = "LONG") -> float:
        """Calculate stop loss price"""
        stop_pct = self.config["default_stop_loss_pct"] / 100
        
        if side == "LONG":
            return entry_price * (1 - stop_pct)
        else:  # SHORT
            return entry_price * (1 + stop_pct)
    
    def calculate_take_profit(self, entry_price: float, side: str = "LONG") -> float:
        """Calculate take profit price"""
        tp_pct = self.config["default_take_profit_pct"] / 100
        
        if side == "LONG":
            return entry_price * (1 + tp_pct)
        else:  # SHORT
            return entry_price * (1 - tp_pct)
    
    def validate_trade(self, symbol: str, action: str, quantity: float, price: float, current_prices: Dict[str, float]) -> Tuple[bool, str]:
        """Validate if a trade meets risk criteria"""
        
        # Check if already have position
        if symbol in self.portfolio.positions:
            return False, f"Already have position in {symbol}"
        
        # Calculate position value
        position_value = quantity * price
        
        # Check max position size
        max_position_value = self.portfolio.balance * (self.config["max_position_size_pct"] / 100)
        if position_value > max_position_value:
            return False, f"Position size ${position_value:.2f} exceeds max ${max_position_value:.2f}"
        
        # Check total exposure
        current_exposure = sum(pos.value for pos in self.portfolio.positions.values())
        total_exposure = current_exposure + position_value
        max_exposure = self.portfolio.balance * (self.config["max_total_exposure_pct"] / 100)
        
        if total_exposure > max_exposure:
            return False, f"Total exposure ${total_exposure:.2f} exceeds max ${max_exposure:.2f}"
        
        # Check daily loss limit
        equity = self.portfolio.get_equity(current_prices)
        max_daily_loss = self.portfolio.initial_balance * (self.config["max_daily_loss_pct"] / 100)
        
        if self.portfolio.daily_pnl < -max_daily_loss:
            return False, f"Daily loss limit reached: ${self.portfolio.daily_pnl:.2f}"
        
        # Check drawdown limit
        self.peak_equity = max(self.peak_equity, equity)
        drawdown_pct = ((self.peak_equity - equity) / self.peak_equity) * 100
        
        if drawdown_pct > self.config["max_drawdown_pct"]:
            return False, f"Drawdown {drawdown_pct:.1f}% exceeds max {self.config['max_drawdown_pct']}%"
        
        # Check sufficient balance
        if position_value > self.portfolio.balance:
            return False, f"Insufficient balance: ${self.portfolio.balance:.2f} < ${position_value:.2f}"
        
        return True, "Trade validated"
    
    def check_stop_loss_take_profit(self, current_prices: Dict[str, float]) -> List[Tuple[str, str]]:
        """Check if any positions hit stop loss or take profit"""
        triggers = []
        
        for symbol, position in list(self.portfolio.positions.items()):
            current_price = current_prices.get(symbol)
            if not current_price:
                continue
            
            # Check stop loss
            if position.stop_loss:
                if (position.side == "LONG" and current_price <= position.stop_loss) or \
                   (position.side == "SHORT" and current_price >= position.stop_loss):
                    triggers.append((symbol, "STOP_LOSS"))
            
            # Check take profit
            if position.take_profit:
                if (position.side == "LONG" and current_price >= position.take_profit) or \
                   (position.side == "SHORT" and current_price <= position.take_profit):
                    triggers.append((symbol, "TAKE_PROFIT"))
        
        return triggers
    
    def reset_daily_pnl(self):
        """Reset daily P&L counter (call at start of each day)"""
        self.portfolio.daily_pnl = 0.0
    
    def get_risk_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Get current risk metrics"""
        equity = self.portfolio.get_equity(current_prices)
        total_exposure = sum(pos.value for pos in self.portfolio.positions.values())
        exposure_pct = (total_exposure / equity * 100) if equity > 0 else 0
        
        drawdown_pct = ((self.peak_equity - equity) / self.peak_equity) * 100 if self.peak_equity > 0 else 0
        
        return {
            "equity": equity,
            "balance": self.portfolio.balance,
            "total_exposure": total_exposure,
            "exposure_pct": exposure_pct,
            "open_positions": len(self.portfolio.positions),
            "daily_pnl": self.portfolio.daily_pnl,
            "total_pnl": self.portfolio.total_pnl,
            "drawdown_pct": drawdown_pct,
            "peak_equity": self.peak_equity
        }
