import { useState, useEffect } from "react";
import { analysisService } from "../services/analysisService";
import toast from "react-hot-toast";

export const useAnalysis = (portfolioId) => {
    const [analysisData, setAnalysisData] = useState(null); // unified object
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // --- Bundle fetcher ---
    const fetchAnalysisBundle = async (id) => {
        setLoading(true);
        try {
            const [overviewRes, performanceRes, sectorsRes, riskRes, holdingsRes] = await Promise.all([
                analysisService.getPortfolioOverview(id),
                analysisService.getPerformanceAnalysis(id),
                analysisService.getSectorAllocation(id),
                analysisService.getRiskAnalysis(id),
                analysisService.getHoldingsAnalysis(id),
            ]);

            setAnalysisData({
                overview: overviewRes.data,
                performance: performanceRes.data,
                sectors: sectorsRes.data,
                risk: riskRes.data,
                holdings: holdingsRes.data,
            });
            setError(null);
        } catch (err) {
            setError(err);
            toast.error("Failed to fetch portfolio analysis");
        } finally {
            setLoading(false);
        }
    };

    // --- Selective refetchers ---
    const refetchOverview = async () => {
        try {
            const res = await analysisService.getPortfolioOverview(portfolioId);
            setAnalysisData((prev) => ({ ...prev, overview: res.data }));
        } catch (err) {
            setError(err);
            toast.error("Failed to refetch overview");
        }
    };

    const refetchPerformance = async () => {
        try {
            const res = await analysisService.getPerformanceAnalysis(portfolioId);
            setAnalysisData((prev) => ({ ...prev, performance: res.data }));
        } catch (err) {
            setError(err);
            toast.error("Failed to refetch performance");
        }
    };

    const refetchSectors = async () => {
        try {
            const res = await analysisService.getSectorAllocation(portfolioId);
            setAnalysisData((prev) => ({ ...prev, sectors: res.data }));
        } catch (err) {
            setError(err);
            toast.error("Failed to refetch sectors");
        }
    };

    const refetchRisk = async () => {
        try {
            const res = await analysisService.getRiskAnalysis(portfolioId);
            setAnalysisData((prev) => ({ ...prev, risk: res.data }));
        } catch (err) {
            setError(err);
            toast.error("Failed to refetch risk analysis");
        }
    };

    const refetchHoldings = async () => {
        try {
            const res = await analysisService.getHoldingsAnalysis(portfolioId);
            setAnalysisData((prev) => ({ ...prev, holdings: res.data }));
        } catch (err) {
            setError(err);
            toast.error("Failed to refetch holdings analysis");
        }
    };

    // --- Auto-fetch when portfolioId changes ---
    useEffect(() => {
        if (portfolioId) {
            fetchAnalysisBundle(portfolioId);
        }
    }, [portfolioId]);

    return {
        analysisData,
        loading,
        error,
        fetchAnalysisBundle,
        refetchOverview,
        refetchPerformance,
        refetchSectors,
        refetchRisk,
        refetchHoldings,
    };
};