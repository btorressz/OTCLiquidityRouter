/**
 * Dashboard JavaScript functionality for OTC Routing Engine
 * Handles real-time updates, chart management, and user interactions
 */

class OTCDashboard {
    constructor() {
        this.charts = {};
        this.updateInterval = null;
        this.isVisible = true;
        
        this.init();
    }
    
    init() {
        this.setupVisibilityHandler();
        this.setupAutoRefresh();
        this.setupEventListeners();
        this.initializeCharts();
    }
    
    setupVisibilityHandler() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            this.isVisible = !document.hidden;
            if (this.isVisible) {
                this.refreshData();
            }
        });
    }
    
    setupAutoRefresh() {
        // Auto-refresh data every 30 seconds when page is visible
        this.updateInterval = setInterval(() => {
            if (this.isVisible && this.shouldAutoRefresh()) {
                this.refreshData();
            }
        }, 30000);
    }
    
    setupEventListeners() {
        // Add click handlers for interactive elements
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-refresh]')) {
                e.preventDefault();
                this.refreshData();
            }
            
            if (e.target.matches('[data-toggle-auto-refresh]')) {
                e.preventDefault();
                this.toggleAutoRefresh();
            }
        });
        
        // Handle form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('#tradeForm')) {
                this.handleTradeSubmit(e);
            }
        });
    }
    
    initializeCharts() {
        // Initialize any charts that need dynamic data
        if (typeof Chart !== 'undefined') {
            Chart.defaults.color = '#adb5bd';
            Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
            Chart.defaults.backgroundColor = 'rgba(255, 255, 255, 0.05)';
        }
    }
    
    shouldAutoRefresh() {
        // Don't auto-refresh if user is actively interacting with forms
        const activeElement = document.activeElement;
        return !activeElement.matches('input, textarea, select');
    }
    
    async refreshData() {
        try {
            this.showLoadingIndicator();
            
            // Fetch latest trade data
            const response = await fetch('/api/trades?limit=10');
            if (response.ok) {
                const trades = await response.json();
                this.updateTradeTable(trades);
            }
            
            this.hideLoadingIndicator();
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showError('Failed to refresh data');
        }
    }
    
    updateTradeTable(trades) {
        const tbody = document.querySelector('#tradesTable tbody');
        if (!tbody || !trades.length) return;
        
        tbody.innerHTML = '';
        
        trades.forEach(trade => {
            const row = this.createTradeRow(trade);
            tbody.appendChild(row);
        });
    }
    
    createTradeRow(trade) {
        const row = document.createElement('tr');
        row.className = 'fade-in';
        
        const formatTime = (timestamp) => {
            return new Date(timestamp).toLocaleString();
        };
        
        const formatAmount = (amount, decimals = 2) => {
            return parseFloat(amount).toFixed(decimals);
        };
        
        row.innerHTML = `
            <td>
                <small class="text-muted">${formatTime(trade.created_at)}</small>
            </td>
            <td>
                <span class="badge bg-${trade.route === 'OTC' ? 'success' : 'primary'}">
                    ${trade.route}
                </span>
            </td>
            <td>${trade.input_token}/${trade.output_token}</td>
            <td>${formatAmount(trade.input_amount)} ${trade.input_token}</td>
            <td>$${formatAmount(trade.price, 4)}</td>
            <td>
                <span class="${trade.slippage > 1.0 ? 'text-warning' : 'text-success'}">
                    ${formatAmount(trade.slippage, 3)}%
                </span>
            </td>
            <td>
                ${trade.cost_savings > 0 ? 
                    `<span class="text-success">+$${formatAmount(trade.cost_savings)}</span>` : 
                    '<span class="text-muted">$0.00</span>'
                }
            </td>
        `;
        
        return row;
    }
    
    showLoadingIndicator() {
        const indicator = document.querySelector('#loadingIndicator');
        if (indicator) {
            indicator.classList.remove('d-none');
        }
    }
    
    hideLoadingIndicator() {
        const indicator = document.querySelector('#loadingIndicator');
        if (indicator) {
            indicator.classList.add('d-none');
        }
    }
    
    showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="bi bi-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('main .container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
    
    showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="bi bi-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('main .container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss after 3 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 3000);
        }
    }
    
    toggleAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
            this.showSuccess('Auto-refresh disabled');
        } else {
            this.setupAutoRefresh();
            this.showSuccess('Auto-refresh enabled');
        }
    }
    
    handleTradeSubmit(event) {
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Executing...';
            
            // Re-enable button after form submission
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i>Execute Trade';
            }, 2000);
        }
    }
    
    // Utility methods for number formatting
    static formatCurrency(amount, decimals = 2) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(amount);
    }
    
    static formatNumber(number, decimals = 2) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    }
    
    static formatPercentage(value, decimals = 2) {
        return `${parseFloat(value).toFixed(decimals)}%`;
    }
    
    // Chart helper methods
    createChart(canvasId, config) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, config);
        
        this.charts[canvasId] = chart;
        return chart;
    }
    
    updateChart(canvasId, newData) {
        const chart = this.charts[canvasId];
        if (!chart) return;
        
        chart.data = newData;
        chart.update('none'); // No animation for real-time updates
    }
    
    destroyChart(canvasId) {
        const chart = this.charts[canvasId];
        if (chart) {
            chart.destroy();
            delete this.charts[canvasId];
        }
    }
    
    // Cleanup method
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Destroy all charts
        Object.keys(this.charts).forEach(chartId => {
            this.destroyChart(chartId);
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.otcDashboard = new OTCDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.otcDashboard) {
        window.otcDashboard.destroy();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OTCDashboard;
}
