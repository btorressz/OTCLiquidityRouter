import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import json

from jupiter_api import JupiterAPI
from otc_engine import OTCEngine
from trade_logger import TradeLogger

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///otc_routing.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Initialize services
jupiter_api = JupiterAPI()
otc_engine = OTCEngine()
trade_logger = TradeLogger()

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Initialize trade logger with database references
    trade_logger.init_db(db, models.Trade, models.SystemMetrics)

@app.route('/')
def dashboard():
    """Main dashboard showing recent trades and system status"""
    try:
        recent_trades = trade_logger.get_recent_trades(limit=10)
        trade_stats = trade_logger.get_trade_statistics()
        
        return render_template('dashboard.html', 
                             recent_trades=recent_trades,
                             trade_stats=trade_stats)
    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template('dashboard.html', recent_trades=[], trade_stats={})

@app.route('/trade', methods=['GET', 'POST'])
def trade_form():
    """Trade execution form and handler"""
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            input_token = request.form.get('input_token', 'SOL')
            output_token = request.form.get('output_token', 'USDC')
            
            if amount < 0.1:
                flash("Minimum trade amount is 0.1 SOL", "error")
                return render_template('trade_form.html')
            
            # Get Jupiter quote
            jupiter_quote = jupiter_api.get_quote(
                input_mint=jupiter_api.get_token_mint(input_token),
                output_mint=jupiter_api.get_token_mint(output_token),
                amount=int(amount * 1e9)  # Convert to lamports
            )
            
            if not jupiter_quote:
                flash("Failed to get Jupiter quote", "error")
                return render_template('trade_form.html')
            
            # Calculate slippage
            slippage = jupiter_api.calculate_slippage(jupiter_quote)
            
            # Determine routing based on slippage and amount
            use_otc = False
            if amount >= 500 and slippage > 1.0:  # Large trade with high slippage
                use_otc = True
            
            # Execute trade
            if use_otc:
                # Route to OTC
                otc_quote = otc_engine.get_otc_quote(input_token, output_token, amount)
                execution_result = otc_engine.execute_trade(otc_quote)
                
                # Calculate cost savings
                dex_cost = float(jupiter_quote['outAmount']) / 1e6  # USDC has 6 decimals
                otc_cost = otc_quote['output_amount']
                cost_savings = otc_cost - dex_cost
                
                trade_data = {
                    'route': 'OTC',
                    'input_token': input_token,
                    'output_token': output_token,
                    'input_amount': amount,
                    'output_amount': otc_quote['output_amount'],
                    'price': otc_quote['price'],
                    'slippage': 0.0,  # OTC has fixed pricing
                    'jupiter_slippage': slippage,
                    'cost_savings': cost_savings,
                    'execution_time': execution_result['execution_time']
                }
            else:
                # Route to DEX (Jupiter)
                # In real implementation, would execute via Jupiter
                execution_result = {
                    'status': 'simulated',
                    'execution_time': datetime.now(),
                    'tx_signature': 'simulated_tx_' + str(int(datetime.now().timestamp()))
                }
                
                trade_data = {
                    'route': 'DEX',
                    'input_token': input_token,
                    'output_token': output_token,
                    'input_amount': amount,
                    'output_amount': float(jupiter_quote['outAmount']) / 1e6,
                    'price': float(jupiter_quote['outAmount']) / 1e6 / amount,
                    'slippage': slippage,
                    'jupiter_slippage': slippage,
                    'cost_savings': 0.0,
                    'execution_time': execution_result['execution_time']
                }
            
            # Log the trade
            trade_id = trade_logger.log_trade(trade_data)
            
            flash(f"Trade executed successfully! Route: {trade_data['route']}, Trade ID: {trade_id}", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            flash(f"Error executing trade: {str(e)}", "error")
    
    return render_template('trade_form.html')

@app.route('/analytics')
def analytics():
    """Analytics dashboard showing trade statistics and performance"""
    try:
        # Get comprehensive analytics
        trade_stats = trade_logger.get_trade_statistics()
        route_distribution = trade_logger.get_route_distribution()
        cost_savings_data = trade_logger.get_cost_savings_analysis()
        slippage_analysis = trade_logger.get_slippage_analysis()
        
        return render_template('analytics.html',
                             trade_stats=trade_stats,
                             route_distribution=route_distribution,
                             cost_savings_data=cost_savings_data,
                             slippage_analysis=slippage_analysis)
    except Exception as e:
        logging.error(f"Error loading analytics: {e}")
        flash(f"Error loading analytics: {str(e)}", "error")
        # Provide default empty data structure
        default_trade_stats = {
            'total_trades': 0,
            'total_volume': 0.0,
            'avg_cost_savings': 0.0,
            'otc_trades': 0,
            'dex_trades': 0
        }
        default_route_distribution = {
            'by_count': {'OTC': 0, 'DEX': 0},
            'by_volume': {'OTC': 0, 'DEX': 0}
        }
        default_cost_savings = {
            'total_savings': 0.0,
            'avg_savings_per_trade': 0.0,
            'savings_distribution': []
        }
        default_slippage = {
            'avg_jupiter_slippage': 0.0,
            'avg_otc_slippage': 0.0,
            'slippage_comparison': []
        }
        return render_template('analytics.html',
                             trade_stats=default_trade_stats,
                             route_distribution=default_route_distribution,
                             cost_savings_data=default_cost_savings,
                             slippage_analysis=default_slippage)

@app.route('/api/quote')
def api_quote():
    """API endpoint for getting trade quotes"""
    try:
        input_token = request.args.get('input_token', 'SOL')
        output_token = request.args.get('output_token', 'USDC')
        amount = float(request.args.get('amount', 0))
        
        if amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        
        # Get Jupiter quote
        jupiter_quote = jupiter_api.get_quote(
            input_mint=jupiter_api.get_token_mint(input_token),
            output_mint=jupiter_api.get_token_mint(output_token),
            amount=int(amount * 1e9)
        )
        
        if not jupiter_quote:
            return jsonify({'error': 'Failed to get Jupiter quote'}), 500
        
        slippage = jupiter_api.calculate_slippage(jupiter_quote)
        
        # Get OTC quote for comparison
        otc_quote = otc_engine.get_otc_quote(input_token, output_token, amount)
        
        # Determine recommended route
        recommended_route = 'OTC' if (amount >= 500 and slippage > 1.0) else 'DEX'
        
        return jsonify({
            'jupiter_quote': {
                'output_amount': float(jupiter_quote['outAmount']) / 1e6,
                'slippage': slippage,
                'route_plan': len(jupiter_quote.get('routePlan', []))
            },
            'otc_quote': otc_quote,
            'recommended_route': recommended_route,
            'cost_savings': otc_quote['output_amount'] - (float(jupiter_quote['outAmount']) / 1e6) if recommended_route == 'OTC' else 0
        })
        
    except Exception as e:
        logging.error(f"Error getting quote: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades')
def api_trades():
    """API endpoint for getting recent trades"""
    try:
        limit = int(request.args.get('limit', 20))
        trades = trade_logger.get_recent_trades(limit=limit)
        return jsonify(trades)
    except Exception as e:
        logging.error(f"Error getting trades: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prices')
def api_prices():
    """API endpoint for getting real-time token prices"""
    try:
        # Get multiple token prices
        price_data = jupiter_api.get_multiple_token_prices()
        
        if 'error' in price_data:
            return jsonify({'error': price_data['error']}), 500
        
        return jsonify(price_data)
        
    except Exception as e:
        logging.error(f"Error getting prices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-sample-data')
def add_sample_data():
    """Add sample trade data for analytics demonstration"""
    try:
        from datetime import datetime, timedelta
        import random
        
        # Check if we already have enough data
        existing_trades = trade_logger.get_recent_trades(limit=50)
        if len(existing_trades) >= 20:
            return jsonify({'message': 'Sufficient sample data already exists', 'trades': len(existing_trades)})
        
        # Add sample trades over the last 7 days
        sample_trades = []
        for i in range(15):
            days_ago = random.randint(0, 7)
            trade_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            # Random trade parameters
            input_amount = random.uniform(100, 2000)
            route = random.choice(['OTC', 'DEX'])
            jupiter_slippage = random.uniform(0.1, 3.0)
            
            if route == 'OTC':
                actual_slippage = random.uniform(0.1, 0.8)
                cost_savings = (jupiter_slippage - actual_slippage) * input_amount * 0.01
            else:
                actual_slippage = jupiter_slippage
                cost_savings = 0.0
            
            trade_data = {
                'route': route,
                'input_token': 'SOL',
                'output_token': 'USDC',
                'input_amount': input_amount,
                'output_amount': input_amount * 165.5,  # SOL price
                'price': 165.5,
                'slippage': actual_slippage,
                'jupiter_slippage': jupiter_slippage,
                'cost_savings': cost_savings,
                'execution_time': trade_time
            }
            
            # Log the trade
            trade_id = trade_logger.log_trade(trade_data)
            sample_trades.append(trade_id)
        
        return jsonify({
            'message': 'Sample data added successfully',
            'trades_created': len(sample_trades),
            'trade_ids': sample_trades
        })
        
    except Exception as e:
        logging.error(f"Error adding sample data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
