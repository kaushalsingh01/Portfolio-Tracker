import { useState, useEffect } from "react";
import { portfolioService } from "../services/portfolioService";
import toast from 'react-hot-toast';

export const usePortfolio = (portfolioId) => {
    const [portfolio, setPortfolio] = useState(null);
    const [holdings, setHoldings] = useState([]);
    const [transactions, setTransaction] = useState([]);
    const [loading, setLoading] = useState(false);
    const [analysis, setAnalysis] = useState(null);

    const fetchPortfolio = async () => {
        try {
            setLoading(true);
            const response = await portfolioService.getPortfolio(portfolioId);
            setPortfolio(response.data);
        } catch (error) {
            toast.error('Failed to fetch portfolio');
        } finally {
            setLoading(false);
        }
    };

    const fetchHoldings = async () => {
        try {
            const response = await portfolioService.getHoldings(portfolioId);
            setHoldings(response.data);
        } catch (error) {
            toast.error('Failed to fetch holdings');
        }
    };

    const fetchAnalysis = async () => {
        try {
            const response = await portfolioService.getPortfolioAnalysis(portfolioId);
            setAnalysis(response.data);
        } catch (error) {
            toast.error('Failed to fetch analysis');
        }
    };

    const addTransaction = async (transactionData) => {
        try {
            await portfolioService.addTransaction(portfolioId, transactionData);
            toast.success('Transaction added successfully');
            await Promise.all([fetchPortfolio(), fetchHoldings()]);
        } catch (error) {
            toast.error('Failied to add transaction');
            throw error;
        }
    };

    useEffect(() => {
        if(portfolioId) {
            fetchPortfolio();
            fetchHoldings();
            fetchAnalysis();
        }
    }, [portfolioId]);

    return {
        portfolio,
        holdings,
        transactions,
        analysis,
        loading,
        fetchPortfolio,
        fetchHoldings,
        addTransaction,
        refetchAnalysis: fetchAnalysis
    };
};