# 🔗 OTCLiquidityRouter – OTC Routing Engine

## 📄 Overview

The **OTC Routing Engine** is a Solana-based trading system that intelligently routes large trades between Jupiter DEX and simulated OTC pools based on slippage analysis and cost optimization.  
It provides real-time trade execution, analytics, and monitoring capabilities through a Flask web application.

---

## 🏛️ System Architecture

### 🎨 Frontend Architecture
- **Framework:** Flask with Jinja2 templating
- **UI Framework:** Bootstrap 5.3.2 with dark theme
- **JavaScript:** Vanilla JS with Chart.js for data visualization
- **Styling:** Custom CSS with CSS variables for theming
- **Icons:** Bootstrap Icons

### ⚙️ Backend Architecture
- **Framework:** Flask (Python web framework)
- **WSGI Server:** Gunicorn for production deployment
- **Database ORM:** SQLAlchemy with Flask-SQLAlchemy extension
- **Database:** SQLite for development *(configurable to PostgreSQL via `DATABASE_URL`)*
- **API Integration:** Custom Jupiter DEX API client
- **Trade Engine:** Simulated OTC pool engine with configurable parameters

### 💾 Data Storage Solutions
- **Primary Database:** SQLite (development) / PostgreSQL (production)
- **Schema:** Three main models:
  - **Trade:** Records all trade executions with routing decisions
  - **OTCPool:** Configuration and liquidity management for OTC pools
  - **SystemMetrics:** System performance and analytics data

---

# 🗂️ Key Components

### 🔗 Jupiter API Integration (`jupiter_api.py`)
- **Purpose:** Interfaces with Jupiter DEX API for real-time quotes and liquidity analysis
- **Features:** Token mint address management, quote retrieval with slippage tolerance
- **Rate Limiting:** Built-in session management and error handling

### 🏦 OTC Engine (`otc_engine.py`)
- **Purpose:** Simulates OTC pool behavior with realistic pricing and liquidity constraints
- **Features:**
  - Multiple pool configurations (e.g., SOL/USDC, SOL/USDT)
  - Dynamic spread calculation
  - Liquidity management with trade size limits
  - Execution delay simulation

### 📝 Trade Logger (`trade_logger.py`)
- **Purpose:** Comprehensive logging and analytics system
- **Features:**
  - Trade execution recording
  - System metrics tracking
  - Cost savings analysis
  - Performance monitoring

### 🗃️ Models (`models.py`)
- **Trade Model:** Stores execution data, routing decisions, and performance metrics
- **OTCPool Model:** Manages pool configurations and liquidity parameters
- **SystemMetrics Model:** Tracks system-wide performance indicators

---

## 🔄 Data Flow

1. **Trade Request:** User submits trade parameters through web interface.
2. **Quote Analysis:** System requests quotes from both Jupiter DEX and OTC pools.
3. **Route Decision:** Algorithm compares slippage, cost, and execution parameters.
4. **Trade Execution:** Selected route executes the trade with appropriate parameters.
5. **Logging:** Trade results and metrics are stored in database.
6. **Analytics:** Real-time dashboard updates with performance data.

---
