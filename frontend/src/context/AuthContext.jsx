import React, { createContext, useState, useContext, useEffect } from "react";
import { authService } from "../services/auth";
import toast from "react-hot-toast";

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const currentUser = authService.getCurrentUser();
        setUser(currentUser);
        setLoading(false);
    }, []);

    const login = async (email, password) => {
        try {
            const userData = await authService.login(email, password);
            setUser(userData);
            toast.success("Logged in successfully");
            return userData;
        } catch (err) {
            toast.error("Login failed");
            throw err;
        }
    };

    const logout = () => {
        authService.logout();
        setUser(null);
        toast.success("Logged out");
    };

    const updateUser = (userData) => {
        setUser(userData);
        localStorage.setItem("user", JSON.stringify(userData));
    };

    const value = {
        user,
        login,
        logout,
        updateUser,
        isAuthenticated: !!user,
        loading,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};