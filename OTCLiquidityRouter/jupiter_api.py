import requests
import logging
from typing import Optional, Dict, Any
import os
import time

class JupiterAPI:
    """Jupiter DEX API integration for real-time quotes and liquidity analysis"""
    
    def __init__(self):
        self.base_url = "https://quote-api.jup.ag/v6"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OTC-Routing-Engine/1.0'
        })
        
        # Token mint addresses for common tokens
        self.token_mints = {
            'SOL': 'So11111111111111111111111111111111111111112',
            'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
            'RAY': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',
            'SRM': 'SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt'
        }
        
    def get_token_mint(self, symbol: str) -> str:
        """Get token mint address by symbol"""
        return self.token_mints.get(symbol.upper(), symbol)
    
    def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50) -> Optional[Dict[str, Any]]:
        """
        Get quote from Jupiter API
        
        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address  
            amount: Input amount in smallest unit (lamports for SOL)
            slippage_bps: Slippage tolerance in basis points (50 = 0.5%)
        
        Returns:
            Quote data or None if failed
        """
        try:
            params = {
                'inputMint': input_mint,
                'outputMint': output_mint,
                'amount': amount,
                'slippageBps': slippage_bps
            }
            
            logging.debug(f"Requesting Jupiter quote: {params}")
            
            response = self.session.get(f"{self.base_url}/quote", params=params, timeout=10)
            response.raise_for_status()
            
            quote_data = response.json()
            logging.debug(f"Jupiter quote received: {quote_data}")
            
            return quote_data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Jupiter API request failed: {e}")
            return None
        except Exception as e:
            logging.error(f"Error getting Jupiter quote: {e}")
            return None
    
    def calculate_slippage(self, quote_data: Dict[str, Any]) -> float:
        """
        Calculate slippage percentage from quote data
        
        Args:
            quote_data: Quote response from Jupiter API
            
        Returns:
            Slippage percentage
        """
        try:
            if not quote_data or 'priceImpactPct' not in quote_data:
                # Estimate slippage based on route complexity
                route_plan = quote_data.get('routePlan', [])
                if len(route_plan) > 2:
                    return 2.5  # Higher slippage for complex routes
                elif len(route_plan) > 1:
                    return 1.5  # Moderate slippage for multi-hop
                else:
                    return 0.5  # Low slippage for direct routes
            
            # Jupiter returns price impact as decimal (0.01 = 1%)
            price_impact = float(quote_data.get('priceImpactPct', 0))
            return abs(price_impact * 100)  # Convert to percentage
            
        except Exception as e:
            logging.error(f"Error calculating slippage: {e}")
            return 5.0  # Conservative estimate if calculation fails
    
    def get_token_price(self, token_mint: str) -> Optional[float]:
        """
        Get current token price from multiple sources
        
        Args:
            token_mint: Token mint address
            
        Returns:
            Token price in USD or None if failed
        """
        try:
            # First try Jupiter's price API
            response = self.session.get(
                f"https://price.jup.ag/v4/price",
                params={'ids': token_mint},
                timeout=5
            )
            
            if response.status_code == 200:
                price_data = response.json()
                if 'data' in price_data and token_mint in price_data['data']:
                    return float(price_data['data'][token_mint]['price'])
            
            # Fallback to CoinGecko for major tokens
            return self._get_coingecko_price(token_mint)
            
        except Exception as e:
            logging.error(f"Error getting token price: {e}")
            return self._get_coingecko_price(token_mint)

    def _get_coingecko_price(self, token_mint: str) -> Optional[float]:
        """
        Get token price from CoinGecko API
        
        Args:
            token_mint: Token mint address
            
        Returns:
            Token price in USD or None if failed
        """
        try:
            # Map token mints to CoinGecko IDs
            coingecko_ids = {
                'So11111111111111111111111111111111111111112': 'solana',  # SOL
                'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': 'usd-coin',  # USDC
                'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': 'tether',  # USDT
                '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R': 'raydium',  # RAY
                'SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt': 'serum'  # SRM
            }
            
            coingecko_id = coingecko_ids.get(token_mint)
            if not coingecko_id:
                return None
            
            response = self.session.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={
                    'ids': coingecko_id,
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true'
                },
                timeout=5
            )
            response.raise_for_status()
            
            price_data = response.json()
            if coingecko_id in price_data and 'usd' in price_data[coingecko_id]:
                return float(price_data[coingecko_id]['usd'])
            
            return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"CoinGecko API request failed: {e}")
            return None
        except Exception as e:
            logging.error(f"Error getting CoinGecko price: {e}")
            return None

    def get_multiple_token_prices(self) -> Dict[str, Any]:
        """
        Get prices for multiple tokens using multiple data sources
        
        Returns:
            Dictionary with token prices and metadata
        """
        current_time = time.time()
        
        # Check cache first (5 minute cache for real-time feel)
        if (hasattr(self, 'price_cache') and self.price_cache and 
            current_time - self.price_cache.get('cached_at', 0) < 300):
            return self.price_cache
        
        # Fallback prices only as last resort
        fallback_prices = {
            'SOL': {
                'price': 150.0,
                'change_24h': 0.0,
                'last_updated': int(current_time),
                'mint': 'So11111111111111111111111111111111111111112'
            },
            'USDC': {
                'price': 1.0,
                'change_24h': 0.0,
                'last_updated': int(current_time),
                'mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
            },
            'USDT': {
                'price': 1.0,
                'change_24h': 0.0,
                'last_updated': int(current_time),
                'mint': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
            },
            'RAY': {
                'price': 2.5,
                'change_24h': 0.0,
                'last_updated': int(current_time),
                'mint': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R'
            },
            'SRM': {
                'price': 0.4,
                'change_24h': 0.0,
                'last_updated': int(current_time),
                'mint': 'SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt'
            }
        }
        
        try:
            # Try multiple data sources in order of preference
            
            # Method 1: Try CoinGecko first (most comprehensive)
            try:
                response = self.session.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        'ids': 'solana,usd-coin,tether,raydium,serum',
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_last_updated_at': 'true'
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Map CoinGecko response to our format
                    token_mapping = {
                        'solana': {'symbol': 'SOL', 'mint': 'So11111111111111111111111111111111111111112'},
                        'usd-coin': {'symbol': 'USDC', 'mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'},
                        'tether': {'symbol': 'USDT', 'mint': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'},
                        'raydium': {'symbol': 'RAY', 'mint': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R'},
                        'serum': {'symbol': 'SRM', 'mint': 'SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt'}
                    }
                    
                    prices = {}
                    for coingecko_id, token_info in token_mapping.items():
                        if coingecko_id in data:
                            token_data = data[coingecko_id]
                            prices[token_info['symbol']] = {
                                'price': token_data.get('usd', fallback_prices[token_info['symbol']]['price']),
                                'change_24h': token_data.get('usd_24h_change', 0.0),
                                'last_updated': token_data.get('last_updated_at', int(current_time)),
                                'mint': token_info['mint']
                            }
                        else:
                            prices[token_info['symbol']] = fallback_prices[token_info['symbol']]
                    
                    result = {
                        'prices': prices,
                        'last_updated': int(current_time),
                        'source': 'coingecko_live',
                        'cached_at': current_time
                    }
                    
                    # Cache successful result
                    self.price_cache = result
                    return result
                    
                elif response.status_code == 429:
                    logging.warning("CoinGecko rate limited, trying Kraken")
                    
            except Exception as e:
                logging.warning(f"CoinGecko error: {e}, trying Kraken")
            
            # Method 2: Try Kraken API for SOL/USD
            try:
                response = self.session.get(
                    "https://api.kraken.com/0/public/Ticker",
                    params={'pair': 'SOLUSD'},
                    timeout=5
                )
                
                if response.status_code == 200:
                    kraken_data = response.json()
                    
                    if 'result' in kraken_data and 'SOLUSD' in kraken_data['result']:
                        sol_data = kraken_data['result']['SOLUSD']
                        sol_price = float(sol_data['c'][0])  # Last trade closed price
                        
                        # Get stablecoin prices from another source or use standard values
                        prices = {
                            'SOL': {
                                'price': sol_price,
                                'change_24h': 0.0,  # Kraken doesn't provide 24h change in this format
                                'last_updated': int(current_time),
                                'mint': 'So11111111111111111111111111111111111111112'
                            },
                            'USDC': {
                                'price': 1.0001,
                                'change_24h': 0.01,
                                'last_updated': int(current_time),
                                'mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
                            },
                            'USDT': {
                                'price': 0.9999,
                                'change_24h': -0.01,
                                'last_updated': int(current_time),
                                'mint': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
                            },
                            'RAY': fallback_prices['RAY'],
                            'SRM': fallback_prices['SRM']
                        }
                        
                        result = {
                            'prices': prices,
                            'last_updated': int(current_time),
                            'source': 'kraken_partial',
                            'cached_at': current_time
                        }
                        
                        # Cache partial result
                        self.price_cache = result
                        return result
                        
            except Exception as e:
                logging.warning(f"Kraken error: {e}")
            
            # Method 3: Try Binance API for backup
            try:
                response = self.session.get(
                    "https://api.binance.com/api/v3/ticker/price",
                    params={'symbol': 'SOLUSDT'},
                    timeout=5
                )
                
                if response.status_code == 200:
                    binance_data = response.json()
                    sol_price = float(binance_data['price'])
                    
                    prices = {
                        'SOL': {
                            'price': sol_price,
                            'change_24h': 0.0,
                            'last_updated': int(current_time),
                            'mint': 'So11111111111111111111111111111111111111112'
                        },
                        'USDC': {
                            'price': 1.0001,
                            'change_24h': 0.01,
                            'last_updated': int(current_time),
                            'mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
                        },
                        'USDT': {
                            'price': 0.9999,
                            'change_24h': -0.01,
                            'last_updated': int(current_time),
                            'mint': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
                        },
                        'RAY': fallback_prices['RAY'],
                        'SRM': fallback_prices['SRM']
                    }
                    
                    result = {
                        'prices': prices,
                        'last_updated': int(current_time),
                        'source': 'binance_partial',
                        'cached_at': current_time
                    }
                    
                    # Cache partial result
                    self.price_cache = result
                    return result
                    
            except Exception as e:
                logging.warning(f"Binance error: {e}")
            
            # Last resort: return fallback but mark it clearly
            logging.error("All price APIs failed, using fallback prices")
            result = {
                'prices': fallback_prices,
                'last_updated': int(current_time),
                'source': 'all_apis_failed',
                'cached_at': current_time
            }
            return result
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"CoinGecko API error: {e}, using fallback prices")
            return {
                'prices': fallback_prices,
                'last_updated': int(time.time()),
                'source': 'api_error_fallback'
            }
        except Exception as e:
            logging.error(f"Error getting multiple token prices: {e}")
            return {
                'prices': fallback_prices,
                'last_updated': int(time.time()),
                'source': 'emergency_fallback'
            }
    
    def check_liquidity_depth(self, input_mint: str, output_mint: str, amount: int) -> Dict[str, Any]:
        """
        Check liquidity depth for a given trade size
        
        Args:
            input_mint: Input token mint
            output_mint: Output token mint
            amount: Trade amount to check
            
        Returns:
            Liquidity analysis data
        """
        try:
            # Get quotes for different trade sizes to analyze liquidity depth
            test_amounts = [
                amount // 4,    # 25% of trade
                amount // 2,    # 50% of trade  
                amount,         # Full trade
                amount * 2      # 2x trade size
            ]
            
            quotes = []
            for test_amount in test_amounts:
                quote = self.get_quote(input_mint, output_mint, test_amount)
                if quote:
                    slippage = self.calculate_slippage(quote)
                    quotes.append({
                        'amount': test_amount,
                        'slippage': slippage,
                        'output_amount': int(quote['outAmount'])
                    })
                time.sleep(0.1)  # Rate limiting
            
            if not quotes:
                return {'status': 'error', 'message': 'No quotes available'}
            
            # Analyze liquidity depth
            analysis = {
                'status': 'success',
                'quotes': quotes,
                'liquidity_warning': False,
                'recommended_max_size': amount
            }
            
            # Check if slippage increases significantly with size
            if len(quotes) >= 2:
                slippage_increase = quotes[-1]['slippage'] - quotes[0]['slippage']
                if slippage_increase > 2.0:  # 2% increase in slippage
                    analysis['liquidity_warning'] = True
                    analysis['recommended_max_size'] = test_amounts[1]  # Recommend smaller size
            
            return analysis
            
        except Exception as e:
            logging.error(f"Error checking liquidity depth: {e}")
            return {'status': 'error', 'message': str(e)}
