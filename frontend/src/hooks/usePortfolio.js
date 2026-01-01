import { useState, useEffect } from "react";
import { portfolioService } from "../services/portfolioService";
import toast from "react-hot-toast";

export const usePortfolio = (portfolioId) => {
    const [portfolioData, setPortfolioData] = useState(null); // unified object
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // --- Bundle fetcher ---
    const fetchPortfolioBundle = async (id) => {
        setLoading(true);
        try {
            const [portfolioRes, holdingsRes, transactionsRes, analysisRes] = await Promise.all([
                portfolioService.getPortfolio(id),
                portfolioService.getHoldings(id),
                portfolioService.getTransactions(id),
                portfolioService.getPortfolioAnalysis(id),
            ]);

            setPortfolioData({
                portfolio: portfolioRes.data,
                holdings: holdingsRes.data,
                transactions: transactionsRes.data,
                analysis: analysisRes.data,
            });
            setError(null);
        } catch (err) {
            setError(err);
            toast.error("Failed to fetch portfolio bundle");
        } finally {
            setLoading(false);
        }
    };

    // --- Selective refetchers ---
    const refetchPortfolio = async () => {
        try {
            const res = await portfolioService.getPortfolio(portfolioId);
            setPortfolioData((prev) => ({ ...prev, portfolio: res.data }));
        } catch (err) {
            setError(err);
            toast.error("Failed to refetch portfolio");
        }
    };

    const refetchHoldings = async () => {
        try {
            const res = await portfolioService.getHoldings(portfolioId);
            setPortfolioData((prev) => ({ ...prev, holdings: res.data }));
        } catch (err) {
            setError(err);
            toast.error("Failed to refetch holdings");
        }
    };

    const refetchTransactions = async () => {
        try {
            const res = await portfolioService.getTransactions(portfolioId);
            setPortfolioData((prev) => ({ ...prev, transactions: res.data }));
        } catch (err) {
            setError(err);
            toast.error("Failed to refetch transactions");
        }
    };

    const refetchAnalysis = async () => {
        try {
            const res = await portfolioService.getPortfolioAnalysis(portfolioId);
            setPortfolioData((prev) => ({ ...prev, analysis: res.data }));
        } catch (err) {
            setError(err);
            toast.error("Failed to refetch analysis");
        }
    };

    // --- Add transaction ---
    const addTransaction = async (transactionData) => {
        setLoading(true);
        try {
            await portfolioService.addTransaction(portfolioId, transactionData);
            toast.success("Transaction added successfully");
            await Promise.all([refetchPortfolio(), refetchHoldings(), refetchTransactions()]);
        } catch (err) {
            setError(err);
            toast.error("Failed to add transaction");
            throw err;
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (portfolioId) {
            fetchPortfolioBundle(portfolioId);
        }
    }, [portfolioId]);

    return {
        portfolioData,
        loading,
        error,
        fetchPortfolioBundle,
        addTransaction,
        refetchPortfolio,
        refetchHoldings,
        refetchTransactions,
        refetchAnalysis,
    };
};