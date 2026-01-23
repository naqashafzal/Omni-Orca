"""
Crypto Trader Tab Setup and Trading Logic Methods
Add these methods to the App class in gui_app.py
"""

def _setup_crypto_tab(self):
    parent = self.tab_crypto
    parent.grid_columnconfigure(1, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    
    # Left Panel: Controls
    frame_controls = ctk.CTkFrame(parent, width=350, fg_color=COLOR_PANEL)
    frame_controls.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    frame_controls.grid_propagate(False)
    
    ctk.CTkLabel(frame_controls, text="CRYPTO TRADING SYSTEM", font=("Consolas", 16, "bold")).pack(pady=20)
    
    # Strategy Selection
    ctk.CTkLabel(frame_controls, text="TRADING STRATEGY", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
    self.strategy_var = ctk.StringVar(value="RSI")
    self.option_strategy = ctk.CTkOptionMenu(frame_controls, values=list(STRATEGIES.keys()), variable=self.strategy_var, command=self.on_strategy_change)
    self.option_strategy.pack(fill="x", padx=10, pady=5)
    
    # Symbol Input
    ctk.CTkLabel(frame_controls, text="TRADING PAIR", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
    self.entry_symbol = ctk.CTkEntry(frame_controls, placeholder_text="BTCUSDT")
    self.entry_symbol.pack(fill="x", padx=10, pady=5)
    self.entry_symbol.insert(0, "BTCUSDT")
    
    # Paper Trading Toggle
    self.paper_trading_var = ctk.BooleanVar(value=True)
    self.check_paper = ctk.CTkCheckBox(frame_controls, text="📄 PAPER TRADING MODE", variable=self.paper_trading_var, font=("Consolas", 11, "bold"), text_color=COLOR_ACCENT)
    self.check_paper.pack(pady=10)
    
    # Start/Stop Buttons
    btn_frame = ctk.CTkFrame(frame_controls, fg_color="transparent")
    btn_frame.pack(fill="x", padx=10, pady=10)
    
    self.btn_start_trading = ctk.CTkButton(btn_frame, text="▶ START TRADING", command=self.start_trading, fg_color=COLOR_SUCCESS, hover_color="#00cc00", text_color="black", font=("Consolas", 12, "bold"))
    self.btn_start_trading.pack(fill="x", pady=5)
    
    self.btn_stop_trading = ctk.CTkButton(btn_frame, text="⏹ STOP TRADING", command=self.stop_trading, fg_color=COLOR_ERROR, hover_color="#cc0000", text_color="white", font=("Consolas", 12, "bold"))
    self.btn_stop_trading.pack(fill="x", pady=5)
    self.btn_stop_trading.configure(state="disabled")
    
    # Emergency Stop
    self.btn_emergency_stop = ctk.CTkButton(frame_controls, text="🚨 EMERGENCY STOP", command=self.emergency_stop, fg_color="#ff0000", hover_color="#990000", text_color="white", font=("Consolas", 14, "bold"), height=50)
    self.btn_emergency_stop.pack(fill="x", padx=10, pady=20)
    
    # Right Panel: Dashboard
    frame_dashboard = ctk.CTkScrollableFrame(parent, fg_color="transparent", label_text="LIVE DASHBOARD")
    frame_dashboard.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
    
    # Portfolio Stats
    stats_frame = ctk.CTkFrame(frame_dashboard, fg_color=COLOR_PANEL)
    stats_frame.pack(fill="x", padx=10, pady=10)
    
    ctk.CTkLabel(stats_frame, text="PORTFOLIO", font=("Consolas", 14, "bold"), text_color=COLOR_ACCENT).pack(pady=10)
    
    self.lbl_balance = ctk.CTkLabel(stats_frame, text="Balance: $10,000.00", font=("Consolas", 12))
    self.lbl_balance.pack(anchor="w", padx=20, pady=2)
    
    self.lbl_equity = ctk.CTkLabel(stats_frame, text="Equity: $10,000.00", font=("Consolas", 12))
    self.lbl_equity.pack(anchor="w", padx=20, pady=2)
    
    self.lbl_pnl = ctk.CTkLabel(stats_frame, text="Total P&L: $0.00 (0.00%)", font=("Consolas", 12))
    self.lbl_pnl.pack(anchor="w", padx=20, pady=2)
    
    self.lbl_daily_pnl = ctk.CTkLabel(stats_frame, text="Daily P&L: $0.00", font=("Consolas", 12))
    self.lbl_daily_pnl.pack(anchor="w", padx=20, pady=2)
    
    self.lbl_positions = ctk.CTkLabel(stats_frame, text="Open Positions: 0", font=("Consolas", 12))
    self.lbl_positions.pack(anchor="w", padx=20, pady=(2,10))
    
    # Open Positions
    positions_frame = ctk.CTkFrame(frame_dashboard, fg_color=COLOR_PANEL)
    positions_frame.pack(fill="x", padx=10, pady=10)
    
    ctk.CTkLabel(positions_frame, text="OPEN POSITIONS", font=("Consolas", 14, "bold"), text_color=COLOR_ACCENT).pack(pady=10)
    
    self.positions_display = ctk.CTkTextbox(positions_frame, height=150, font=("Consolas", 11))
    self.positions_display.pack(fill="x", padx=10, pady=(0,10))
    self.positions_display.insert("0.0", "No open positions")
    self.positions_display.configure(state="disabled")
    
    # Trade History
    history_frame = ctk.CTkFrame(frame_dashboard, fg_color=COLOR_PANEL)
    history_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    ctk.CTkLabel(history_frame, text="TRADE HISTORY", font=("Consolas", 14, "bold"), text_color=COLOR_ACCENT).pack(pady=10)
    
    self.trade_history_display = ctk.CTkTextbox(history_frame, font=("Consolas", 10))
    self.trade_history_display.pack(fill="both", expand=True, padx=10, pady=(0,10))
    self.trade_history_display.insert("0.0", "No trades yet")
    self.trade_history_display.configure(state="disabled")
    
    # Initialize strategy
    self.on_strategy_change("RSI")

# Trading Logic Methods

def on_strategy_change(self, strategy_name):
    """Handle strategy selection change"""
    strategy_class = STRATEGIES.get(strategy_name)
    if strategy_class:
        strategy = strategy_class()
        self.trading_engine.set_strategy(strategy)
        self.log(f"CRYPTO TRADER: Strategy changed to {strategy_name}")

def start_trading(self):
    """Start automated trading"""
    symbol = self.entry_symbol.get().strip()
    if not symbol:
        self.log("ERROR: Please enter a trading pair")
        return
    
    self.current_symbol = symbol
    self.trading_active = True
    
    # Update UI
    self.btn_start_trading.configure(state="disabled")
    self.btn_stop_trading.configure(state="normal")
    self.check_paper.configure(state="disabled")
    
    mode = "PAPER" if self.paper_trading_var.get() else "LIVE"
    self.log(f"CRYPTO TRADER: Starting {mode} trading on {symbol}")
    self.tts.speak(f"Starting {mode} trading")
    
    # Start trading loop in thread
    threading.Thread(target=self._trading_loop, daemon=True).start()

def stop_trading(self):
    """Stop automated trading"""
    self.trading_active = False
    self.btn_start_trading.configure(state="normal")
    self.btn_stop_trading.configure(state="disabled")
    self.check_paper.configure(state="normal")
    self.log("CRYPTO TRADER: Trading stopped")
    self.tts.speak("Trading stopped")

def emergency_stop(self):
    """Emergency stop - close all positions and halt trading"""
    self.trading_active = False
    
    # Close all positions
    current_prices = {self.current_symbol: self.exchange_client.get_price(self.current_symbol) or 0}
    for symbol in list(self.portfolio.positions.keys()):
        price = current_prices.get(symbol, 0)
        if price > 0:
            self.portfolio.close_position(symbol, price, "Emergency stop")
            self.log(f"EMERGENCY: Closed position in {symbol}")
    
    self.btn_start_trading.configure(state="normal")
    self.btn_stop_trading.configure(state="disabled")
    self.check_paper.configure(state="normal")
    
    self.log("🚨 EMERGENCY STOP ACTIVATED - ALL POSITIONS CLOSED")
    self.tts.speak("Emergency stop activated")
    self.update_trading_dashboard()

def _trading_loop(self):
    """Main trading loop"""
    import time
    from datetime import datetime
    
    while self.trading_active:
        try:
            # Simulate price update (in real scenario, fetch from exchange)
            # For demo, generate random price movement
            import random
            base_price = 50000 if "BTC" in self.current_symbol else 3000
            price = base_price * (1 + random.uniform(-0.02, 0.02))
            
            # Update market data
            self.trading_engine.market_data.update_price(self.current_symbol, price)
            self.exchange_client.update_price(self.current_symbol, price)
            
            # Generate trading signal
            signal = self.trading_engine.analyze(self.current_symbol)
            
            if signal and signal.action in ["BUY", "SELL"]:
                self.after(0, lambda: self.log(f"SIGNAL: {signal}"))
                
                # Check if we should execute
                if signal.action == "BUY" and self.current_symbol not in self.portfolio.positions:
                    self._execute_buy(signal)
                elif signal.action == "SELL" and self.current_symbol in self.portfolio.positions:
                    self._execute_sell(signal)
            
            # Check stop loss / take profit
            current_prices = {self.current_symbol: price}
            triggers = self.risk_manager.check_stop_loss_take_profit(current_prices)
            
            for symbol, trigger_type in triggers:
                self._close_position(symbol, price, trigger_type)
            
            # Update dashboard
            self.after(0, self.update_trading_dashboard)
            
            # Wait before next iteration
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            self.after(0, lambda: self.log(f"TRADING ERROR: {e}"))
            time.sleep(5)

def _execute_buy(self, signal):
    """Execute buy order"""
    # Calculate position size
    quantity = self.risk_manager.calculate_position_size(signal.symbol, signal.price)
    
    # Validate trade
    current_prices = {signal.symbol: signal.price}
    valid, reason = self.risk_manager.validate_trade(signal.symbol, "BUY", quantity, signal.price, current_prices)
    
    if not valid:
        self.after(0, lambda: self.log(f"TRADE REJECTED: {reason}"))
        return
    
    # Execute order
    success, msg, order = self.exchange_client.create_market_order(signal.symbol, "BUY", quantity)
    
    if success:
        # Create position
        stop_loss = self.risk_manager.calculate_stop_loss(signal.price, "LONG")
        take_profit = self.risk_manager.calculate_take_profit(signal.price, "LONG")
        
        position = Position(
            symbol=signal.symbol,
            side="LONG",
            entry_price=signal.price,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.portfolio.add_position(position)
        self.after(0, lambda: self.log(f"BUY EXECUTED: {quantity:.4f} {signal.symbol} @ ${signal.price:.2f}"))
        self.after(0, lambda: self.tts.speak("Buy order executed"))
    else:
        self.after(0, lambda: self.log(f"BUY FAILED: {msg}"))

def _execute_sell(self, signal):
    """Execute sell order"""
    position = self.portfolio.positions.get(signal.symbol)
    if not position:
        return
    
    # Execute order
    success, msg, order = self.exchange_client.create_market_order(signal.symbol, "SELL", position.quantity)
    
    if success:
        trade = self.portfolio.close_position(signal.symbol, signal.price, signal.reason)
        if trade:
            pnl_color = COLOR_SUCCESS if trade.pnl > 0 else COLOR_ERROR
            self.after(0, lambda: self.log(f"SELL EXECUTED: {trade.quantity:.4f} {signal.symbol} @ ${signal.price:.2f} | P&L: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)"))
            self.after(0, lambda: self.tts.speak(f"Sell order executed. Profit {trade.pnl:.0f} dollars" if trade.pnl > 0 else f"Loss {abs(trade.pnl):.0f} dollars"))
    else:
        self.after(0, lambda: self.log(f"SELL FAILED: {msg}"))

def _close_position(self, symbol, price, reason):
    """Close position (stop loss or take profit)"""
    trade = self.portfolio.close_position(symbol, price, reason)
    if trade:
        self.after(0, lambda: self.log(f"{reason.upper()}: Closed {symbol} @ ${price:.2f} | P&L: ${trade.pnl:.2f}"))
        self.after(0, lambda: self.tts.speak(f"{reason} triggered"))

def update_trading_dashboard(self):
    """Update trading dashboard with current stats"""
    # Get current prices
    current_price = self.exchange_client.get_price(self.current_symbol) or 0
    current_prices = {self.current_symbol: current_price}
    
    # Update portfolio stats
    equity = self.portfolio.get_equity(current_prices)
    unrealized_pnl = self.portfolio.get_unrealized_pnl(current_prices)
    total_pnl = self.portfolio.total_pnl + unrealized_pnl
    return_pct = (total_pnl / self.portfolio.initial_balance) * 100
    
    self.lbl_balance.configure(text=f"Balance: ${self.portfolio.balance:,.2f}")
    self.lbl_equity.configure(text=f"Equity: ${equity:,.2f}")
    
    pnl_color = COLOR_SUCCESS if total_pnl >= 0 else COLOR_ERROR
    self.lbl_pnl.configure(text=f"Total P&L: ${total_pnl:,.2f} ({return_pct:.2f}%)", text_color=pnl_color)
    
    daily_color = COLOR_SUCCESS if self.portfolio.daily_pnl >= 0 else COLOR_ERROR
    self.lbl_daily_pnl.configure(text=f"Daily P&L: ${self.portfolio.daily_pnl:,.2f}", text_color=daily_color)
    
    self.lbl_positions.configure(text=f"Open Positions: {len(self.portfolio.positions)}")
    
    # Update positions display
    self.positions_display.configure(state="normal")
    self.positions_display.delete("0.0", "end")
    
    if self.portfolio.positions:
        for symbol, pos in self.portfolio.positions.items():
            pnl = pos.pnl(current_prices.get(symbol, pos.entry_price))
            pnl_pct = pos.pnl_percent(current_prices.get(symbol, pos.entry_price))
            pnl_sign = "+" if pnl >= 0 else ""
            self.positions_display.insert("end", f"{symbol} | {pos.side}\n")
            self.positions_display.insert("end", f"  Entry: ${pos.entry_price:.2f} | Qty: {pos.quantity:.4f}\n")
            self.positions_display.insert("end", f"  P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%)\n")
            self.positions_display.insert("end", f"  SL: ${pos.stop_loss:.2f} | TP: ${pos.take_profit:.2f}\n\n")
    else:
        self.positions_display.insert("0.0", "No open positions")
    
    self.positions_display.configure(state="disabled")
    
    # Update trade history
    self.trade_history_display.configure(state="normal")
    self.trade_history_display.delete("0.0", "end")
    
    if self.portfolio.trade_history:
        for trade in reversed(self.portfolio.trade_history[-10:]):  # Last 10 trades
            pnl_sign = "+" if trade.pnl >= 0 else ""
            self.trade_history_display.insert("end", f"{trade.exit_time.strftime('%H:%M:%S')} | {trade.symbol} {trade.side}\n")
            self.trade_history_display.insert("end", f"  Entry: ${trade.entry_price:.2f} → Exit: ${trade.exit_price:.2f}\n")
            self.trade_history_display.insert("end", f"  P&L: {pnl_sign}${trade.pnl:.2f} ({pnl_sign}{trade.pnl_percent:.2f}%) | {trade.reason}\n\n")
    else:
        self.trade_history_display.insert("0.0", "No trades yet")
    
    self.trade_history_display.configure(state="disabled")
