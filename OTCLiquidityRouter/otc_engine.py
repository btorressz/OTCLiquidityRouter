import logging
from datetime import datetime
from typing import Dict, Any, Optional
import random
import time

class OTCEngine:
    """OTC pool simulation engine with fixed pricing and liquidity management"""
    
    def __init__(self):
        # Simulated OTC pools with different characteristics
        self.otc_pools = {
            'SOL/USDC': {
                'liquidity': 50000.0,  # 50K SOL available
                'spread': 0.25,        # 0.25% spread
                'min_trade': 100.0,    # Minimum 100 SOL
                'max_trade': 5000.0,   # Maximum 5000 SOL per trade
                'base_price_offset': 0.0,  # No offset from market price
                'active': True
            },
            'SOL/USDT': {
                'liquidity': 25000.0,
                'spread': 0.35,
                'min_trade': 250.0,
                'max_trade': 2500.0,
                'base_price_offset': -0.1,  # Slightly below market
                'active': True
            }
        }
        
        # Fallback prices (used only if API calls fail)
        self.fallback_prices = {
            'SOL': 150.0,  # $150 per SOL
            'USDC': 1.0,   # $1 per USDC
            'USDT': 1.0    # $1 per USDT
        }
        
        # Trade execution simulation
        self.execution_delay_range = (0.5, 2.0)  # 0.5-2 seconds execution time
        
        # Price cache to avoid excessive API calls
        self.price_cache = {}
        self.cache_timestamp = 0
        self.cache_duration = 30  # Cache prices for 30 seconds
        
    def get_otc_quote(self, input_token: str, output_token: str, amount: float) -> Dict[str, Any]:
        """
        Get OTC quote for a trade
        
        Args:
            input_token: Input token symbol
            output_token: Output token symbol
            amount: Input amount
            
        Returns:
            OTC quote data
        """
        try:
            pair = f"{input_token}/{output_token}"
            
            # Check if OTC pool exists for this pair
            if pair not in self.otc_pools:
                return {
                    'available': False,
                    'error': f'No OTC pool available for {pair}'
                }
            
            pool = self.otc_pools[pair]
            
            # Check if pool is active
            if not pool['active']:
                return {
                    'available': False,
                    'error': f'OTC pool for {pair} is currently inactive'
                }
            
            # Check trade size limits
            if amount < pool['min_trade']:
                return {
                    'available': False,
                    'error': f'Trade size {amount} below minimum {pool["min_trade"]}'
                }
            
            if amount > pool['max_trade']:
                return {
                    'available': False,
                    'error': f'Trade size {amount} exceeds maximum {pool["max_trade"]}'
                }
            
            # Check liquidity availability
            if amount > pool['liquidity']:
                return {
                    'available': False,
                    'error': f'Insufficient liquidity. Available: {pool["liquidity"]}, Requested: {amount}'
                }
            
            # Calculate OTC price
            base_price = self._get_market_price(input_token, output_token)
            spread_adjustment = pool['spread'] / 100  # Convert to decimal
            price_offset = pool['base_price_offset'] / 100
            
            # OTC price includes spread and offset
            otc_price = base_price * (1 - spread_adjustment + price_offset)
            output_amount = amount * otc_price
            
            # Add some randomness to simulate real OTC pricing
            price_variance = random.uniform(-0.001, 0.001)  # ±0.1% variance
            otc_price *= (1 + price_variance)
            output_amount *= (1 + price_variance)
            
            return {
                'available': True,
                'pair': pair,
                'input_token': input_token,
                'output_token': output_token,
                'input_amount': amount,
                'output_amount': round(output_amount, 6),
                'price': round(otc_price, 6),
                'spread': pool['spread'],
                'execution_estimate': f"{self.execution_delay_range[0]}-{self.execution_delay_range[1]}s",
                'pool_liquidity_remaining': pool['liquidity'] - amount,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting OTC quote: {e}")
            return {
                'available': False,
                'error': f'Error calculating OTC quote: {str(e)}'
            }
    
    def execute_trade(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate OTC trade execution
        
        Args:
            quote: OTC quote from get_otc_quote
            
        Returns:
            Execution result
        """
        try:
            if not quote.get('available'):
                return {
                    'status': 'failed',
                    'error': quote.get('error', 'Quote not available')
                }
            
            # Simulate execution delay
            execution_delay = random.uniform(*self.execution_delay_range)
            time.sleep(execution_delay)
            
            # Update pool liquidity
            pair = quote['pair']
            if pair in self.otc_pools:
                self.otc_pools[pair]['liquidity'] -= quote['input_amount']
            
            # Generate simulated transaction data
            tx_signature = f"otc_tx_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
            
            execution_result = {
                'status': 'success',
                'tx_signature': tx_signature,
                'input_token': quote['input_token'],
                'output_token': quote['output_token'],
                'input_amount': quote['input_amount'],
                'output_amount': quote['output_amount'],
                'execution_price': quote['price'],
                'execution_time': datetime.now(),
                'execution_delay': execution_delay,
                'pool_used': pair,
                'remaining_liquidity': self.otc_pools[pair]['liquidity'] if pair in self.otc_pools else 0
            }
            
            logging.info(f"OTC trade executed: {execution_result}")
            return execution_result
            
        except Exception as e:
            logging.error(f"Error executing OTC trade: {e}")
            return {
                'status': 'failed',
                'error': f'Execution failed: {str(e)}'
            }
    
    def _get_real_time_price(self, token_symbol: str) -> float:
        """
        Get real-time price with caching
        
        Args:
            token_symbol: Token symbol (SOL, USDC, etc.)
            
        Returns:
            Current price in USD
        """
        current_time = time.time()
        
        # Check cache first
        if (current_time - self.cache_timestamp < self.cache_duration and 
            token_symbol in self.price_cache):
            return self.price_cache[token_symbol]
        
        try:
            # Import here to avoid circular imports
            from jupiter_api import JupiterAPI
            
            jupiter_api = JupiterAPI()
            token_mint = jupiter_api.get_token_mint(token_symbol)
            price = jupiter_api.get_token_price(token_mint)
            
            if price is not None:
                # Update cache
                self.price_cache[token_symbol] = price
                self.cache_timestamp = current_time
                return price
            else:
                # Fallback to cached price or default
                return self.price_cache.get(token_symbol, self.fallback_prices.get(token_symbol, 1.0))
                
        except Exception as e:
            logging.error(f"Error getting real-time price for {token_symbol}: {e}")
            return self.price_cache.get(token_symbol, self.fallback_prices.get(token_symbol, 1.0))

    def _get_market_price(self, input_token: str, output_token: str) -> float:
        """
        Get market price for token pair using real-time data
        
        Args:
            input_token: Input token symbol
            output_token: Output token symbol
            
        Returns:
            Market price
        """
        try:
            input_price = self._get_real_time_price(input_token)
            output_price = self._get_real_time_price(output_token)
            
            # Calculate exchange rate
            market_price = input_price / output_price
            
            # Add small volatility for OTC simulation (smaller than before since we have real prices)
            volatility = random.uniform(-0.005, 0.005)  # ±0.5% volatility
            market_price *= (1 + volatility)
            
            return market_price
            
        except Exception as e:
            logging.error(f"Error getting market price: {e}")
            # Fallback to cached or default prices
            input_price = self.price_cache.get(input_token, self.fallback_prices.get(input_token, 150.0))
            output_price = self.price_cache.get(output_token, self.fallback_prices.get(output_token, 1.0))
            return input_price / output_price
    
    def get_pool_status(self) -> Dict[str, Any]:
        """
        Get status of all OTC pools
        
        Returns:
            Pool status information
        """
        try:
            pool_status = {}
            total_liquidity = 0
            active_pools = 0
            
            for pair, pool in self.otc_pools.items():
                pool_status[pair] = {
                    'liquidity': pool['liquidity'],
                    'spread': pool['spread'],
                    'min_trade': pool['min_trade'],
                    'max_trade': pool['max_trade'],
                    'active': pool['active'],
                    'utilization': max(0, (50000 - pool['liquidity']) / 50000 * 100)  # Assuming 50K initial
                }
                
                if pool['active']:
                    active_pools += 1
                    total_liquidity += pool['liquidity']
            
            return {
                'pools': pool_status,
                'summary': {
                    'total_active_pools': active_pools,
                    'total_liquidity': total_liquidity,
                    'average_spread': sum(p['spread'] for p in self.otc_pools.values()) / len(self.otc_pools)
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting pool status: {e}")
            return {'error': str(e)}
    
    def update_pool_liquidity(self, pair: str, new_liquidity: float) -> bool:
        """
        Update liquidity for an OTC pool
        
        Args:
            pair: Trading pair (e.g., 'SOL/USDC')
            new_liquidity: New liquidity amount
            
        Returns:
            Success status
        """
        try:
            if pair in self.otc_pools:
                self.otc_pools[pair]['liquidity'] = new_liquidity
                logging.info(f"Updated {pair} liquidity to {new_liquidity}")
                return True
            else:
                logging.error(f"Pool {pair} not found")
                return False
                
        except Exception as e:
            logging.error(f"Error updating pool liquidity: {e}")
            return False
