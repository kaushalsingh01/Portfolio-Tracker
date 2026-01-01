import { useState, useEffect } from "react";
import { stockService } from "../services/stockService";
import toast from "react-hot-toast";

export const useStock = (stockId) => {
    const [stocks, setStocks] = useState(null);
    const [details, setDetails] = useState(null);
    const [history, setHistory] = useState(null);
    const [quote, setQuote] = useState(null);
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

    const fetchStockDetails = async (id) => {
        setLoading(true);
        try {
            const response = await stockService.getStockDetail(id);
            setDetails(response.data);
            setError(null);
        } catch (err) {
            setError(err);
            toast.error("Failed to fetch stock details");
        } finally {
            setLoading(false);
        }
    };

    const fetchStockHistory = async (id) => {
        setLoading(true);
        try {
            const response = await stockService.getStockHistory(id);
            setHistory(response.data);
            setError(null);
        } catch (err) {
            setError(err);
            toast.error("Failed to fetch stock history");
        } finally {
            setLoading(false);
        }
    };

    const fetchStockQuote = async (id) => {
        setLoading(true);
        try {
            const response = await stockService.getStockQuote(id);
            setQuote(response.data);
            setError(null);
        } catch (err) {
            setError(err);
            toast.error("Failed to fetch stock real time quote");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (stockId) {
            fetchStockDetails(stockId);
            fetchStockHistory(stockId);
            fetchStockQuote(stockId);
        }
    }, [stockId]);

    return {
        stocks,
        details,
        history,
        quote,
        loading,
        error,
        fetchStockList,
        fetchSearchedStock,
        fetchPopularStock,
        fetchStockDetails,
        fetchStockHistory,
        fetchStockQuote,
    };
};