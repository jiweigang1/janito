# Market Data Sources Guide

This guide provides information about reliable sources for accessing financial market data and stock information.

## Reliable Market Data Sources

### Government & Regulatory Sources

| Source | URL | Data Type | Access Method | Notes |
|--------|-----|-----------|---------------|--------|
| **SEC EDGAR** | https://www.sec.gov/edgar/searchedgar/companysearch.html | Company filings, 10-K, 10-Q, 8-K reports | Web scraping + official API | Official financial statements, insider trading reports |
| **Federal Reserve FRED** | https://fred.stlouisfed.org/ | Economic indicators, interest rates, market indices | Free API with registration | Comprehensive economic and market data |

### Public Financial Data Sources

| Source | URL | Data Type | Access Method | Coverage |
|--------|-----|-----------|---------------|----------|
| **TradingView** | https://www.tradingview.com/markets/ | Real-time quotes, charts, technical analysis | Web scraping friendly | Global markets with proper user-agent |
| **Investing.com** | https://www.investing.com/indices/ | Global indices, commodities, currencies, stocks | Web scraping | International markets and real-time data |
| **Yahoo Finance** | https://finance.yahoo.com/ | Stock prices, historical data | Limited access | May have restrictions, use alternatives |

### Financial APIs with Free Tiers

| API Provider | URL | Free Tier Limits | Data Types | Rate Limits |
|--------------|-----|------------------|------------|-------------|
| **Alpha Vantage** | https://www.alphavantage.co/ | 5 calls/min, 500/day | Stocks, forex, crypto, historical | 5 API calls per minute |
| **Financial Modeling Prep** | https://financialmodelingprep.com/developer/docs/ | Limited daily calls | Financial statements, ratios, prices | Daily quota system |
| **Twelve Data** | https://twelvedata.com/ | 8 calls/minute | Stocks, forex, crypto, real-time | 8 API calls per minute |

## Working with Market Data in Janito

### Quick Stock Price Check

```bash
# Get current Apple stock information
janito "Fetch Apple's current stock price and key metrics from tradingview.com"

# Get market indices overview
janito "Retrieve current S&P 500, Dow Jones, and Nasdaq values from investing.com"
```

### Historical Data Access

```bash
# Get historical price data
janito "Find historical stock price data for Apple from FRED database"

# Access SEC filings
janito "Download Apple's latest 10-K filing from SEC EDGAR"
```

### Economic Indicators

```bash
# Get Federal Reserve data
janito "Fetch current federal funds rate and economic indicators from FRED"

# Market analysis
janito "Analyze current market conditions using available public data sources"
```

## Data Source Reliability

| Tier | Sources | Reliability | Access Notes |
|------|---------|-------------|--------------|
| **Tier 1** | SEC, FRED, Census Bureau, Official APIs | Most Reliable | Government sources with documented endpoints |
| **Tier 2** | TradingView, Investing.com, Alpha Vantage | Reliable with Limitations | Good for current data, web scraping friendly, free tier limits |
| **Tier 3** | Yahoo Finance, Bloomberg, Reuters | Use with Caution | Access restrictions, typically blocked for automated access |

## Best Practices

### Data Collection Best Practices

| Practice | Description | Implementation |
|----------|-------------|----------------|
| **Official APIs** | Use provided APIs when available | Check developer documentation for endpoints |
| **Rate Limiting** | Implement delays to avoid blocks | Add sleep timers between requests |
| **Data Caching** | Store frequently accessed data locally | Use local files or databases for storage |
| **Cross-Reference** | Verify data from multiple sources | Compare results across different providers |
| **Terms Compliance** | Respect robots.txt and service terms | Review and follow usage guidelines |

### Error Handling

```bash
# Handle blocked access gracefully
janito "If tradingview.com is blocked, try investing.com for Apple stock data"

# Fallback sources
janito "Get Apple's financial data from SEC filings if market data sources are unavailable"
```

## Integration Examples

### Portfolio Tracking

```bash
# Track multiple stocks
janito "Monitor AAPL, MSFT, GOOGL, and TSLA using available public sources"

# Market overview
janito "Generate a daily market summary using government and public data sources"
```

### Economic Analysis

```bash
# Economic indicators
janito "Analyze the relationship between Federal Reserve data and market performance"

# Sector analysis
janito "Compare technology sector performance using SEC filings and market data"
```

## Related Documentation

- [Stock Market Guide](stock-market-guide.md) - Comprehensive guide to accessing financial data
- [Public Sources](public-sources.md) - Government and institutional data sources
- [Using Tools](using_tools.md) - How to use Janito's data fetching capabilities
- [CLI Options](../reference/cli-options.md) - Command-line options for data access

## Getting Help

For assistance with market data access:

1. Check the [troubleshooting section](configuration.md)
2. Use `janito --help` to see available options
3. Test different data sources for reliability
4. Open GitHub issues for specific data source requests