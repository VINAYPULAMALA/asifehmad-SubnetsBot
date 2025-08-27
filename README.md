# 🚀 SN73 Micro-Grid Bot - Early Adopter Strategy

A sophisticated micro-grid trading bot for **Subnet 73 (MetaHash)** - the newest OTC marketplace infrastructure subnet on Bittensor.

## 🎯 Strategy Overview

**"V2 Micro-Grid with 15% Profit Taking"**
- **DCA**: 0.05 TAO every 12 hours into SN73 alpha
- **Profit Taking**: Each DCA creates a 15% profit sell order
- **Investment Cap**: Stop at 5.0 TAO total investment
- **Timeline**: ~50 days to complete deployment

## 🔥 Why SN73 (MetaHash)?

### **Early Adopter Opportunity**
- **Launched**: April 2025 (only 4 months old!)
- **Purpose**: Decentralized OTC marketplace for Bittensor miners
- **Function**: Infrastructure layer for cross-subnet token swapping
- **Potential**: Could become essential Bittensor trading infrastructure

### **Investment Thesis**
- **First-mover advantage** in Bittensor OTC trading
- **Network effects** - more valuable as ecosystem grows
- **Infrastructure play** - utility increases with adoption
- **Early positioning** before mass market discovery

## ⚙️ How It Works

### **Phase 1: DCA Accumulation (Days 1-50)**
```python
# Every 12 hours
dca_purchase = 0.05 TAO → SN73 alpha staking
create_sell_order = current_price × 1.15 (15% profit target)
```

### **Phase 2: Position Management (Ongoing)**
```python
# Continuous monitoring
if current_price >= sell_target:
    execute_unstake() # Sell for 15% profit
    update_metrics()
    free_investment_cap() # Allow new DCA if under cap
```

### **Example Position Flow**
```
DCA #1: 0.05 TAO → 0.625 alpha @ 0.08 → Sell target: 0.092
DCA #2: 0.05 TAO → 0.667 alpha @ 0.075 → Sell target: 0.086  
DCA #3: 0.05 TAO → 0.610 alpha @ 0.082 → Sell target: 0.094

When SN73 price hits targets → Automatic unstaking for profit
```

## 📊 Expected Performance

### **Investment Schedule**
- **0.05 TAO every 12 hours** = 0.1 TAO daily
- **100 total purchases** over 50 days
- **5.0 TAO total investment** (hard cap)

### **Profit Potential (if all positions hit 15%)**
- **Total Profit**: 0.75 TAO
- **ROI**: 15% on invested capital
- **Plus**: Remaining alpha for potential appreciation

### **Timeline Milestones**
```
Week 1:  0.7 TAO invested (14%) - Initial testing
Week 2:  1.4 TAO invested (28%) - Early positions may fill  
Month 1: 2.5 TAO invested (50%) - Strategy validation
Week 7: 5.0 TAO invested (100%) - Full deployment complete
Month 3+: Sell-only mode - Position management phase
```

## 🚀 Quick Start

### **1. Setup Configuration**
```bash
# Edit sn73_micro_grid_config.yaml
validator: "your_validator_hotkey_ss58_here"  # ← UPDATE THIS
target_netuid: 73  # MetaHash subnet
```

### **2. Test Configuration**
```bash
python3 test_sn73_config.py
```

### **3. Deploy Bot**
```bash
python3 sn73_micro_grid_bot.py
```

### **4. Monitor Progress**
The bot provides real-time status updates:
```
📊 SN73 Micro-Grid Status:
   💰 Investment Progress: 2.35/5.0 TAO (47.0%)
   📈 Active Positions: 47
   ✅ Completed Trades: 15  
   💎 Total Profits: 0.127 TAO
   📊 Success Rate: 93.8%
```

## ⚠️ Risk Management

### **Built-in Safeguards**
- **Investment Cap**: Hard limit at 5.0 TAO
- **Price Filtering**: Skip DCA if SN73 price too high
- **Stop Loss**: Optional emergency exit at -25%
- **Position Limits**: Max 150 tracked positions
- **Balance Protection**: Keep minimum 1.0 TAO in wallet

### **Risk Factors**
- **Experimental Subnet**: SN73 is only 4 months old
- **Limited Liquidity**: New subnet with thin trading
- **Early Adopter Risk**: Betting on unproven infrastructure
- **Market Risk**: Crypto volatility affects all positions

## 📈 Success Metrics

### **Technical Success**
- ✅ Bot runs continuously without crashes
- ✅ Positions tracked accurately
- ✅ Sells execute when targets hit

### **Financial Success**
- 🎯 **Conservative**: 20% of positions hit 15% profit
- 🎯 **Moderate**: 50% of positions achieve targets  
- 🎯 **Optimistic**: 80%+ success rate with SN73 growth

### **Strategic Success**
- 🚀 Early position in promising infrastructure subnet
- 🚀 Profit realization funds expansion to other subnets
- 🚀 SN73 appreciation beyond 15% targets

## 🛠️ Advanced Features

### **Position Tracking**
- Individual position monitoring with buy/sell prices
- Profit/loss calculation per position
- Days waiting for each sell target
- Success rate analytics

### **Session Analytics**
- Total invested vs. cap progress
- Completed trades with profit details
- Average profit percentage achieved
- Investment timeline tracking

### **Network Resilience**  
- Auto-reconnection on network failures
- 3-retry logic for all blockchain operations
- Graceful error handling and recovery
- Comprehensive logging and reporting

## 🤝 Configuration Options

### **Conservative Setup**
```yaml
max_investment: 2.0      # Lower risk exposure
profit_target_percent: 10  # Faster profit taking
max_entry_price: 0.06    # Only buy on dips
```

### **Aggressive Setup**
```yaml
max_investment: 5.0      # Full allocation
profit_target_percent: 20  # Wait for bigger moves
max_entry_price: 0.12    # Accept higher entry prices
```

### **Balanced Setup (Recommended)**
```yaml
max_investment: 5.0      # Full strategy allocation
profit_target_percent: 15  # Reasonable profit target
max_entry_price: 0.10    # Moderate price filtering
```

## 🔧 Troubleshooting

### **Common Issues**
- **"Config validation failed"**: Update validator hotkey in config
- **"SN73 subnet not found"**: Verify SN73 is active on network
- **"Price too high"**: Increase max_entry_price or wait for dip
- **"Insufficient balance"**: Add more TAO or lower min_balance

### **Performance Optimization**
- **Monitor first week closely** to validate assumptions
- **Adjust profit targets** based on SN73 volatility patterns  
- **Consider price filtering** to avoid expensive entries
- **Track success rates** and modify strategy if needed

## 📞 Support

This is an experimental early-adopter strategy. Key considerations:
- **Start small** to test the approach
- **Monitor closely** especially first 2 weeks
- **Adjust parameters** based on SN73 behavior
- **Have exit plan** if thesis doesn't materialize

## 🎯 Next Steps After Deployment

1. **Week 1**: Validate technical operation and first position fills
2. **Month 1**: Assess profit patterns and SN73 adoption trends
3. **Month 3**: Evaluate overall strategy success and next steps
4. **Month 6**: Consider expansion to additional subnets

---

**⚠️ Disclaimer**: This is a high-risk experimental strategy on a very new subnet. Only invest funds you can afford to lose. Past performance does not guarantee future results.