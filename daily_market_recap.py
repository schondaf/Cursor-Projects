#!/usr/bin/env python3
"""
Daily Market Recap Generator
Fetches cryptocurrency closing prices, Treasury yields, and FRED rates to create
a comprehensive market analysis report suitable for LinkedIn sharing.
"""

import requests  # pyright: ignore[reportMissingModuleSource]
import pandas as pd  # pyright: ignore[reportMissingImports]
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List, Tuple, Optional

try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️ Anthropic package not installed. Claude analysis will be disabled.")
    print("💡 Install it with: pip install anthropic")

class DailyMarketRecapGenerator:
    """
    Main class to generate comprehensive daily market recap reports
    combining traditional finance and digital asset data using closing prices
    """
    
    def __init__(self, alpha_vantage_api_key: str, claude_api_key: Optional[str] = None):
        """
        Initialize the generator with API keys
        
        Args:
            alpha_vantage_api_key (str): Alpha Vantage API key for Treasury data
            claude_api_key (str, optional): Claude API key for enhanced analysis
        """
        self.alpha_vantage_api_key = alpha_vantage_api_key
        self.claude_api_key = claude_api_key
        self.fred_api_key = None  # FRED doesn't require API key for basic data
        
        # Initialize Claude client if API key is provided
        self.claude_client = None
        if claude_api_key and CLAUDE_AVAILABLE:
            try:
                self.claude_client = Anthropic(api_key=claude_api_key)
                print("✅ Claude API initialized for enhanced analysis")
            except Exception as e:
                print(f"⚠️ Failed to initialize Claude API: {str(e)}")
                self.claude_client = None
        
        # Base URLs for different data sources
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        self.fred_base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        # Cryptocurrency IDs for CoinGecko API
        self.crypto_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'XRP': 'ripple'
        }
        
        # FRED series IDs for interest rates
        self.fred_series = {
            'fed_funds_rate': 'FEDFUNDS',  # Federal Funds Rate
            '3_month_tbill': 'DGS3MO',     # 3-Month Treasury Bill
            '2_year_treasury': 'DGS2'      # 2-Year Treasury
        }
    
    def get_crypto_closing_prices(self) -> Dict[str, Dict]:
        """
        Fetch cryptocurrency closing prices and calculate day-over-day changes
        
        Returns:
            Dict containing closing prices and day-over-day changes for BTC, ETH, XRP
        """
        print("🔍 Fetching cryptocurrency closing price data...")
        
        crypto_data = {}
        
        for symbol, coin_id in self.crypto_ids.items():
            print(f"🔍 Processing {symbol} ({coin_id})...")
            try:
                # Get historical data for the last 2 days to calculate day-over-day change
                url = f"{self.coingecko_base_url}/coins/{coin_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': '2',  # Get 2 days of data
                    'interval': 'daily'
                }
                
                print(f"🔍 Fetching from: {url}")
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                print(f"🔍 {symbol} response received, data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                if 'prices' in data and len(data['prices']) >= 2:
                    # Extract closing prices for current and previous day
                    # CoinGecko provides daily data at midnight UTC, which is close to US market close
                    current_close = data['prices'][-1][1]  # Most recent closing price
                    previous_close = data['prices'][-2][1]  # Previous day closing price
                    
                    # Calculate day-over-day change
                    price_change = current_close - previous_close
                    price_change_pct = (price_change / previous_close) * 100 if previous_close != 0 else 0
                    
                    # Get additional market data
                    market_data_url = f"{self.coingecko_base_url}/coins/{coin_id}"
                    market_response = requests.get(market_data_url, timeout=30)
                    market_response.raise_for_status()
                    market_data = market_response.json()
                    
                    crypto_data[symbol] = {
                        'current_close': current_close,
                        'previous_close': previous_close,
                        'price_change': price_change,
                        'price_change_pct': price_change_pct,
                        'market_cap': market_data['market_data']['market_cap']['usd'],
                        'volume_24h': market_data['market_data']['total_volume']['usd']
                    }
                    
                    print(f"✅ {symbol}: ${current_close:,.2f} ({price_change_pct:+.2f}% from previous close)")
                    
                else:
                    print(f"❌ Insufficient historical data for {symbol}")
                    print(f"🔍 {symbol} data structure: {str(data)[:200]}...")
                    crypto_data[symbol] = None
                
                # Rate limiting to be respectful to the API
                time.sleep(2.0)  # Increased from 0.5 to 2.0 seconds
                
            except Exception as e:
                print(f"❌ Error fetching {symbol} closing data: {str(e)}")
                print(f"🔍 Full error details: {type(e).__name__}: {e}")
                crypto_data[symbol] = None
        
        return crypto_data
    
    def get_treasury_yield(self) -> Dict[str, float]:
        """
        Fetch 10-year Treasury yield closing data from Alpha Vantage
        with fallback to alternative sources if needed
        
        Returns:
            Dict containing Treasury yield closing data and day-over-day changes
        """
        print("🔍 Fetching Treasury yield closing data from Alpha Vantage...")
        
        try:
            # Alpha Vantage Treasury yield endpoint
            params = {
                'function': 'TREASURY_YIELD',
                'interval': 'daily',
                'maturity': '10year',
                'apikey': self.alpha_vantage_api_key
            }
            
            response = requests.get(self.alpha_vantage_base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Debug: Print the response structure
            print(f"🔍 Treasury API Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Check for different possible response formats
            if 'data' in data and len(data['data']) >= 2:
                # Standard format - this is what your API returns
                latest_data = data['data'][0]
                previous_data = data['data'][1]
                
                # Extract date and value from the data structure
                current_date = latest_data.get('date', 'Unknown')
                current_yield = float(latest_data.get('value', 0))
                previous_date = previous_data.get('date', 'Unknown')
                previous_yield = float(previous_data.get('value', 0))
                
                yield_change = current_yield - previous_yield
                
                treasury_data = {
                    'current_yield': current_yield,
                    'previous_yield': previous_yield,
                    'yield_change': yield_change,
                    'yield_change_pct': (yield_change / previous_yield) * 100 if previous_yield != 0 else 0,
                    'current_date': current_date,
                    'previous_date': previous_date
                }
                
                print(f"✅ 10Y Treasury: {current_yield:.2f}% ({yield_change:+.2f}bps from {previous_date} close)")
                return treasury_data
                
            elif 'Time Series (Daily)' in data:
                # Alternative format - time series data
                time_series = data['Time Series (Daily)']
                dates = sorted(time_series.keys(), reverse=True)
                
                if len(dates) >= 2:
                    current_yield = float(time_series[dates[0]]['10Y'])
                    previous_yield = float(time_series[dates[1]]['10Y'])
                    yield_change = current_yield - previous_yield
                    
                    treasury_data = {
                        'current_yield': current_yield,
                        'previous_yield': previous_yield,
                        'yield_change': yield_change,
                        'yield_change_pct': (yield_change / previous_yield) * 100 if previous_yield != 0 else 0
                    }
                    
                    print(f"✅ 10Y Treasury: {current_yield:.2f}% ({yield_change:+.2f}bps from previous close)")
                    return treasury_data
                    
            elif 'Note' in data:
                # API limit or error message
                print(f"⚠️ Alpha Vantage API Note: {data['Note']}")
                print("💡 This usually means you've hit the rate limit or need to upgrade your plan")
                return None
                
            elif 'Error Message' in data:
                # API error
                print(f"❌ Alpha Vantage API Error: {data['Error Message']}")
                return None
                
            else:
                print("❌ Unexpected Treasury API response format")
                print(f"🔍 Response preview: {str(data)[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching Treasury data: {str(e)}")
            print("💡 Trying alternative Treasury data source...")
            
            # Fallback: Try to get Treasury data from FRED
            return self.get_treasury_from_fred()
    
    def get_treasury_from_fred(self) -> Dict[str, float]:
        """
        Fallback method to get Treasury yield from FRED if Alpha Vantage fails
        
        Returns:
            Dict containing Treasury yield data from FRED
        """
        print("🔍 Trying FRED as alternative Treasury data source...")
        
        try:
            # FRED 10-year Treasury constant maturity rate
            params = {
                'series_id': 'DGS10',  # 10-year Treasury constant maturity rate
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'limit': 2
            }
            
            response = requests.get(self.fred_base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'observations' in data and len(data['observations']) >= 2:
                current_value = float(data['observations'][0]['value'])
                previous_value = float(data['observations'][1]['value'])
                change = current_value - previous_value
                
                treasury_data = {
                    'current_yield': current_value,
                    'previous_yield': previous_value,
                    'yield_change': change,
                    'yield_change_pct': (change / previous_value) * 100 if previous_value != 0 else 0
                }
                
                print(f"✅ 10Y Treasury (FRED): {current_value:.2f}% ({change:+.2f}bps from previous close)")
                return treasury_data
                
            else:
                print("❌ No FRED Treasury data available")
                return None
                
        except Exception as e:
            print(f"❌ FRED Treasury fallback also failed: {str(e)}")
            return None
    
    def get_fred_closing_rates(self) -> Dict[str, Dict]:
        """
        Fetch FRED interest rate closing data or use Alpha Vantage as alternative
        
        Returns:
            Dict containing various short-term rates and day-over-day changes
        """
        print("🔍 Fetching short-term interest rate data...")
        
        # Try FRED first, then fallback to Alpha Vantage
        fred_data = self.get_fred_rates()
        
        # If FRED fails, try Alpha Vantage for additional Treasury data
        if not fred_data or all(v is None for v in fred_data.values()):
            print("💡 FRED data unavailable, trying Alpha Vantage for additional Treasury rates...")
            return self.get_additional_treasury_rates()
        
        return fred_data
    
    def get_fred_rates(self) -> Dict[str, Dict]:
        """
        Fetch FRED interest rate closing data
        
        Returns:
            Dict containing various short-term rates and day-over-day changes
        """
        print("🔍 Trying FRED for interest rate data...")
        
        fred_data = {}
        
        for rate_name, series_id in self.fred_series.items():
            try:
                # FRED requires API key for most endpoints
                if not self.fred_api_key:
                    print(f"⚠️ No FRED API key - skipping {rate_name}")
                    fred_data[rate_name] = None
                    continue
                
                params = {
                    'series_id': series_id,
                    'api_key': self.fred_api_key,
                    'file_type': 'json',
                    'limit': 2  # Get current and previous closing values
                }
                
                response = requests.get(self.fred_base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'observations' in data and len(data['observations']) >= 2:
                    current_value = float(data['observations'][0]['value'])
                    previous_value = float(data['observations'][1]['value'])
                    change = current_value - previous_value
                    change_pct = (change / previous_value) * 100 if previous_value != 0 else 0
                    
                    fred_data[rate_name] = {
                        'current_rate': current_value,
                        'previous_rate': previous_value,
                        'change': change,
                        'change_pct': change_pct
                    }
                    
                    print(f"✅ {rate_name}: {current_value:.2f}% ({change:+.2f}bps from previous close)")
                    
                else:
                    print(f"❌ No FRED data found for {rate_name}")
                    fred_data[rate_name] = None
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error fetching {rate_name} from FRED: {str(e)}")
                fred_data[rate_name] = None
        
        return fred_data
    
    def get_additional_treasury_rates(self) -> Dict[str, Dict]:
        """
        Get additional Treasury rates from Alpha Vantage as FRED alternative
        
        Returns:
            Dict containing 2-year and 3-month Treasury rates
        """
        print("🔍 Fetching additional Treasury rates from Alpha Vantage...")
        
        treasury_rates = {}
        
        # Get 2-year Treasury rate
        try:
            params_2y = {
                'function': 'TREASURY_YIELD',
                'interval': 'daily',
                'maturity': '2year',
                'apikey': self.alpha_vantage_api_key
            }
            
            response_2y = requests.get(self.alpha_vantage_base_url, params=params_2y, timeout=30)
            response_2y.raise_for_status()
            data_2y = response_2y.json()
            
            if 'data' in data_2y and len(data_2y['data']) >= 2:
                current_2y = float(data_2y['data'][0]['value'])
                previous_2y = float(data_2y['data'][1]['value'])
                change_2y = current_2y - previous_2y
                
                treasury_rates['2_year_treasury'] = {
                    'current_rate': current_2y,
                    'previous_rate': previous_2y,
                    'change': change_2y,
                    'change_pct': (change_2y / previous_2y) * 100 if previous_2y != 0 else 0
                }
                
                print(f"✅ 2Y Treasury: {current_2y:.2f}% ({change_2y:+.2f}bps from previous close)")
            else:
                print("⚠️ 2Y Treasury data not available")
                treasury_rates['2_year_treasury'] = None
                
        except Exception as e:
            print(f"❌ Error fetching 2Y Treasury: {str(e)}")
            treasury_rates['2_year_treasury'] = None
        
        # Get 3-month Treasury rate
        try:
            params_3m = {
                'function': 'TREASURY_YIELD',
                'interval': 'daily',
                'maturity': '3month',
                'apikey': self.alpha_vantage_api_key
            }
            
            response_3m = requests.get(self.alpha_vantage_base_url, params=params_3m, timeout=30)
            response_3m.raise_for_status()
            data_3m = response_3m.json()
            
            if 'data' in data_3m and len(data_3m['data']) >= 2:
                current_3m = float(data_3m['data'][0]['value'])
                previous_3m = float(data_3m['data'][1]['value'])
                change_3m = current_3m - previous_3m
                
                treasury_rates['3_month_tbill'] = {
                    'current_rate': current_3m,
                    'previous_rate': previous_3m,
                    'change': change_3m,
                    'change_pct': (change_3m / previous_3m) * 100 if previous_3m != 0 else 0
                }
                
                print(f"✅ 3M Treasury: {current_3m:.2f}% ({change_3m:+.2f}bps from previous close)")
            else:
                print("⚠️ 3M Treasury data not available")
                treasury_rates['3_month_tbill'] = None
                
        except Exception as e:
            print(f"❌ Error fetching 3M Treasury: {str(e)}")
            treasury_rates['3_month_tbill'] = None
        
        # Add Fed Funds Rate (approximation using 3-month rate)
        if treasury_rates.get('3_month_tbill'):
            # Fed Funds Rate is typically close to 3-month Treasury
            fed_funds = treasury_rates['3_month_tbill']['current_rate']
            treasury_rates['fed_funds_rate'] = {
                'current_rate': fed_funds,
                'previous_rate': treasury_rates['3_month_tbill']['previous_rate'],
                'change': treasury_rates['3_month_tbill']['change'],
                'change_pct': treasury_rates['3_month_tbill']['change_pct'],
                'note': 'Approximated from 3M Treasury'
            }
            print(f"✅ Fed Funds Rate (approx): {fed_funds:.2f}% (from 3M Treasury)")
        else:
            treasury_rates['fed_funds_rate'] = None
        
        return treasury_rates
    
    def get_claude_analysis(self, crypto_data: Dict, treasury_data: Dict, fred_data: Dict, sentiment: str) -> Optional[str]:
        """
        Generate enhanced market analysis using Claude API
        
        Args:
            crypto_data: Cryptocurrency closing price data
            treasury_data: Treasury yield closing data
            fred_data: FRED interest rate closing data
            sentiment: Overall market sentiment (bullish/bearish/mixed)
            
        Returns:
            Enhanced analysis text from Claude, or None if unavailable
        """
        if not self.claude_client:
            return None
        
        try:
            print("🤖 Generating enhanced analysis with Claude...")
            
            # Prepare data summary for Claude
            crypto_summary = []
            for symbol, data in crypto_data.items():
                if data:
                    direction = "up" if data['price_change_pct'] > 0 else "down"
                    crypto_summary.append(
                        f"{symbol}: ${data['current_close']:,.2f} ({data['price_change_pct']:+.2f}% {direction})"
                    )
            
            treasury_summary = ""
            if treasury_data:
                direction = "up" if treasury_data['yield_change'] > 0 else "down"
                treasury_summary = f"10Y Treasury: {treasury_data['current_yield']:.2f}% ({treasury_data['yield_change']:+.2f}bps {direction})"
            
            rates_summary = []
            if fred_data:
                for rate_name, data in fred_data.items():
                    if data:
                        direction = "up" if data['change'] > 0 else "down"
                        rate_display = rate_name.replace('_', ' ').title()
                        rates_summary.append(f"{rate_display}: {data['current_rate']:.2f}% ({data['change']:+.2f}bps {direction})")
            
            # Create prompt for Claude
            prompt = f"""You are a financial market analyst providing insights for a daily market recap report. 

Market Data Summary:
- Cryptocurrencies: {', '.join(crypto_summary) if crypto_summary else 'No data'}
- Treasury: {treasury_summary if treasury_summary else 'No data'}
- Short-term Rates: {', '.join(rates_summary) if rates_summary else 'No data'}
- Overall Sentiment: {sentiment.upper()}

Provide a concise, professional market correlation analysis (2-3 sentences) that:
1. Explains the relationship between Treasury yields, interest rates, and cryptocurrency performance
2. Identifies key market dynamics and what they might indicate
3. Uses professional financial language suitable for LinkedIn
4. Is insightful but not overly technical
5. Includes relevant market context

Format your response as plain text without markdown, emojis, or special formatting. Keep it under 200 words."""

            # Call Claude API
            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract the analysis text
            analysis_text = message.content[0].text.strip()
            print("✅ Claude analysis generated successfully")
            return analysis_text
            
        except Exception as e:
            print(f"⚠️ Error generating Claude analysis: {str(e)}")
            print("💡 Continuing with standard analysis...")
            return None
    
    def generate_market_recap(self, crypto_data: Dict, treasury_data: Dict, fred_data: Dict) -> Dict[str, any]:
        """
        Generate comprehensive market recap using closing price data
        
        Args:
            crypto_data: Cryptocurrency closing price data
            treasury_data: Treasury yield closing data  
            fred_data: FRED interest rate closing data
            
        Returns:
            Dict containing formatted market recap report and date info
        """
        print("\n📊 Generating comprehensive market recap from closing prices...")
        
        # Calculate overall market sentiment based on closing price changes
        crypto_positive = sum(1 for data in crypto_data.values() 
                            if data and data['price_change_pct'] > 0)
        crypto_negative = sum(1 for data in crypto_data.values() 
                             if data and data['price_change_pct'] < 0)
        
        # Determine market sentiment
        if crypto_positive > crypto_negative:
            sentiment = "bullish"
        elif crypto_negative > crypto_positive:
            sentiment = "bearish"
        else:
            sentiment = "mixed"
        
        # Get the date this data represents (previous trading day)
        # If run on Friday, this shows Thursday's data
        # If run on Monday, this shows Friday's data
        current_date = datetime.now()
        
        # Determine the data date (previous trading day)
        if current_date.weekday() == 0:  # Monday
            # If it's Monday, data is from Friday
            data_date = current_date - timedelta(days=3)
        elif current_date.weekday() == 6:  # Sunday
            # If it's Sunday, data is from Friday
            data_date = current_date - timedelta(days=2)
        else:
            # Other days, data is from previous day
            data_date = current_date - timedelta(days=1)
        
        # Format the date for display
        data_date_str = data_date.strftime('%B %d, %Y')
        run_date_str = current_date.strftime('%B %d, %Y')
        
        # Generate recap report
        recap = f"""
🚀 DAILY MARKET RECAP - {data_date_str} 🚀
📊 Based on {data_date_str} Market Closing Prices
📅 Report Generated: {run_date_str}

📈 CRYPTOCURRENCY PERFORMANCE (Day-over-Day):
"""
        
        # Add crypto performance details using closing prices
        for symbol, data in crypto_data.items():
            if data:
                change_emoji = "🟢" if data['price_change_pct'] > 0 else "🔴"
                recap += f"{change_emoji} {symbol}: ${data['current_close']:,.2f} ({data['price_change_pct']:+.2f}% from previous close)\n"
        
        # Add Treasury yield analysis
        if treasury_data:
            recap += f"""
🏛️ TREASURY YIELD UPDATE (Closing):
📊 10Y Treasury: {treasury_data['current_yield']:.2f}% ({treasury_data['yield_change']:+.2f}bps from previous close)
"""
        
        # Add FRED rates analysis
        if fred_data:
            recap += f"""
💵 SHORT-TERM RATES (Closing):
"""
            for rate_name, data in fred_data.items():
                if data:
                    rate_display_name = rate_name.replace('_', ' ').title()
                    change_emoji = "🟢" if data['change'] > 0 else "🔴"
                    if 'note' in data:
                        recap += f"{change_emoji} {rate_display_name}: {data['current_rate']:.2f}% ({data['change']:+.2f}bps from previous close) {data['note']}\n"
                    else:
                        recap += f"{change_emoji} {rate_display_name}: {data['current_rate']:.2f}% ({data['change']:+.2f}bps from previous close)\n"
        
        # Add market correlation analysis
        recap += f"""
🔗 MARKET CORRELATION ANALYSIS:
"""
        
        # Try to get Claude analysis first
        claude_analysis = self.get_claude_analysis(crypto_data, treasury_data, fred_data, sentiment)
        
        if claude_analysis:
            # Use Claude's enhanced analysis
            recap += f"{claude_analysis}\n"
        elif treasury_data and crypto_data:
            # Fallback to standard analysis if Claude is unavailable
            if treasury_data['yield_change'] > 0:
                if sentiment == "bearish":
                    recap += "📉 Rising Treasury yields may be contributing to crypto selling pressure as investors seek safer yields\n"
                else:
                    recap += "📈 Despite rising yields, crypto showing resilience - risk appetite remains strong\n"
            else:
                if sentiment == "bullish":
                    recap += "📈 Falling Treasury yields supporting crypto rally as risk assets become more attractive\n"
                else:
                    recap += "📊 Lower yields not translating to crypto gains - other factors driving market sentiment\n"
        else:
            recap += "📊 Market data analysis unavailable\n"
        
        # Add market summary
        recap += f"""
📋 MARKET SUMMARY:
🎯 Overall Sentiment: {sentiment.upper()}
🌊 Risk Appetite: {'High' if sentiment == 'bullish' else 'Low' if sentiment == 'bearish' else 'Mixed'}
💡 Key Takeaway: {'Risk-on environment favors crypto' if sentiment == 'bullish' else 'Risk-off sentiment prevails' if sentiment == 'bearish' else 'Mixed signals suggest cautious approach'}
        
#Crypto #Markets #Treasury #Finance #DigitalAssets #TradFi #DeFi #MarketRecap #ClosingPrices
        """
        
        return {
            'recap_text': recap,
            'data_date': data_date_str,
            'run_date': run_date_str
        }
    
    def generate_recap(self) -> str:
        """
        Main method to generate the complete market recap using closing prices
        
        Returns:
            Complete market recap report
        """
        print("🚀 Starting Daily Market Recap Generation (Closing Prices)...")
        print("=" * 70)
        
        # Fetch all closing price data
        crypto_data = self.get_crypto_closing_prices()
        treasury_data = self.get_treasury_yield()
        fred_data = self.get_fred_closing_rates()
        
        print("\n" + "=" * 70)
        
        # Generate comprehensive recap
        recap_result = self.generate_market_recap(crypto_data, treasury_data, fred_data)
        
        return recap_result['recap_text']

def test_treasury_api(api_key: str):
    """
    Test function to debug Treasury API connection
    
    Args:
        api_key (str): Alpha Vantage API key to test
    """
    print("🧪 Testing Treasury API Connection...")
    print("=" * 50)
    
    try:
        # Test Alpha Vantage Treasury endpoint
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'TREASURY_YIELD',
            'interval': 'daily',
            'maturity': '10year',
            'apikey': api_key
        }
        
        print(f"🔍 Testing URL: {url}")
        print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
        
        response = requests.get(url, params=params, timeout=30)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            if 'Note' in data:
                print(f"⚠️ API Note: {data['Note']}")
            elif 'Error Message' in data:
                print(f"❌ API Error: {data['Error Message']}")
            elif 'data' in data:
                print(f"📊 Data Points Available: {len(data['data'])}")
                if len(data['data']) > 0:
                    print(f"📈 Latest Yield: {data['data'][0]}")
            else:
                print(f"🔍 Full Response Preview: {str(data)[:300]}...")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📝 Response Text: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")

def main():
    """
    Main function to run the daily market recap generator
    """
    print("🔑 DAILY MARKET RECAP GENERATOR (Closing Prices)")
    print("=" * 60)
    print("📊 This script fetches market closing prices for accurate day-over-day analysis")
    print("=" * 60)
    
    # Check for test mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--test-treasury':
        print("\n🧪 TREASURY API TEST MODE")
        api_key = input("Please enter your Alpha Vantage API key: ").strip()
        if api_key:
            test_treasury_api(api_key)
        return
    
    # Get API keys from user
    api_key = input("Please enter your Alpha Vantage API key: ").strip()
    
    if not api_key:
        print("❌ API key is required to fetch Treasury data")
        return
    
    # Get Claude API key (optional)
    print("\n💡 Claude API key is optional but recommended for enhanced analysis")
    claude_key = input("Enter your Claude API key (or press Enter to skip): ").strip()
    
    if not claude_key:
        print("⚠️ Continuing without Claude analysis - using standard analysis")
    else:
        print("✅ Claude API key provided - enhanced analysis will be used")
    
    # Initialize generator
    generator = DailyMarketRecapGenerator(api_key, claude_api_key=claude_key if claude_key else None)
    
    try:
        # Generate recap
        recap_result = generator.generate_recap()
        
        # Display recap
        print("\n" + "=" * 70)
        print("📊 COMPLETE MARKET RECAP (Closing Prices)")
        print("=" * 70)
        print(recap_result)
        
        # Save recap to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"market_recap_closing_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(recap_result)
        
        print(f"\n💾 Recap saved to: {filename}")
        print("📱 Copy and paste this recap to LinkedIn for professional sharing!")
        print("💡 Tip: Post in the morning for better engagement!")
        print("✅ Data represents official market closing prices for accurate analysis!")
        
    except Exception as e:
        print(f"❌ Error generating recap: {str(e)}")
        print("Please check your API key and internet connection")

if __name__ == "__main__":
    main()
