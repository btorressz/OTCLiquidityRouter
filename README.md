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

## 📦 External Dependencies

### 🧰 Core Dependencies
- **Flask 3.1.1:** Web framework
- **SQLAlchemy 2.0.41:** Database ORM
- **Requests 2.32.4:** HTTP client for external API calls
- **Gunicorn 23.0.0:** Production WSGI server
- **psycopg2-binary 2.9.10:** PostgreSQL adapter

### 🖼️ Frontend Dependencies (CDN)
- **Bootstrap 5.3.2:** UI framework
- **Bootstrap Icons 1.11.1:** Icon library
- **Chart.js:** Data visualization

### 🌐 Jupiter DEX API
- **Endpoint:** `https://quote-api.jup.ag/v6`
- **Purpose:** Real-time DEX quotes and routing
- **Authentication:** None required (public API)

## 💹 Real-time Pricing System

### 🌐 CoinGecko Primary Source
- Main pricing API providing comprehensive token data with **24-hour price changes** for all supported tokens.

### 🔗 Multi-source Failover
- Fallback sequence: **CoinGecko (primary)** → **Kraken (secondary)** → **Binance (tertiary)** → Static fallback.

### 🐙 Kraken Integration
- Added as a **secondary source** for SOL/USD pricing when CoinGecko experiences rate limiting.

### ⚡ Jupiter Role
- **Jupiter** is used **exclusively** for **DEX trade quotes and execution routing**, not for general pricing data.

### 🗄️ Price Caching
- Implements a **5-minute cache duration** to optimize API calls and reduce rate limiting.

### 📈 Dashboard Transparency
- Real-time price display with **clear data source indicators**:
  - 🟢 Live CoinGecko
  - 🟡 Live Kraken
  - 🔴 Offline

### 🤖 Smart Rate Limit Handling
- Automatic API source switching when **rate limits or errors** occur.

---

## 🌐 API Endpoints

- **`/api/prices`** → Enhanced endpoint with multi-source pricing and transparent data source reporting.
- **OTC Engine** now uses **real-time pricing** instead of static fallback prices for improved accuracy.

---

## 🔍 Data Source Transparency

- **Source Indicators:** Dashboard clearly shows which pricing data source is active (*CoinGecko Live*, *Kraken Live*, etc.).
- **Rate Limit Handling:** Graceful fallback to secondary or tertiary sources if APIs hit rate limits.
- **Cache Management:** 5-minute cache duration with source tracking for optimal performance.

  ---

## 📜 LICENSE - MIT LICENSE 
  - This project is under the **MIT LICENSE**

    ---
    

## 📸 Screenshots

![OTCLiquidityRouter Screenshot](https://github.com/btorressz/OTCLiquidityRouter/blob/main/OTCLiquidityRouter1.jpg?raw=true)

![OTCLiquidityRouter Screenshot](https://github.com/btorressz/OTCLiquidityRouter/blob/main/OTCLiquidityRouter2.jpg?raw=true)

![OTCLiquidityRouter Screenshot](https://github.com/btorressz/OTCLiquidityRouter/blob/main/OTCLiquidityRouter3.jpg?raw=true)

![OTCLiquidityRouter Screenshot](https://github.com/btorressz/OTCLiquidityRouter/blob/main/OTCLiquidityRouter4.jpg?raw=true)




