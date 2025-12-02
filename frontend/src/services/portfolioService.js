import api from './api';

export const portfolioService = {
    // CRUD
    getPortfolios: () => api.get('/portfolios/'),
    getPortfolio: (id) => api.get(`/portfolios/${id}/`),
    createPortfolio: (data) => api.post('/portfolios/', data),
    updatePortfolio: (id, data) => api.put(`/portfolios/${id}/`, data),
    deletePortfolio: (id) => api.delete(`/portfolios/${id}/`),

    //Holdings
    getHoldings: (portfolioId) => api.get(`/portfolios/${portfolioId}/holdings/`),
    addHolding: (portfolioId, data) => api.post(`/portfolios/${portfolioId}/create_transaction/`, data),

    //Transactions
    getTransactions: (portfolioId) => api.get(`/portfolios/${portfolioId}/transactions/`),
    addTransaction: (portfolioId, data) => api.post(`/portfolios/${portfolioId}/create_transaction/`, data),

    //Analysis
    getPortfolioAnalysis: (portfolioId) => api.get(`/portfolio-analysis/${portfolioId}/overview/`),
    getPerformance: (portfolioId) => api.get(`/portfolio-analysis/${portfolioId}/performance/`),
    getRiskAssessment: (portfolioId) => api.get(`/portfolio-analysis/${portfolioId}/risk/`),

    //Compare portfolios
    comparePortfolios: () => api.get('/portfolio-analysis/compare_portfolios/')
};