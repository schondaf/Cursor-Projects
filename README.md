# 🚀 Daily Market Recap Generator

A comprehensive Python script that generates professional LinkedIn-style market reports by combining cryptocurrency data, Treasury yields, and FRED interest rates to analyze the relationship between traditional finance and digital assets.

## ✨ Features

- **Real-time Cryptocurrency Data**: Fetches current prices and 24h changes for BTC, ETH, and XRP
- **Treasury Yield Analysis**: Gets 10-year Treasury yield data from Alpha Vantage
- **FRED Interest Rates**: Retrieves short-term rates (Fed Funds, 3-Month T-Bill, 2-Year Treasury)
- **AI-Powered Market Analysis**: Optional Claude API integration for enhanced insights and professional commentary
- **Market Correlation Analysis**: Links crypto performance with traditional finance indicators
- **Professional Report Format**: Generates LinkedIn-ready market summaries with emojis and hashtags
- **Automatic File Saving**: Saves reports with timestamps for easy reference

## 🛠️ Installation

1. **Clone or download the files** to your local machine
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🔑 API Keys Required

### Alpha Vantage API Key (Required)
- **Purpose**: Fetch Treasury yield data
- **Get it here**: [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- **Cost**: Free tier available (500 requests/day)
- **Note**: Required for Treasury yield functionality

### Claude API Key (Optional but Recommended)
- **Purpose**: Generate enhanced AI-powered market analysis and insights
- **Get it here**: [Anthropic Console](https://console.anthropic.com/)
- **Cost**: Pay-as-you-go pricing (very affordable for daily use)
- **Note**: The script works without this API key, but analysis will be more basic
- **Benefits**: 
  - Deeper market correlation insights
  - Professional financial commentary
  - Context-aware analysis of market dynamics

### FRED API (Optional)
- **Purpose**: Fetch Federal Reserve interest rate data
- **Get it here**: [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html)
- **Cost**: Free (no API key required for basic usage)
- **Note**: The script works without this API key

## 🚀 Usage

### Basic Usage
```bash
python daily_market_recap.py
```

### What Happens When You Run It
1. **API Key Prompts**: 
   - Enter your Alpha Vantage API key (required)
   - Optionally enter your Claude API key for enhanced analysis
2. **Data Fetching**: The script fetches data from multiple sources:
   - CoinGecko (cryptocurrency prices)
   - Alpha Vantage (Treasury yields)
   - FRED (interest rates)
3. **Analysis Generation**: 
   - If Claude API key provided: Generates AI-powered market analysis
   - Otherwise: Uses standard rule-based analysis
4. **Recap Display**: Shows the complete recap in the terminal
5. **File Saving**: Automatically saves the recap to a timestamped file

## 📊 Sample Output

The script generates recaps like this:

```
🚀 DAILY MARKET RECAP - December 15, 2024 🚀

📈 CRYPTOCURRENCY PERFORMANCE (24h):
🟢 BTC: $43,250.00 (+2.45%)
🔴 ETH: $2,650.00 (-1.20%)
🟢 XRP: $0.65 (+0.85%)

🏛️ TREASURY YIELD UPDATE:
📊 10Y Treasury: 4.25% (+5.00bps)

💵 SHORT-TERM RATES:
🟢 Fed Funds Rate: 5.50% (+0.00bps)
🔴 3 Month Tbill: 5.35% (-2.00bps)

🔗 MARKET CORRELATION ANALYSIS:
📈 Despite rising yields, crypto showing resilience - risk appetite remains strong

📋 MARKET SUMMARY:
🎯 Overall Sentiment: BULLISH
🌊 Risk Appetite: High
💡 Key Takeaway: Risk-on environment favors crypto

#Crypto #Markets #Treasury #Finance #DigitalAssets #TradFi #DeFi #MarketRecap
```

## 🔧 Customization

### Adding More Cryptocurrencies
Edit the `crypto_ids` dictionary in the `DailyMarketRecapGenerator` class:

```python
self.crypto_ids = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum', 
    'XRP': 'ripple',
    'ADA': 'cardano',  # Add more coins
    'SOL': 'solana'
}
```

### Adding More FRED Series
Edit the `fred_series` dictionary:

```python
self.fred_series = {
    'fed_funds_rate': 'FEDFUNDS',
    '3_month_tbill': 'DGS3MO',
    '2_year_treasury': 'DGS2',
    '5_year_treasury': 'DGS5',  # Add more series
    '30_year_treasury': 'DGS30'
}
```

## 📁 File Structure

```
├── daily_market_recap.py       # Main script
├── requirements.txt             # Python dependencies
├── README.md                   # This file
└── market_recap_YYYYMMDD_HHMMSS.txt  # Generated recaps
```

## 🚨 Troubleshooting

### Common Issues

1. **"API key is required" error**
   - Make sure you have a valid Alpha Vantage API key
   - Check that the API key is entered correctly

2. **"Error fetching Treasury data"**
   - Verify your Alpha Vantage API key is valid
   - Check your internet connection
   - Alpha Vantage free tier has rate limits

3. **"Error fetching crypto data"**
   - CoinGecko API may be temporarily unavailable
   - Check your internet connection
   - Wait a few minutes and try again

4. **Import errors**
   - Make sure you've installed requirements: `pip install -r requirements.txt`
   - Verify you're using Python 3.7+

### Rate Limiting
- **CoinGecko**: Built-in rate limiting (0.5s delay between requests)
- **Alpha Vantage**: Free tier: 500 requests/day, 5 requests/minute
- **FRED**: No rate limiting for basic usage

## 💡 Tips for LinkedIn Sharing

1. **Run the script daily** at market close (4 PM ET) for fresh data
2. **Post in the morning** (8-9 AM ET) for better engagement
3. **Customize the analysis** section based on your market insights
4. **Add personal commentary** before sharing
5. **Use the generated hashtags** for better reach
6. **Save recaps** for historical analysis and trend tracking

## 🔮 Future Enhancements

Potential improvements for future versions:
- Historical price charts and graphs
- More sophisticated correlation analysis
- Additional traditional finance indicators
- Export to Excel/CSV formats
- Email automation for daily recaps
- Web dashboard interface

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your API keys are valid
3. Ensure all dependencies are installed
4. Check your internet connection

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Trading! 📈💰**
