import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func, desc
import json

class TradeLogger:
    """Comprehensive trade logging and analytics system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = None
        self.Trade = None
        self.SystemMetrics = None
    
    def init_db(self, db, Trade, SystemMetrics):
        """Initialize database connections"""
        self.db = db
        self.Trade = Trade
        self.SystemMetrics = SystemMetrics
    
    def log_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Log a completed trade to the database
        
        Args:
            trade_data: Dictionary containing trade information
            
        Returns:
            Trade ID of the logged trade
        """
        try:
            trade = self.Trade(
                route=trade_data['route'],
                input_token=trade_data['input_token'],
                output_token=trade_data['output_token'],
                input_amount=trade_data['input_amount'],
                output_amount=trade_data['output_amount'],
                price=trade_data['price'],
                slippage=trade_data['slippage'],
                jupiter_slippage=trade_data['jupiter_slippage'],
                cost_savings=trade_data.get('cost_savings', 0.0),
                execution_time=trade_data.get('execution_time', datetime.now())
            )
            
            self.db.session.add(trade)
            self.db.session.commit()
            
            self.logger.info(f"Trade logged: ID={trade.id}, Route={trade.route}, "
                           f"Amount={trade.input_amount} {trade.input_token}")
            
            # Record system metrics
            self._record_trade_metrics(trade)
            
            return trade.id
            
        except Exception as e:
            self.logger.error(f"Error logging trade: {e}")
            self.db.session.rollback()
            raise
    
    def get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent trades from the database
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        try:
            trades = self.db.session.query(self.Trade)\
                .order_by(desc(self.Trade.created_at))\
                .limit(limit)\
                .all()
            
            return [trade.to_dict() for trade in trades]
            
        except Exception as e:
            self.logger.error(f"Error getting recent trades: {e}")
            return []
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive trade statistics
        
        Returns:
            Dictionary containing various trade statistics
        """
        try:
            # Basic trade counts
            total_trades = self.db.session.query(self.Trade).count()
            dex_trades = self.db.session.query(self.Trade).filter(self.Trade.route == 'DEX').count()
            otc_trades = self.db.session.query(self.Trade).filter(self.Trade.route == 'OTC').count()
            
            # Volume statistics
            total_volume = self.db.session.query(func.sum(self.Trade.input_amount)).scalar() or 0
            dex_volume = self.db.session.query(func.sum(self.Trade.input_amount))\
                .filter(self.Trade.route == 'DEX').scalar() or 0
            otc_volume = self.db.session.query(func.sum(self.Trade.input_amount))\
                .filter(self.Trade.route == 'OTC').scalar() or 0
            
            # Cost savings
            total_savings = self.db.session.query(func.sum(self.Trade.cost_savings)).scalar() or 0
            
            # Average slippage
            avg_dex_slippage = self.db.session.query(func.avg(self.Trade.slippage))\
                .filter(self.Trade.route == 'DEX').scalar() or 0
            avg_jupiter_slippage = self.db.session.query(func.avg(self.Trade.jupiter_slippage)).scalar() or 0
            
            # Today's statistics
            today = datetime.now().date()
            today_trades = self.db.session.query(self.Trade)\
                .filter(func.date(self.Trade.created_at) == today).count()
            today_volume = self.db.session.query(func.sum(self.Trade.input_amount))\
                .filter(func.date(self.Trade.created_at) == today).scalar() or 0
            today_savings = self.db.session.query(func.sum(self.Trade.cost_savings))\
                .filter(func.date(self.Trade.created_at) == today).scalar() or 0
            
            return {
                'total_trades': total_trades,
                'dex_trades': dex_trades,
                'otc_trades': otc_trades,
                'total_volume': round(total_volume, 2),
                'dex_volume': round(dex_volume, 2),
                'otc_volume': round(otc_volume, 2),
                'total_cost_savings': round(total_savings, 2),
                'avg_dex_slippage': round(avg_dex_slippage, 4),
                'avg_jupiter_slippage': round(avg_jupiter_slippage, 4),
                'today_trades': today_trades,
                'today_volume': round(today_volume, 2),
                'today_savings': round(today_savings, 2),
                'otc_efficiency': round((otc_trades / total_trades * 100), 2) if total_trades > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting trade statistics: {e}")
            return {}
    
    def get_route_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of trades by route
        
        Returns:
            Route distribution data for charts
        """
        try:
            # Route distribution by count
            route_counts = self.db.session.query(self.Trade.route, func.count(self.Trade.id))\
                .group_by(self.Trade.route).all()
            
            # Route distribution by volume
            route_volumes = self.db.session.query(self.Trade.route, func.sum(self.Trade.input_amount))\
                .group_by(self.Trade.route).all()
            
            return {
                'by_count': [{'route': route, 'count': count} for route, count in route_counts],
                'by_volume': [{'route': route, 'volume': float(volume or 0)} for route, volume in route_volumes]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting route distribution: {e}")
            return {'by_count': [], 'by_volume': []}
    
    def get_cost_savings_analysis(self) -> Dict[str, Any]:
        """
        Get detailed cost savings analysis
        
        Returns:
            Cost savings analysis data
        """
        try:
            # Daily cost savings for the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            daily_savings = self.db.session.query(
                func.date(self.Trade.created_at).label('date'),
                func.sum(self.Trade.cost_savings).label('savings')
            ).filter(self.Trade.created_at >= thirty_days_ago)\
             .group_by(func.date(self.Trade.created_at))\
             .order_by('date').all()
            
            # Cost savings by trade size
            size_brackets = [
                (0, 100, 'Small (0-100 SOL)'),
                (100, 500, 'Medium (100-500 SOL)'),
                (500, 1000, 'Large (500-1000 SOL)'),
                (1000, float('inf'), 'Jumbo (1000+ SOL)')
            ]
            
            savings_by_size = []
            for min_size, max_size, label in size_brackets:
                query = self.db.session.query(func.sum(self.Trade.cost_savings))\
                    .filter(self.Trade.input_amount >= min_size)
                
                if max_size != float('inf'):
                    query = query.filter(self.Trade.input_amount < max_size)
                
                savings = query.scalar() or 0
                savings_by_size.append({
                    'category': label,
                    'savings': float(savings)
                })
            
            # Average savings per trade by route
            avg_savings_otc = self.db.session.query(func.avg(self.Trade.cost_savings))\
                .filter(self.Trade.route == 'OTC').scalar() or 0
            
            return {
                'daily_savings': [
                    {'date': str(date), 'savings': float(savings or 0)}
                    for date, savings in daily_savings
                ],
                'savings_by_size': savings_by_size,
                'avg_savings_per_otc_trade': round(avg_savings_otc, 2),
                'total_savings': round(sum(item['savings'] for item in savings_by_size), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cost savings analysis: {e}")
            return {'daily_savings': [], 'savings_by_size': []}
    
    def get_slippage_analysis(self) -> Dict[str, Any]:
        """
        Get slippage analysis data
        
        Returns:
            Slippage analysis for DEX vs OTC routing decisions
        """
        try:
            # Slippage distribution for different trade sizes
            slippage_data = self.db.session.query(
                self.Trade.input_amount,
                self.Trade.jupiter_slippage,
                self.Trade.route
            ).order_by(self.Trade.input_amount).all()
            
            # Group by trade size ranges
            size_ranges = []
            current_range = []
            range_size = 100  # 100 SOL ranges
            
            for trade in slippage_data:
                current_range.append({
                    'amount': trade.input_amount,
                    'slippage': trade.jupiter_slippage,
                    'route': trade.route
                })
                
                if len(current_range) >= 10:  # Group every 10 trades
                    avg_amount = sum(t['amount'] for t in current_range) / len(current_range)
                    avg_slippage = sum(t['slippage'] for t in current_range) / len(current_range)
                    otc_ratio = sum(1 for t in current_range if t['route'] == 'OTC') / len(current_range)
                    
                    size_ranges.append({
                        'avg_amount': round(avg_amount, 2),
                        'avg_slippage': round(avg_slippage, 4),
                        'otc_ratio': round(otc_ratio, 2)
                    })
                    current_range = []
            
            # Threshold analysis - how often does slippage exceed 1%
            high_slippage_trades = self.db.session.query(self.Trade)\
                .filter(self.Trade.jupiter_slippage > 1.0).count()
            total_trades = self.db.session.query(self.Trade).count()
            
            high_slippage_ratio = (high_slippage_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'size_vs_slippage': size_ranges,
                'high_slippage_ratio': round(high_slippage_ratio, 2),
                'threshold_analysis': {
                    'trades_above_1pct': high_slippage_trades,
                    'total_trades': total_trades,
                    'percentage': round(high_slippage_ratio, 2)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting slippage analysis: {e}")
            return {'size_vs_slippage': [], 'high_slippage_ratio': 0}
    
    def _record_trade_metrics(self, trade):
        """
        Record system metrics for trade
        
        Args:
            trade: Trade object to record metrics for
        """
        try:
            # Record basic metrics
            self.SystemMetrics.record_metric('trade_volume', trade.input_amount)
            self.SystemMetrics.record_metric('slippage', trade.slippage)
            self.SystemMetrics.record_metric('jupiter_slippage', trade.jupiter_slippage)
            
            if trade.cost_savings > 0:
                self.SystemMetrics.record_metric('cost_savings', trade.cost_savings)
            
            # Record route-specific metrics
            if trade.route == 'OTC':
                self.SystemMetrics.record_metric('otc_trade', 1)
            else:
                self.SystemMetrics.record_metric('dex_trade', 1)
                
        except Exception as e:
            self.logger.error(f"Error recording trade metrics: {e}")