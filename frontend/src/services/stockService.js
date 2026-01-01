import api from "./api";

const stockUrl = (id) => `/stocks/${id}/`;

export const stockService = {
    // List all Stocks (with optional params for pagination/filters)
    getStocksList: (params = {}) => api.get('/stocks/', { params }),

    // Search Stock (safe encoding)
    getSearchStock: (query) => api.get(`/stocks/?q=${encodeURIComponent(query)}`),

    // Stock Specific Data
    getStockDetail: (id) => api.get(stockUrl(id)),
    getStockHistory: (id) => api.get(`${stockUrl(id)}history/`),
    getStockQuote: (id) => api.get(`${stockUrl(id)}quote/`),

    // Popular Stocks
    getPopularStocks: () => api.get('/stocks/popular/')
};