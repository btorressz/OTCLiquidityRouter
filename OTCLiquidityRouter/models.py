from app import db
from datetime import datetime
from sqlalchemy import func

class Trade(db.Model):
    """Model for storing trade execution data"""
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.String(10), nullable=False)  # 'DEX' or 'OTC'
    input_token = db.Column(db.String(20), nullable=False)
    output_token = db.Column(db.String(20), nullable=False)
    input_amount = db.Column(db.Float, nullable=False)
    output_amount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    slippage = db.Column(db.Float, nullable=False)
    jupiter_slippage = db.Column(db.Float, nullable=False)  # Jupiter's slippage for comparison
    cost_savings = db.Column(db.Float, default=0.0)
    execution_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert trade to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'route': self.route,
            'input_token': self.input_token,
            'output_token': self.output_token,
            'input_amount': self.input_amount,
            'output_amount': self.output_amount,
            'price': self.price,
            'slippage': self.slippage,
            'jupiter_slippage': self.jupiter_slippage,
            'cost_savings': self.cost_savings,
            'execution_time': self.execution_time.isoformat() if self.execution_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class OTCPool(db.Model):
    """Model for OTC pool configuration and pricing"""
    id = db.Column(db.Integer, primary_key=True)
    base_token = db.Column(db.String(20), nullable=False)
    quote_token = db.Column(db.String(20), nullable=False)
    liquidity = db.Column(db.Float, nullable=False)  # Available liquidity
    spread = db.Column(db.Float, default=0.5)  # Spread percentage
    min_trade_size = db.Column(db.Float, default=100.0)
    max_trade_size = db.Column(db.Float, default=10000.0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemMetrics(db.Model):
    """Model for storing system performance metrics"""
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(50), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def record_metric(cls, name, value):
        """Record a system metric"""
        metric = cls(metric_name=name, metric_value=value)
        db.session.add(metric)
        db.session.commit()
        return metric
