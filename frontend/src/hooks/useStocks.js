import { useState, useEffect } from "react";
import { stockService } from "../services/stockService";
import toast from "react-hot-toast";

export const useStock = (stockId) => {
    const [stocks, setStocks] = useState(null);       // list or searched/popular stocks
    const [stockData, setStockData] = useState(null); // unified object for details/history/quote
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchStockList = async () => {
        setLoading(true);
        try {
            const response = await stockService.getStocksList();
            setStocks(response.data);
            setError(null);
        } catch (err) {
            setError(err);
            toast.error("Failed to fetch stocks");
        } finally {
            setLoading(false);
        }
    };

    const fetchSearchedStock = async (query) => {
        setLoading(true);
        try {
            const response = await stockService.getSearchStock(query);
            setStocks(response.data);
            setError(null);
        } catch (err) {
            setError(err);
            toast.error("Failed to fetch searched stock");
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const fetchPopularStock = async () => {
        setLoading(true);
        try {
            const response = await stockService.getPopularStocks();
            setStocks(response.data);
            setError(null);
        } catch (err) {
            setError(err);
            toast.error("Failed to fetch popular stocks");
        } finally {
            setLoading(false);
        }
    };

    // Unified bundle fetcher
    const fetchStockBundle = async (id) => {
        setLoading(true);
        try {
            const [detailsRes, historyRes, quoteRes] = await Promise.all([
                stockService.getStockDetail(id),
                stockService.getStockHistory(id),
                stockService.getStockQuote(id),
            ]);

            setStockData({
                details: detailsRes.data,
                history: historyRes.data,
                quote: quoteRes.data,
            });
            setError(null);
        } catch (err) {
            setError(err);
            toast.error("Failed to fetch stock bundle");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (stockId) {
            fetchStockBundle(stockId);
        }
    }, [stockId]);

    return {
        stocks,
        stockData,
        loading,
        error,
        fetchStockList,
        fetchSearchedStock,
        fetchPopularStock,
        fetchStockBundle,
    };
};