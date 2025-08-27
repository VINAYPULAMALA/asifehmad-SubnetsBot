#!/usr/bin/env python3
"""
Test script for SN73 Micro-Grid Bot configuration and basic functionality
"""

import yaml
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_config():
    """Test loading and validating the SN73 config file."""
    try:
        with open("sn73_micro_grid_config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        console.print("✅ Configuration file loaded successfully")
        
        # Validate required fields
        required_fields = [
            'wallet', 'validator', 'target_netuid', 'dca_amount', 
            'dca_interval_hours', 'max_investment', 'profit_target_percent'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in config:
                missing_fields.append(field)
        
        if missing_fields:
            console.print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        # Validate field values
        validations = []
        
        if config['target_netuid'] != 73:
            validations.append(f"⚠️  target_netuid is {config['target_netuid']}, expected 73")
        
        if config['dca_amount'] != 0.05:
            validations.append(f"⚠️  dca_amount is {config['dca_amount']}, expected 0.05")
            
        if config['profit_target_percent'] != 15:
            validations.append(f"⚠️  profit_target_percent is {config['profit_target_percent']}, expected 15")
            
        if config['max_investment'] != 5.0:
            validations.append(f"⚠️  max_investment is {config['max_investment']}, expected 5.0")
        
        if config['validator'] == "5E4z3h9yVhmQyCFWNbY9BPpwhx4xFiPwq3eeqmBgVF6KULde":
            validations.append("❌ Please update the validator hotkey in config file!")
        
        # Print validation results
        table = Table(title="Configuration Validation", show_header=True, header_style="bold magenta")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white") 
        table.add_column("Status", style="green")
        
        table.add_row("Subnet", f"SN{config['target_netuid']}", "✅" if config['target_netuid'] == 73 else "⚠️")
        table.add_row("DCA Amount", f"{config['dca_amount']} TAO", "✅" if config['dca_amount'] == 0.05 else "⚠️")
        table.add_row("Profit Target", f"{config['profit_target_percent']}%", "✅" if config['profit_target_percent'] == 15 else "⚠️")
        table.add_row("Investment Cap", f"{config['max_investment']} TAO", "✅" if config['max_investment'] == 5.0 else "⚠️")
        table.add_row("DCA Interval", f"{config['dca_interval_hours']} hours", "✅")
        table.add_row("Validator", config['validator'][:20] + "...", "❌" if "your_validator" in config['validator'] else "✅")
        
        console.print()
        console.print(table)
        
        if validations:
            console.print()
            for validation in validations:
                console.print(validation)
        
        return len([v for v in validations if v.startswith("❌")]) == 0
        
    except FileNotFoundError:
        console.print("❌ sn73_micro_grid_config.yaml not found!")
        return False
    except Exception as e:
        console.print(f"❌ Error loading config: {e}")
        return False

def test_strategy_math():
    """Test the mathematical assumptions of the strategy."""
    console.print()
    console.print(Panel("🧮 Strategy Mathematics Validation", style="bold blue"))
    
    dca_amount = 0.05
    max_investment = 5.0
    profit_target = 15
    dca_interval_hours = 12
    
    # Calculate strategy metrics
    total_dca_purchases = max_investment / dca_amount
    days_to_complete = (total_dca_purchases * dca_interval_hours) / 24
    dca_per_day = 24 / dca_interval_hours
    
    console.print(f"📊 Strategy Analysis:")
    console.print(f"   💰 Total DCA Purchases: {total_dca_purchases:.0f}")
    console.print(f"   📅 Days to Complete: {days_to_complete:.1f}")
    console.print(f"   🔄 DCA per Day: {dca_per_day:.1f}")
    console.print(f"   🎯 Target Profit per Position: {profit_target}%")
    console.print()
    
    # Calculate potential outcomes
    console.print(f"📈 Potential Outcomes (if all positions hit {profit_target}% profit):")
    total_profit = max_investment * (profit_target / 100)
    roi_percent = (total_profit / max_investment) * 100
    
    console.print(f"   💎 Total Profit: {total_profit:.2f} TAO")
    console.print(f"   📊 ROI: {roi_percent:.1f}%")
    console.print()
    
    # Risk analysis  
    console.print(f"⚠️  Risk Analysis:")
    console.print(f"   📉 Maximum Loss: {max_investment:.1f} TAO (if SN73 goes to zero)")
    console.print(f"   🎲 Strategy Risk: Early adopter play on 4-month-old subnet")
    console.print(f"   💧 Liquidity Risk: New subnet with limited trading history")
    console.print()

def test_timeline():
    """Show expected timeline and milestones."""
    console.print(Panel("📅 Expected Timeline & Milestones", style="bold green"))
    
    milestones = [
        (7, 0.7, "First week - 14 DCA purchases"),
        (14, 1.4, "Two weeks - 28 positions, some may hit profit targets"),
        (25, 2.5, "Month 1 - Halfway point, strategy validation"),
        (35, 3.5, "5 weeks - 70% complete, profit patterns emerging"),
        (50, 5.0, "~7 weeks - Full investment cap reached"),
        (90, 5.0, "3 months - Sell-only mode, position management")
    ]
    
    for days, investment, description in milestones:
        progress = (investment / 5.0) * 100
        console.print(f"Day {days:2d}: {investment:.1f} TAO invested ({progress:3.0f}%) - {description}")
    
    console.print()

def main():
    """Run all tests."""
    console.print(Panel("🧪 SN73 Micro-Grid Bot - Configuration Test", title="Test Suite", style="bold cyan"))
    
    # Test 1: Configuration
    config_valid = test_config()
    
    # Test 2: Strategy math
    test_strategy_math()
    
    # Test 3: Timeline
    test_timeline()
    
    # Final recommendation
    console.print(Panel(
        "🚀 Ready to Deploy!" if config_valid else "⚠️  Fix Configuration Issues First",
        title="Test Results",
        style="bold green" if config_valid else "bold red"
    ))
    
    if config_valid:
        console.print()
        console.print("Next steps:")
        console.print("1. Update validator hotkey in sn73_micro_grid_config.yaml") 
        console.print("2. Run: python sn73_micro_grid_bot.py")
        console.print("3. Monitor first few cycles closely")
        console.print("4. Track performance vs expectations")
    else:
        console.print()
        console.print("Please fix configuration issues before deploying.")

if __name__ == "__main__":
    main()