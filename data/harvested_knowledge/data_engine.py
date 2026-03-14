import os
import json
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp

@dataclass
class MarketData:
    symbol: str
    price: float
    change_24h: float
    volume: float
    timestamp: datetime
    source: str

class FreeDataEngine:
    """
    Fetches market data using FREE APIs (no keys required for basic data).
    Falls back to cached data if APIs fail.
    """
    
    def __init__(self):
        self.cache: Dict[str, MarketData] = {}
        self.cache_time = timedelta(minutes=5)
        self.last_update: Dict[str, datetime] = {}
    
    async def get_crypto_price(self, symbol: str = "BTC") -> Optional[MarketData]:
        """
        Get crypto price from free CoinGecko API (no key required).
        """
        cache_key = f"crypto_{symbol}"
        
        # Check cache
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        try:
            async with aiohttp.ClientSession() as session:
                # CoinGecko free API (no key needed)
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if symbol.lower() in data:
                            coin_data = data[symbol.lower()]
                            market_data = MarketData(
                                symbol=symbol.upper(),
                                price=coin_data["usd"],
                                change_24h=coin_data.get("usd_24h_change", 0),
                                volume=coin_data.get("usd_24h_vol", 0),
                                timestamp=datetime.now(),
                                source="coingecko_free"
                            )
                            self._update_cache(cache_key, market_data)
                            return market_data
        except Exception as e:
            print(f"Error fetching crypto {symbol}: {e}")
        
        return self._get_cached_or_none(cache_key)
    
    async def get_stock_price(self, symbol: str = "AAPL") -> Optional[MarketData]:
        """
        Get stock price from free Yahoo Finance proxy.
        """
        cache_key = f"stock_{symbol}"
        
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        try:
            # Using Yahoo Finance via RapidAPI free tier or direct
            # For now, return mock data with realistic structure
            # Replace with real API when you get Alpha Vantage key
            
            mock_data = MarketData(
                symbol=symbol.upper(),
                price=150.0 + (hash(symbol) % 50),  # Deterministic "random" price
                change_24h=2.5,
                volume=1000000,
                timestamp=datetime.now(),
                source="mock_data"
            )
            self._update_cache(cache_key, mock_data)
            return mock_data
            
        except Exception as e:
            print(f"Error fetching stock {symbol}: {e}")
        
        return self._get_cached_or_none(cache_key)
    
    def _is_cached(self, key: str) -> bool:
        if key not in self.last_update:
            return False
        return datetime.now() - self.last_update[key] < self.cache_time
    
    def _update_cache(self, key: str, data: MarketData):
        self.cache[key] = data
        self.last_update[key] = datetime.now()
    
    def _get_cached_or_none(self, key: str) -> Optional[MarketData]:
        return self.cache.get(key)
    
    async def get_multiple_assets(self, crypto_symbols: List[str], stock_symbols: List[str]) -> Dict[str, MarketData]:
        """
        Fetch multiple assets in parallel.
        """
        tasks = []
        
        for symbol in crypto_symbols:
            tasks.append(self.get_crypto_price(symbol))
        
        for symbol in stock_symbols:
            tasks.append(self.get_stock_price(symbol))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        assets = {}
        for i, result in enumerate(results):
            if isinstance(result, MarketData):
                assets[result.symbol] = result
            elif i < len(crypto_symbols):
                print(f"Failed to fetch crypto: {crypto_symbols[i]}")
            else:
                stock_idx = i - len(crypto_symbols)
                print(f"Failed to fetch stock: {stock_symbols[stock_idx]}")
        
        return assets
