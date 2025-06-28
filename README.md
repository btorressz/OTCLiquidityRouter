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

