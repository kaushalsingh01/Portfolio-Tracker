import api from "./api";

const analysisUrl = (id) => `/portfolio-analysis/${id}/`;

export const analysisService = {
    getPortfolioOverview: (id) => api.get(`${analysisUrl(id)}overview/`),
    getPerformanceAnalysis: (id, params = {}) => api.get(`${analysisUrl(id)}performance/`, { params }),
    getSectorAllocation: (id) => api.get(`${analysisUrl(id)}sectors/`),
    getRiskAnalysis: (id) => api.get(`${analysisUrl(id)}risk/`),
    getHoldingsAnalysis: (id) => api.get(`${analysisUrl(id)}holdings_analysis/`),

    // Unified fetcher
    getFullAnalysis: async (id) => {
        const [overview, performance, sectors, risk, holdings] = await Promise.all([
            api.get(`${analysisUrl(id)}overview/`),
            api.get(`${analysisUrl(id)}performance/`),
            api.get(`${analysisUrl(id)}sectors/`),
            api.get(`${analysisUrl(id)}risk/`),
            api.get(`${analysisUrl(id)}holdings_analysis/`),
        ]);

        return {
            overview: overview.data,
            performance: performance.data,
            sectors: sectors.data,
            risk: risk.data,
            holdings: holdings.data,
        };
    },
};