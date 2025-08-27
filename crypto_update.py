#!/usr/bin/env python3
"""
Crypto Market Update Report Generator
Fetches cryptocurrency prices, Treasury yields, and FRED rates to create
a comprehensive market analysis report suitable for LinkedIn sharing.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List, Tuple

class CryptoMarketReporter:
    """
    Main class to generate comprehensive crypto market reports
    combining traditional finance and digital asset data
    """
    
    def __init__(self, alpha_vantage_api_key: str):
        """
        Initialize the reporter with API keys
        
        Args:
            alpha_vantage_api_key (str): Alpha Vantage API key for Treasury data
        """
        self.alpha_vantage_api_key = alpha_vantage_api_key
        self.fred_api_key = None  # FRED doesn't require API key for basic data
        
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
    
    def get_crypto_prices(self) -> Dict[str, Dict]:
        """
        Fetch current and historical cryptocurrency prices from CoinGecko
        
        Returns:
            Dict containing current prices and 24h changes for BTC, ETH, XRP
        """
        print("🔍 Fetching cryptocurrency price data...")
        
        crypto_data = {}
        
        for symbol, coin_id in self.crypto_ids.items():
            try:
                # Get current market data
                url = f"{self.coingecko_base_url}/coins/{coin_id}"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract relevant price information
                current_price = data['market_data']['current_price']['usd']
                price_change_24h = data['market_data']['price_change_percentage_24h']
                price_change_24h_usd = data['market_data']['price_change_24h']
                
                crypto_data[symbol] = {
                    'current_price': current_price,
                    'price_change_24h_pct': price_change_24h,
                    'price_change_24h_usd': price_change_24h_usd,
                    'market_cap': data['market_data']['market_cap']['usd'],
                    'volume_24h': data['market_data']['total_volume']['usd']
                }
                
                print(f"✅ {symbol}: ${current_price:,.2f} ({price_change_24h:+.2f}%)")
                
                # Rate limiting to be respectful to the API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error fetching {symbol} data: {str(e)}")
                crypto_data[symbol] = None
        
        return crypto_data
    
    def get_treasury_yield(self) -> Dict[str, float]:
        """
        Fetch 10-year Treasury yield from Alpha Vantage
        
        Returns:
            Dict containing Treasury yield data
        """
        print("🔍 Fetching Treasury yield data from Alpha Vantage...")
        
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
            
            if 'data' in data and len(data['data']) > 0:
                # Get the most recent yield data
                latest_data = data['data'][0]
                current_yield = float(latest_data['value'])
                previous_yield = float(data['data'][1]['value']) if len(data['data']) > 1 else current_yield
                yield_change = current_yield - previous_yield
                
                treasury_data = {
                    'current_yield': current_yield,
                    'previous_yield': previous_yield,
                    'yield_change': yield_change,
                    'yield_change_pct': (yield_change / previous_yield) * 100 if previous_yield != 0 else 0
                }
                
                print(f"✅ 10Y Treasury: {current_yield:.2f}% ({yield_change:+.2f}bps)")
                return treasury_data
                
            else:
                print("❌ No Treasury data found in response")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching Treasury data: {str(e)}")
            return None
    
    def get_fred_rates(self) -> Dict[str, Dict]:
        """
        Fetch short-term interest rates from FRED
        
        Returns:
            Dict containing various short-term rates
        """
        print("🔍 Fetching FRED interest rate data...")
        
        fred_data = {}
        
        for rate_name, series_id in self.fred_series.items():
            try:
                params = {
                    'series_id': series_id,
                    'api_key': self.fred_api_key,
                    'file_type': 'json',
                    'limit': 2  # Get current and previous values
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
                    
                    print(f"✅ {rate_name}: {current_value:.2f}% ({change:+.2f}bps)")
                    
                else:
                    print(f"❌ No data found for {rate_name}")
                    fred_data[rate_name] = None
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error fetching {rate_name}: {str(e)}")
                fred_data[rate_name] = None
        
        return fred_data
    
    def generate_market_analysis(self, crypto_data: Dict, treasury_data: Dict, fred_data: Dict) -> str:
        """
        Generate comprehensive market analysis linking crypto and traditional finance
        
        Args:
            crypto_data: Cryptocurrency price data
            treasury_data: Treasury yield data  
            fred_data: FRED interest rate data
            
        Returns:
            Formatted market analysis report
        """
        print("\n📊 Generating comprehensive market analysis...")
        
        # Calculate overall market sentiment
        crypto_positive = sum(1 for data in crypto_data.values() 
                            if data and data['price_change_24h_pct'] > 0)
        crypto_negative = sum(1 for data in crypto_data.values() 
                             if data and data['price_change_24h_pct'] < 0)
        
        # Determine market sentiment
        if crypto_positive > crypto_negative:
            sentiment = "bullish"
        elif crypto_negative > crypto_positive:
            sentiment = "bearish"
        else:
            sentiment = "mixed"
        
        # Generate analysis report
        report = f"""
🚀 CRYPTO MARKET UPDATE - {datetime.now().strftime('%B %d, %Y')} 🚀

📈 CRYPTOCURRENCY PERFORMANCE (24h):
"""
        
        # Add crypto performance details
        for symbol, data in crypto_data.items():
            if data:
                change_emoji = "🟢" if data['price_change_24h_pct'] > 0 else "🔴"
                report += f"{change_emoji} {symbol}: ${data['current_price']:,.2f} ({data['price_change_24h_pct']:+.2f}%)\n"
        
        # Add Treasury yield analysis
        if treasury_data:
            report += f"""
🏛️ TREASURY YIELD UPDATE:
📊 10Y Treasury: {treasury_data['current_yield']:.2f}% ({treasury_data['yield_change']:+.2f}bps)
"""
        
        # Add FRED rates analysis
        if fred_data:
            report += f"""
💵 SHORT-TERM RATES:
"""
            for rate_name, data in fred_data.items():
                if data:
                    rate_display_name = rate_name.replace('_', ' ').title()
                    change_emoji = "🟢" if data['change'] > 0 else "🔴"
                    report += f"{change_emoji} {rate_display_name}: {data['current_rate']:.2f}% ({data['change']:+.2f}bps)\n"
        
        # Add market correlation analysis
        report += f"""
🔗 MARKET CORRELATION ANALYSIS:
"""
        
        if treasury_data and crypto_data:
            # Analyze correlation between Treasury yields and crypto performance
            if treasury_data['yield_change'] > 0:
                if sentiment == "bearish":
                    report += "📉 Rising Treasury yields may be contributing to crypto selling pressure as investors seek safer yields\n"
                else:
                    report += "📈 Despite rising yields, crypto showing resilience - risk appetite remains strong\n"
            else:
                if sentiment == "bullish":
                    report += "📈 Falling Treasury yields supporting crypto rally as risk assets become more attractive\n"
                else:
                    report += "📊 Lower yields not translating to crypto gains - other factors driving market sentiment\n"
        
        # Add market summary
        report += f"""
📋 MARKET SUMMARY:
🎯 Overall Sentiment: {sentiment.upper()}
🌊 Risk Appetite: {'High' if sentiment == 'bullish' else 'Low' if sentiment == 'bearish' else 'Mixed'}
💡 Key Takeaway: {'Risk-on environment favors crypto' if sentiment == 'bullish' else 'Risk-off sentiment prevails' if sentiment == 'bearish' else 'Mixed signals suggest cautious approach'}
        
#Crypto #Markets #Treasury #Finance #DigitalAssets #TradFi #DeFi
        """
        
        return report
    
    def run_report(self) -> str:
        """
        Main method to run the complete market report
        
        Returns:
            Complete market analysis report
        """
        print("🚀 Starting Crypto Market Report Generation...")
        print("=" * 60)
        
        # Fetch all data
        crypto_data = self.get_crypto_prices()
        treasury_data = self.get_treasury_yield()
        fred_data = self.get_fred_rates()
        
        print("\n" + "=" * 60)
        
        # Generate comprehensive analysis
        report = self.generate_market_analysis(crypto_data, treasury_data, fred_data)
        
        return report

def main():
    """
    Main function to run the crypto market reporter
    """
    print("🔑 CRYPTO MARKET UPDATE REPORTER")
    print("=" * 50)
    
    # Get API key from user
    api_key = input("Please enter your Alpha Vantage API key: ").strip()
    
    if not api_key:
        print("❌ API key is required to fetch Treasury data")
        return
    
    # Initialize reporter
    reporter = CryptoMarketReporter(api_key)
    
    try:
        # Generate report
        report = reporter.run_report()
        
        # Display report
        print("\n" + "=" * 60)
        print("📊 COMPLETE MARKET REPORT")
        print("=" * 60)
        print(report)
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crypto_market_report_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\n💾 Report saved to: {filename}")
        print("📱 Copy and paste this report to LinkedIn for professional sharing!")
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        print("Please check your API key and internet connection")

if __name__ == "__main__":
    main()
