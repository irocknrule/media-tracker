# Asset Allocation Feature Guide

## Overview

The new Asset Allocation feature provides a comprehensive view of your portfolio's allocation across different asset categories, with automatic ticker categorization using real-time market data.

## Features

### 1. Automatic Ticker Categorization
- **US Stocks**: Automatically detects US-based companies and US-focused funds
- **International Stocks**: Identifies international funds (VXUS, EFA, etc.) and foreign companies
- **Bonds**: Detects bond funds and fixed income securities
- **Cash**: Identifies money market and cash equivalent funds

The system uses `yfinance` to analyze:
- Company country of origin
- Fund names (e.g., "International", "Ex-US", "EAFE")
- Quote type (Equity, ETF, Mutual Fund)
- Exchange information

### 2. Allocation Summary Tab
- **Horizontal Bar Chart**: Visual comparison of target vs actual allocation
- **Detailed Table**: Shows category, target, actual, difference, threshold, and value
- **Rebalancing Recommendations**: Suggests specific dollar amounts to buy/sell
- **Status Indicators**: Highlights categories that need rebalancing

### 3. Settings Tab
- Adjust target allocation percentages for each category
- Set threshold percentages for acceptable deviation
- Validation to ensure targets total 100%

### 4. Ticker Categories Tab
- View all tickers grouped by category
- See which tickers were auto-categorized vs manually set
- Manually override categorization for any ticker
- Re-scan tickers to update auto-categorization

## Setup

### 1. Run Migration
```bash
python migrate_add_asset_allocation.py
```

This creates:
- `asset_allocation_targets` table with default targets:
  - US Stocks: 70% (±5% threshold)
  - International Stocks: 25% (±5% threshold)
  - Bonds: 0% (±0% threshold)
  - Cash: 5% (±1% threshold)
- `ticker_categories` table for storing ticker classifications

### 2. Start the Backend
```bash
uvicorn backend.main:app --reload
```

### 3. Start the Frontend
```bash
streamlit run frontend/app.py
```

## Usage

### Viewing Your Allocation

1. Navigate to **Portfolio Tracker** → **Asset Allocation**
2. The **Allocation Summary** tab shows:
   - Current portfolio value
   - Visual chart comparing target vs actual
   - Detailed breakdown table
   - Rebalancing recommendations (if needed)

### Adjusting Targets

1. Go to the **Settings** tab
2. Adjust target percentages and thresholds for each category
3. Click "Update" for each category you modify
4. Ensure targets total 100%

### Managing Ticker Categories

1. Go to the **Ticker Categories** tab
2. View tickers grouped by category
3. To manually override:
   - Select new category from dropdown
   - Click "Update"
   - Ticker is marked as manually categorized
4. To refresh auto-categorization:
   - Click "Re-scan" button
   - System re-analyzes using latest market data

## Common Ticker Examples

### US Stocks
- Individual US companies: AAPL, MSFT, GOOGL
- US market ETFs: VTI, VOO, SPY, QQQ

### International Stocks
- International ETFs: VXUS, IXUS, VEA, IEFA, VWO
- Foreign companies trading as ADRs

### Bonds
- Bond ETFs: BND, AGG, TLT, SHY

### Cash
- Money market funds: SGOV, VMFXX, SPAXX

## API Endpoints

### Allocation Summary
- `GET /portfolio/allocation/summary` - Get complete allocation analysis

### Targets Management
- `GET /portfolio/allocation/targets` - Get all targets
- `PUT /portfolio/allocation/targets/{category}` - Update target
- `POST /portfolio/allocation/targets` - Create new target

### Ticker Categories
- `GET /portfolio/allocation/ticker-categories` - Get all ticker mappings
- `GET /portfolio/allocation/ticker-categories/{ticker}` - Get/create category for ticker
- `PUT /portfolio/allocation/ticker-categories/{ticker}` - Update ticker category
- `POST /portfolio/allocation/ticker-categories/recategorize/{ticker}` - Force re-categorization

## Tips

1. **Regular Rebalancing**: Check allocation monthly or quarterly
2. **Threshold Tuning**: Adjust thresholds based on your rebalancing frequency
3. **Manual Override**: Some tickers (like total world funds) may need manual categorization
4. **Re-scan Feature**: Use after major fund changes or ticker splits

## Notes

- Auto-categorization happens when tickers are first added to portfolio
- Categorization is cached in database for performance
- Current prices are fetched using yfinance (no API key needed)
- All calculations use real-time market data

