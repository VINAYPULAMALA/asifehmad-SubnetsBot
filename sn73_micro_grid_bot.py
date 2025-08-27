#!/usr/bin/env python3
"""
SN73 Micro-Grid Bot - Early Adopter Strategy

A sophisticated micro-grid trading bot that:
- DCA purchases 0.05 TAO every 12 hours into Subnet 73 (MetaHash)  
- Creates 15% profit sell orders for each DCA position
- Caps total investment at 5.0 TAO (100 positions max)
- Manages multiple active positions simultaneously
- Early adopter play on newly launched SN73 infrastructure subnet
"""

import asyncio
import os
import time
import yaml
import json
import bittensor as bt
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import signal
import sys

console = Console()
bt.trace()

class SN73MicroGridBot:
    def __init__(self, config):
        self.config = config
        self.wallet = None
        self.sub = None
        self.running = True
        self.start_time = time.time()
        
        # Investment tracking
        self.total_invested = 0.0
        self.active_positions = []
        self.completed_trades = []
        self.position_counter = 0
        
        # Performance metrics
        self.total_profit_realized = 0.0
        self.successful_sells = 0
        self.failed_sells = 0
        
        # DCA timing control
        self.last_dca_time = 0  # Track when last DCA was executed
        
        # State persistence
        self.state_file = f"sn73_bot_state_{self.config.wallet}.json"
        
    async def initialize(self):
        """Initialize wallet and subtensor connection."""
        console.print(Panel("🚀 Initializing SN73 Micro-Grid Bot...", title="Startup", style="bold green"))
        
        # Set up wallet
        try:
            self.wallet = bt.wallet(name=self.config.wallet)
            password = os.environ.get("WALLET_PASSWORD")
            if not password:
                import getpass
                password = getpass.getpass("🔐 Enter wallet password: ")
            if password:
                self.wallet.coldkey_file.save_password_to_env(password)
                del password
            self.wallet.unlock_coldkey()
            console.print(f"✅ Wallet '{self.config.wallet}' loaded successfully")
        except Exception as e:
            console.print(Panel(f"❌ Error loading wallet: {e}", title="Error", style="bold red"))
            return False
        
        # Set up subtensor connection
        try:
            self.sub = bt.async_subtensor()
            await self.sub.initialize()
            current_block = await self.sub.get_current_block()
            console.print(f"✅ Connected to Bittensor network (Block: {current_block})")
        except Exception as e:
            console.print(Panel(f"❌ Error connecting to network: {e}", title="Error", style="bold red"))
            return False
        
        # Load previous state if exists
        self.load_state()
        
        return True
    
    async def get_wallet_balance(self):
        """Get current wallet balance with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return float(await self.sub.get_balance(self.wallet.coldkey.ss58_address))
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"⚠️ Error getting wallet balance (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(5)
                    continue
                else:
                    raise e
    
    async def get_subnet_info(self):
        """Get SN73 subnet information with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                subnets = await self.sub.all_subnets()
                for subnet in subnets:
                    if subnet.netuid == self.config.target_netuid:
                        return subnet
                return None
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"⚠️ Error getting SN73 subnet info (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(5)
                    continue
                else:
                    raise e
    
    async def get_current_holdings(self):
        """Get current alpha holdings in SN73 with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stake_info = await self.sub.get_stake_for_coldkey(coldkey_ss58=self.wallet.coldkeypub.ss58_address)
                for stake in stake_info:
                    if stake.netuid == self.config.target_netuid and stake.hotkey_ss58 == self.config.validator:
                        return float(stake.stake)
                return 0.0
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"⚠️ Error getting SN73 holdings (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(5)
                    continue
                else:
                    console.print(f"❌ Failed to get holdings after {max_retries} attempts: {e}")
                    return 0.0
    
    def is_at_investment_cap(self):
        """Check if we've reached the investment cap."""
        upper_limit = self.config.max_investment + self.config.cap_tolerance
        return self.total_invested >= upper_limit
    
    def can_resume_dca(self):
        """Check if we can resume DCA (under lower cap limit)."""
        lower_limit = self.config.max_investment - self.config.cap_tolerance
        return self.total_invested < lower_limit
    
    def get_available_balance_for_trading(self, wallet_balance):
        """Calculate how much TAO is available for trading after reserving fees."""
        if getattr(self.config, 'fee_reserve_enabled', True):
            fee_reserve = getattr(self.config, 'auto_fee_reserve', 0.04)
            return max(0, wallet_balance - fee_reserve)
        else:
            # Fall back to old min_balance method
            return max(0, wallet_balance - self.config.min_balance)
    
    def is_time_for_dca(self):
        """Check if enough time has passed since last DCA."""
        current_time = time.time()
        dca_interval_seconds = self.config.dca_interval_hours * 3600  # Convert hours to seconds
        
        if self.last_dca_time == 0:  # First DCA
            return True
            
        time_since_last_dca = current_time - self.last_dca_time
        return time_since_last_dca >= dca_interval_seconds
    
    def get_time_until_next_dca(self):
        """Get minutes until next DCA is allowed."""
        if self.last_dca_time == 0:
            return 0
        
        current_time = time.time()
        dca_interval_seconds = self.config.dca_interval_hours * 3600
        time_since_last = current_time - self.last_dca_time
        time_until_next = dca_interval_seconds - time_since_last
        
        return max(0, time_until_next / 60)  # Return minutes
    
    def save_state(self):
        """Save bot state to file."""
        try:
            state = {
                "total_invested": self.total_invested,
                "active_positions": self.active_positions,
                "completed_trades": self.completed_trades,
                "position_counter": self.position_counter,
                "total_profit_realized": self.total_profit_realized,
                "successful_sells": self.successful_sells,
                "failed_sells": self.failed_sells,
                "last_dca_time": self.last_dca_time,
                "start_time": self.start_time,
                "last_save_time": time.time()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, default=str, indent=2)
        except Exception as e:
            console.print(f"⚠️ Warning: Could not save state: {e}")
    
    def load_state(self):
        """Load bot state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                self.total_invested = float(state.get("total_invested", 0.0))
                self.active_positions = state.get("active_positions", [])
                self.completed_trades = state.get("completed_trades", [])
                self.position_counter = int(state.get("position_counter", 0))
                self.total_profit_realized = float(state.get("total_profit_realized", 0.0))
                self.successful_sells = int(state.get("successful_sells", 0))
                self.failed_sells = int(state.get("failed_sells", 0))
                self.last_dca_time = float(state.get("last_dca_time", 0))
                
                # Convert timestamp strings back to datetime objects for positions
                for position in self.active_positions:
                    if isinstance(position.get("created_timestamp"), str):
                        position["created_timestamp"] = datetime.fromisoformat(position["created_timestamp"])
                
                for trade in self.completed_trades:
                    if isinstance(trade.get("created_timestamp"), str):
                        trade["created_timestamp"] = datetime.fromisoformat(trade["created_timestamp"])
                    if isinstance(trade.get("sell_timestamp"), str):
                        trade["sell_timestamp"] = datetime.fromisoformat(trade["sell_timestamp"])
                
                console.print(f"✅ Loaded previous state: {len(self.active_positions)} active positions, {len(self.completed_trades)} completed trades")
                console.print(f"📊 Previous progress: {self.total_invested:.4f} TAO invested")
                
        except Exception as e:
            console.print(f"⚠️ Warning: Could not load previous state: {e}")
            console.print("🔄 Starting with fresh state")
    
    async def check_price_slippage(self, expected_price, trade_type="buy"):
        """Check for excessive price slippage before executing trades."""
        try:
            # Get current price again right before trade
            subnet_info = await self.get_subnet_info()
            if not subnet_info:
                return False, "Could not get current price"
            
            current_price = float(subnet_info.price)
            
            # Calculate slippage percentage
            slippage_percent = abs((current_price - expected_price) / expected_price) * 100
            
            # Check against maximum allowed slippage
            max_slippage = getattr(self.config, 'max_slippage_percent', 2.0)
            
            if slippage_percent > max_slippage:
                return False, f"Slippage too high: {slippage_percent:.2f}% > {max_slippage}%"
            
            # Check if price moved unfavorably beyond tolerance
            price_tolerance = getattr(self.config, 'price_check_tolerance', 1.0)
            
            if trade_type == "buy" and current_price > expected_price * (1 + price_tolerance/100):
                return False, f"Price increased beyond tolerance: {current_price:.6f} vs {expected_price:.6f}"
            
            if trade_type == "sell" and current_price < expected_price * (1 - price_tolerance/100):
                return False, f"Price decreased beyond tolerance: {current_price:.6f} vs {expected_price:.6f}"
            
            return True, current_price
            
        except Exception as e:
            return False, f"Error checking slippage: {e}"
    
    async def execute_dca_purchase(self):
        """Execute a single DCA purchase and create sell order."""
        try:
            # Get current SN73 alpha price
            subnet_info = await self.get_subnet_info()
            if not subnet_info:
                console.print(f"❌ Error: Could not find SN73 subnet")
                return False
            
            current_price = float(subnet_info.price)
            
            # Check price threshold
            if hasattr(self.config, 'max_entry_price') and current_price > self.config.max_entry_price:
                console.print(f"⏸️  Skipping DCA - price too high: {current_price:.6f} > {self.config.max_entry_price:.6f}")
                return True
            
            # Check wallet balance with automatic fee reservation
            wallet_balance = await self.get_wallet_balance()
            available_balance = self.get_available_balance_for_trading(wallet_balance)
            
            if available_balance < self.config.dca_amount:
                fee_reserve = getattr(self.config, 'auto_fee_reserve', 0.04)
                console.print(f"🛑 Insufficient balance for DCA: {available_balance:.4f} TAO available")
                console.print(f"   💳 Total Balance: {wallet_balance:.4f} TAO")
                console.print(f"   🔒 Fee Reserve: {fee_reserve:.4f} TAO")
                console.print(f"   💰 Need: {self.config.dca_amount:.4f} TAO for DCA")
                return False
            
            # Calculate alpha amount we'll receive
            alpha_amount = self.config.dca_amount / current_price
            
            console.print(f"🔄 Preparing DCA: {self.config.dca_amount:.4f} TAO → {alpha_amount:.6f} alpha @ {current_price:.6f}")
            
            # Check for price slippage before executing
            slippage_ok, slippage_result = await self.check_price_slippage(current_price, "buy")
            
            if not slippage_ok:
                console.print(f"⏸️  DCA skipped due to slippage: {slippage_result}")
                return True  # Continue running, just skip this purchase
            
            # Use updated price from slippage check
            if isinstance(slippage_result, (int, float)):
                current_price = float(slippage_result)
                alpha_amount = self.config.dca_amount / current_price
                console.print(f"✅ Slippage check passed, executing at: {current_price:.6f}")
            
            # Execute the stake (DCA purchase)
            success = await self.stake_sn73(self.config.dca_amount)
            
            if success:
                # Record DCA execution time
                self.last_dca_time = time.time()
                
                # Create position tracking
                self.position_counter += 1
                sell_target_price = current_price * (1 + self.config.profit_target_percent / 100)
                
                position = {
                    "id": self.position_counter,
                    "buy_price": current_price,
                    "sell_target_price": sell_target_price,
                    "alpha_amount": alpha_amount,
                    "tao_invested": self.config.dca_amount,
                    "created_timestamp": datetime.now(),
                    "status": "active",
                    "profit_percent": self.config.profit_target_percent
                }
                
                self.active_positions.append(position)
                self.total_invested += self.config.dca_amount
                
                # Save state after successful DCA
                self.save_state()
                
                console.print(f"🟢 DCA #{position['id']} CREATED:")
                console.print(f"   💰 Invested: {self.config.dca_amount:.4f} TAO")
                console.print(f"   🪙 Alpha Amount: {alpha_amount:.6f}")
                console.print(f"   📊 Buy Price: {current_price:.6f} TAO/alpha")
                console.print(f"   🎯 Sell Target: {sell_target_price:.6f} TAO/alpha (+{self.config.profit_target_percent}%)")
                console.print(f"   📈 Total Invested: {self.total_invested:.4f}/{self.config.max_investment:.1f} TAO")
                console.print("─" * 80)
                
                return True
            else:
                console.print("❌ DCA purchase failed")
                return False
                
        except Exception as e:
            console.print(f"❌ Error in DCA execution: {e}")
            return False
    
    async def stake_sn73(self, tao_amount):
        """Stake TAO in SN73 (standard Bittensor staking)."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await self.sub.add_stake(
                    wallet=self.wallet,
                    hotkey_ss58=self.config.validator,
                    netuid=self.config.target_netuid,
                    amount=bt.Balance.from_tao(tao_amount),
                    wait_for_inclusion=False,
                    wait_for_finalization=False
                )
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"⚠️ Error staking in SN73 (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(10)
                    continue
                else:
                    console.print(f"❌ Failed to stake in SN73 after {max_retries} attempts: {e}")
                    return False
    
    async def unstake_sn73(self, alpha_amount):
        """Unstake alpha from SN73 (sell position)."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await self.sub.unstake(
                    wallet=self.wallet,
                    hotkey_ss58=self.config.validator,
                    netuid=self.config.target_netuid,
                    amount=bt.Balance.from_tao(alpha_amount),
                    wait_for_inclusion=False,
                    wait_for_finalization=False
                )
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"⚠️ Error unstaking from SN73 (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(10)
                    continue
                else:
                    console.print(f"❌ Failed to unstake from SN73 after {max_retries} attempts: {e}")
                    return False
    
    async def check_and_execute_sells(self):
        """Check all active positions for sell opportunities."""
        if not self.active_positions:
            return
        
        try:
            # Get current SN73 price
            subnet_info = await self.get_subnet_info()
            if not subnet_info:
                return
            
            current_price = float(subnet_info.price)
            
            positions_to_remove = []
            
            for position in self.active_positions:
                if position["status"] != "active":
                    continue
                
                # Check if price has reached sell target
                if current_price >= position["sell_target_price"]:
                    console.print(f"🎯 Position #{position['id']} hit sell target!")
                    console.print(f"   Current Price: {current_price:.6f} >= Target: {position['sell_target_price']:.6f}")
                    
                    # Check for slippage before selling
                    slippage_ok, slippage_result = await self.check_price_slippage(current_price, "sell")
                    
                    if not slippage_ok:
                        console.print(f"⏸️  Sell skipped due to slippage: {slippage_result}")
                        continue  # Skip this position, check others
                    
                    # Use updated price from slippage check
                    if isinstance(slippage_result, (int, float)):
                        current_price = float(slippage_result)
                        console.print(f"✅ Slippage check passed for sale at: {current_price:.6f}")
                    
                    # Execute sell (unstake)
                    sell_success = await self.unstake_sn73(position["alpha_amount"])
                    
                    if sell_success:
                        # Calculate profit
                        tao_received = position["alpha_amount"] * current_price
                        profit_tao = tao_received - position["tao_invested"]
                        profit_percent = (profit_tao / position["tao_invested"]) * 100
                        
                        # Update position
                        position["status"] = "sold"
                        position["sell_price"] = current_price
                        position["tao_received"] = tao_received
                        position["profit_tao"] = profit_tao
                        position["profit_percent_actual"] = profit_percent
                        position["sell_timestamp"] = datetime.now()
                        
                        # Move to completed trades
                        self.completed_trades.append(position)
                        positions_to_remove.append(position)
                        
                        # Update metrics
                        self.total_profit_realized += profit_tao
                        self.successful_sells += 1
                        self.total_invested -= position["tao_invested"]  # Free up cap space
                        
                        # Save state after successful sell
                        self.save_state()
                        
                        console.print(f"✅ SOLD Position #{position['id']}:")
                        console.print(f"   💰 Profit: {profit_tao:.4f} TAO ({profit_percent:.2f}%)")
                        console.print(f"   📊 Sell Price: {current_price:.6f} TAO/alpha")
                        console.print(f"   🏦 TAO Received: {tao_received:.4f}")
                        console.print(f"   📈 Total Profits: {self.total_profit_realized:.4f} TAO")
                        console.print("─" * 80)
                    else:
                        console.print(f"❌ Failed to sell position #{position['id']}")
                        self.failed_sells += 1
                
                # Check for stop-loss (if configured)
                elif hasattr(self.config, 'stop_loss_percent') and self.config.stop_loss_percent > 0:
                    stop_loss_price = position["buy_price"] * (1 - abs(self.config.stop_loss_percent) / 100)
                    if current_price <= stop_loss_price:
                        console.print(f"🛑 Position #{position['id']} hit stop-loss!")
                        # Execute emergency sell
                        # (Implementation similar to regular sell above)
            
            # Remove sold positions from active list
            for position in positions_to_remove:
                self.active_positions.remove(position)
                
        except Exception as e:
            console.print(f"❌ Error checking sell opportunities: {e}")
    
    async def print_status(self):
        """Print current bot status."""
        active_count = len(self.active_positions)
        completed_count = len(self.completed_trades)
        investment_pct = (self.total_invested / self.config.max_investment) * 100
        
        # Get current balance info
        wallet_balance = await self.get_wallet_balance()
        available_balance = self.get_available_balance_for_trading(wallet_balance)
        fee_reserve = getattr(self.config, 'auto_fee_reserve', 0.04)
        
        console.print()
        console.print(f"📊 SN73 Micro-Grid Status:")
        console.print(f"   💰 Investment Progress: {self.total_invested:.2f}/{self.config.max_investment:.1f} TAO ({investment_pct:.1f}%)")
        console.print(f"   💳 Available for Trading: {available_balance:.4f} TAO (Reserve: {fee_reserve:.4f} TAO)")
        console.print(f"   📈 Active Positions: {active_count}")
        console.print(f"   ✅ Completed Trades: {completed_count}")  
        console.print(f"   💎 Total Profits: {self.total_profit_realized:.4f} TAO")
        if completed_count > 0:
            success_rate = (self.successful_sells / (self.successful_sells + self.failed_sells)) * 100
            console.print(f"   📊 Success Rate: {success_rate:.1f}%")
        console.print()
    
    def print_session_summary(self):
        """Print detailed session summary."""
        session_duration = time.time() - self.start_time
        hours = int(session_duration // 3600)
        minutes = int((session_duration % 3600) // 60)
        seconds = int(session_duration % 60)
        
        # Create summary table
        table = Table(title="📊 SN73 Micro-Grid Session Summary", box=box.ROUNDED, header_style="bold white on blue")
        table.add_column("Metric", style="cyan", justify="left")
        table.add_column("Value", style="white", justify="right")
        
        table.add_row("🎯 Target Subnet", f"SN73 (MetaHash)")
        table.add_row("⏱️ Session Duration", f"{hours}h {minutes}m {seconds}s")
        table.add_row("💰 Total Invested", f"{self.total_invested:.4f} TAO")
        table.add_row("📈 Active Positions", str(len(self.active_positions)))
        table.add_row("✅ Completed Trades", str(len(self.completed_trades)))
        table.add_row("💎 Total Profits Realized", f"{self.total_profit_realized:.4f} TAO")
        table.add_row("📊 Investment Progress", f"{(self.total_invested/self.config.max_investment)*100:.1f}%")
        
        if self.completed_trades:
            avg_profit_pct = sum([t["profit_percent_actual"] for t in self.completed_trades]) / len(self.completed_trades)
            table.add_row("📈 Average Profit %", f"{avg_profit_pct:.2f}%")
            
            success_rate = (self.successful_sells / (self.successful_sells + self.failed_sells)) * 100
            table.add_row("🎯 Success Rate", f"{success_rate:.1f}%")
        
        console.print()
        console.print(table)
        
        # Print position details
        if self.active_positions:
            console.print()
            console.print(Panel("📋 Active Positions", style="bold blue"))
            for pos in self.active_positions[-10:]:  # Show last 10
                days_waiting = (datetime.now() - pos["created_timestamp"]).days
                console.print(f"#{pos['id']:3d} | Buy: {pos['buy_price']:.6f} | Target: {pos['sell_target_price']:.6f} | Days: {days_waiting}")
        
        if self.completed_trades:
            console.print()
            console.print(Panel("📋 Recent Completed Trades", style="bold green"))
            for trade in self.completed_trades[-5:]:  # Show last 5
                console.print(f"#{trade['id']:3d} | Profit: {trade['profit_tao']:.4f} TAO ({trade['profit_percent_actual']:.2f}%)")
    
    async def micro_grid_cycle(self):
        """Execute one complete micro-grid cycle."""
        try:
            # Phase 1: DCA if under investment cap and timing is right
            if not self.is_at_investment_cap():
                if len(self.active_positions) < self.config.max_positions:
                    if self.is_time_for_dca():
                        await self.execute_dca_purchase()
                    else:
                        time_until_next = self.get_time_until_next_dca()
                        console.print(f"⏰ Next DCA in {time_until_next:.1f} minutes (interval: {self.config.dca_interval_hours}h)")
                else:
                    console.print(f"⏸️  Max positions reached ({self.config.max_positions}), skipping DCA")
            else:
                console.print(f"🛑 Investment cap reached ({self.config.max_investment} TAO), DCA paused")
            
            # Phase 2: Always check for sell opportunities
            await self.check_and_execute_sells()
            
            # Phase 3: Status update
            await self.print_status()
            
            return True
            
        except Exception as e:
            console.print(f"❌ Error in micro-grid cycle: {e}")
            console.print("🔄 Attempting to reconnect to network...")
            
            # Try to reconnect
            try:
                if self.sub:
                    await self.sub.close()
                await asyncio.sleep(10)
                self.sub = bt.async_subtensor()
                await self.sub.initialize()
                current_block = await self.sub.get_current_block()
                console.print(f"✅ Reconnected to network (Block: {current_block})")
                return True
            except Exception as reconnect_error:
                console.print(f"❌ Failed to reconnect: {reconnect_error}")
                return True  # Continue trying
    
    async def run(self):
        """Main bot loop."""
        if not await self.initialize():
            return
        
        # Print initial configuration
        max_slippage = getattr(self.config, 'max_slippage_percent', 2.0)
        price_tolerance = getattr(self.config, 'price_check_tolerance', 1.0)
        fee_reserve = getattr(self.config, 'auto_fee_reserve', 0.04)
        
        console.print(Panel(
            f"🎯 Target Subnet: SN73 (MetaHash)\n"
            f"💰 DCA Amount: {self.config.dca_amount:.4f} TAO per purchase\n"
            f"⏰ DCA Interval: {self.config.dca_interval_hours} hours\n"
            f"🎯 Profit Target: {self.config.profit_target_percent}% per position\n"
            f"🏦 Investment Cap: {self.config.max_investment:.1f} TAO\n"
            f"💲 Max Entry Price: {getattr(self.config, 'max_entry_price', 'No limit')} TAO\n"
            f"🛡️ Max Slippage: {max_slippage}%\n"
            f"📊 Price Tolerance: {price_tolerance}%\n"
            f"🔒 Fee Reserve: {fee_reserve:.4f} TAO (auto-managed)\n"
            f"🔑 Validator: {self.config.validator}",
            title="SN73 Micro-Grid Configuration",
            style="bold cyan"
        ))
        
        # Initial status
        wallet_balance = await self.get_wallet_balance()
        holdings = await self.get_current_holdings()
        console.print(f"💳 Starting Wallet Balance: {wallet_balance:.4f} TAO")
        console.print(f"🪙 Current SN73 Holdings: {holdings:.6f} alpha")
        console.print("═" * 80)
        
        try:
            while self.running:
                # Execute micro-grid cycle
                should_continue = await self.micro_grid_cycle()
                if not should_continue:
                    break
                
                # Wait for next check interval
                console.print(f"⏳ Next check in {self.config.check_interval_minutes} minutes...")
                for i in range(self.config.check_interval_minutes * 60):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            console.print("\n🛑 Bot stopped by user")
        
        finally:
            console.print()
            console.print(Panel("📊 Generating Session Summary...", style="bold yellow"))
            self.print_session_summary()
            
            if self.sub:
                await self.sub.close()
    
    def stop(self):
        """Stop the bot gracefully."""
        self.running = False

def load_config(config_file="sn73_micro_grid_config.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        return type('Config', (), config)()
    except FileNotFoundError:
        console.print(Panel(f"❌ Config file '{config_file}' not found!", title="Error", style="bold red"))
        return None
    except Exception as e:
        console.print(Panel(f"❌ Error loading config: {e}", title="Error", style="bold red"))
        return None

def signal_handler(bot):
    """Handle interrupt signals gracefully."""
    def handler(signum, frame):
        console.print("\n🛑 Received stop signal...")
        bot.stop()
    return handler

async def main():
    """Main entry point."""
    console.print(Panel("🚀 SN73 Micro-Grid Bot - Early Adopter Strategy", title="Welcome", style="bold green"))
    
    # Load configuration
    config = load_config("sn73_micro_grid_config.yaml")
    if not config:
        return
    
    # Create and run bot
    bot = SN73MicroGridBot(config)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler(bot))
    signal.signal(signal.SIGTERM, signal_handler(bot))
    
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())